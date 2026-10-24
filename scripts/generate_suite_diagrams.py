"""Export staged native Ibis graphs grouped by their parent entities.

Queries use illustrative unbound history tables; no data or validation runs.
Requires the Python graphviz dependency and Graphviz's `dot` executable.
"""

import argparse
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from functools import cache
from pathlib import Path

import graphviz
import ibis
import ibis.expr.operations as ops
import ibis.expr.types as ir
from ibis.expr.visualize import to_graph

from ppsc_ops_data_quality.account_to_survey_results.lineage import (
    FLOW_ENTITY_LINEAGE,
    PROJECTION_LINEAGE,
)
from ppsc_ops_data_quality.account_to_survey_results.queries import (
    add_flow_context,
    expected_account_values,
    expected_survey_rollups,
    flow_account_comparison,
    join_account,
    rollup_account_comparison,
)
from ppsc_ops_data_quality.core.queries import history_tables, snapshot

SHARED_PARENT = "Shared / query mechanics"
PARENT_COLORS = {
    "Salesforce object: Account": "#DCEBFF",
    "Salesforce object: Contact": "#DDF4E4",
    "Salesforce object: Survey_Result__c": "#FFF0D6",
    **{f"Flow: {entry['source_flow']}": "#EADFFA" for entry in FLOW_ENTITY_LINEAGE.values()},
    SHARED_PARENT: "#EEEEEE",
}
SOURCE_PARENTS = {
    f"{name}_History": f"Salesforce object: {name}"
    for name in ("Account", "Contact", "Survey_Result__c")
}


def _metadata_parent(name: str) -> str | None:
    metadata = PROJECTION_LINEAGE.get(name, {})
    if target := metadata.get("target_field"):
        return "Salesforce object: " + target.split(".", 1)[0]
    if metadata.get("entity_type", "").startswith("Flow"):
        return "Flow: " + metadata["source_flow"]
    if metadata.get("entity_type") in ("SalesforceField", "BusinessCondition"):
        objects = {source.split(".", 1)[0] for source in metadata["source_entities"]}
        if len(objects) == 1:
            return "Salesforce object: " + objects.pop()
    return None


def _relation_values(node: ops.Relation) -> dict[str, ops.Value]:
    if isinstance(node, (ops.Project, ops.JoinChain)):
        return dict(node.values)
    if isinstance(node, ops.Aggregate):
        return {**node.groups, **node.metrics}
    if isinstance(node, ops.UnboundTable):
        return {}
    parent = getattr(node, "parent", None)
    if not isinstance(parent, ops.Relation):
        raise TypeError(f"Unsupported diagram relation: {type(node).__name__}")
    return dict(parent.fields)


def node_parents(
    expression: ir.Table, inputs: dict[str, dict[str, str]]
) -> tuple[dict[ops.Node, str], dict[str, str]]:
    """Resolve ownership separately from dependencies, retaining boundary field owners."""
    declared: defaultdict[ops.Node, set[str]] = defaultdict(set)
    for relation in expression.op().find(ops.Relation):
        for name, value in _relation_values(relation).items():
            if parent := _metadata_parent(name):
                # A direct source field keeps its object, even when read by a Flow.
                if not isinstance(value, ops.Field):
                    declared[value].add(parent)

    for root, parents in list(declared.items()):
        pending = list(root.__children__)
        visited = set()
        while pending:
            node = pending.pop()
            if node in visited or isinstance(node, (ops.Field, ops.Relation)):
                continue
            visited.add(node)
            declared[node].update(parents)
            pending.extend(node.__children__)

    @cache
    def owners(node: ops.Node) -> frozenset[str]:
        if isinstance(node, ops.Field):
            if isinstance(node.rel, ops.UnboundTable):
                if node.rel.name in inputs:
                    return frozenset({inputs[node.rel.name][node.name]})
                parent = SOURCE_PARENTS.get(node.rel.name, SHARED_PARENT)
                return frozenset({parent})
            if parent := _metadata_parent(node.name):
                return frozenset({parent})
            return owners(_relation_values(node.rel)[node.name])
        if declared.get(node):
            return frozenset(declared[node])
        if isinstance(node, ops.Relation):
            if isinstance(node, ops.UnboundTable):
                return frozenset(
                    parent for name in node.schema for parent in owners(node.fields[name])
                )
            values = _relation_values(node).values()
        else:
            values = (child for child in node.__children__ if not isinstance(child, ops.Relation))
        return frozenset(parent for value in values for parent in owners(value))

    def single_parent(node: ops.Node) -> str:
        parents = owners(node)
        return next(iter(parents)) if len(parents) == 1 else SHARED_PARENT

    nodes = {node: single_parent(node) for node in expression.op().find(ops.Node)}
    outputs = {name: single_parent(value) for name, value in expression.op().fields.items()}
    return nodes, outputs


def build_parent_graph(expression: ir.Table, parents: dict[ops.Node, str]) -> graphviz.Digraph:
    """Keep Ibis's nodes/edges and labels; add parent colors and Graphviz clusters."""

    def attributes(node: ops.Node) -> dict[str, str]:
        parent = parents[node]
        return {
            "fillcolor": PARENT_COLORS[parent],
            "style": "rounded,filled",
            "group": parent,
            "tooltip": "Parent entity: " + parent,
        }

    graph = to_graph(expression, node_attr_getter=attributes)
    for index, parent in enumerate(sorted(set(parents.values()))):
        with graph.subgraph(name=f"cluster_parent_{index}") as cluster:
            cluster.attr(label=parent, color=PARENT_COLORS[parent], style="rounded")
            for node, owner in parents.items():
                if owner == parent:
                    cluster.node(str(hash(node)))
    return graph


@dataclass(frozen=True)
class DiagramPart:
    name: str
    builder: str
    expression: ir.Table


def _add_part(parts: list[DiagramPart], name: str, builder: str, expression: ir.Table) -> ir.Table:
    parts.append(DiagramPart(name, builder, expression))
    return ibis.table(expression.schema(), name=name)


def _cut_input(expression: ir.Table, original: ir.Table, boundary: ir.Table) -> ir.Table:
    if original.op() not in expression.op().find(ops.Relation):
        raise ValueError("Diagram boundary must occur in the expression")
    return expression.op().replace({original.op(): boundary.op()}).to_expr()


def illustrative_parts() -> dict[str, list[DiagramPart]]:
    """Stop each native graph at schema-preserving, diagram-only table inputs."""
    sources = history_tables(
        account_database="example_account",
        contact_database="example_contact",
        survey_result_database="example_survey_result",
    )
    history = {
        name: ibis.table(table.schema(), name=f"{name}_History") for name, table in sources.items()
    }
    before_at = datetime(2026, 10, 21, 11, 59, 59)
    execution_at = datetime(2026, 10, 21, 12)
    after_at = datetime(2026, 10, 21, 12, 5)
    event_id = ibis.literal("ILLUSTRATIVE_EVENT")
    flow = []
    AccountBefore = _add_part(
        flow,
        "Account_Before",
        "snapshot",
        snapshot(history["Account"], as_of=before_at),
    )
    Contact = _add_part(
        flow,
        "Contact_At_Execution",
        "snapshot",
        snapshot(history["Contact"], as_of=execution_at),
    )
    Survey = _add_part(
        flow,
        "Survey_Results_At_Execution",
        "snapshot",
        snapshot(history["Survey_Result__c"], as_of=execution_at),
    )
    Trigger = _add_part(
        flow,
        "Trigger_Survey_Result",
        "flow_account_query",
        Survey.filter(Survey.Id == event_id),
    )
    Record = _add_part(
        flow, "Joined_Record", "join_account", join_account(Trigger, Contact, AccountBefore)
    )
    Context = add_flow_context(Record, Survey, flow_run_date=ibis.literal(date(2026, 10, 21)))
    Context = _add_part(flow, "Flow_Context", "add_flow_context", Context)
    _add_part(flow, "Expected_Account", "expected_account_values", expected_account_values(Context))
    AccountAfter = _add_part(
        flow, "Account_After", "snapshot", snapshot(history["Account"], as_of=after_at)
    )
    Observed = _add_part(
        flow,
        "Account_After_By_Survey_Event",
        "flow_account_query",
        AccountAfter.mutate(survey_result_id=event_id),
    )
    _add_part(
        flow,
        "Flow_Comparison",
        "flow_account_comparison",
        flow_account_comparison(Context, Observed),
    )

    rollups = []
    AccountSnapshot = _add_part(
        rollups, "Account_Snapshot", "snapshot", snapshot(history["Account"], as_of=after_at)
    )
    SurveySnapshot = _add_part(
        rollups,
        "Survey_Result_Snapshot",
        "snapshot",
        snapshot(history["Survey_Result__c"], as_of=after_at),
    )
    _add_part(
        rollups,
        "Expected_Rollups",
        "expected_survey_rollups",
        expected_survey_rollups(AccountSnapshot, SurveySnapshot),
    )
    _add_part(
        rollups,
        "Rollup_Comparison",
        "rollup_account_comparison",
        rollup_account_comparison(AccountSnapshot, SurveySnapshot, AccountSnapshot),
    )
    return {"flow": flow, "rollups": rollups}


def write_parts_document(parts: list[DiagramPart], name: str, output: Path) -> Path:
    """Export parent-grouped Ibis graphs with an index of their function boundaries."""
    output.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {name}",
        "",
        "Native Ibis table graphs, split at function and intermediate-table boundaries. "
        "Each named input has the exact schema of its preceding stage, but no upstream "
        "expression graph. These are diagram-only boundaries, not materialized runtime tables.",
        "",
        "Bindings and events are illustrative; no data was queried. "
        "Graphs retain Ibis's native nodes, edges and labels, with parent-entity colors and "
        "clusters; there are no GX overlays.",
        "",
        "Fields are grouped by their Salesforce object, including expected and observed fields. "
        "Flow elements are grouped by their owning Flow from the authoritative lineage. "
        "Field ownership is preserved across diagram boundaries. Shared expressions, "
        "mixed-object relations and unmapped query mechanics are neutral gray.",
        "",
        "| Parent entity | Fill color |",
        "| --- | --- |",
        *[f"| {parent} | `{color}` |" for parent, color in PARENT_COLORS.items()],
        "",
        "| Output / diagram | Builder | Inputs |",
        "| --- | --- | --- |",
    ]
    for part in parts:
        inputs = sorted(op.name for op in part.expression.op().find(ops.UnboundTable))
        stem = f"{name}_{part.name}"
        lines.append(
            f"| [{part.name}]({stem}.svg) | `{part.builder}()` | "
            + ", ".join(f"`{input_name}`" for input_name in inputs)
            + " |"
        )
    inputs = {}
    for part in parts:
        stem = f"{name}_{part.name}"
        parents, outputs = node_parents(part.expression, inputs)
        graph = build_parent_graph(part.expression, parents)
        inputs[part.name] = outputs
        (output / f"{stem}.svg").write_bytes(graph.pipe(format="svg"))
        (output / f"{stem}.dot").write_text(graph.source, encoding="utf-8")
        lines.extend(
            [
                "",
                f"## {part.name}",
                "",
                f"Builder: `{part.builder}()`",
                "",
                f"![Native Ibis table graph: {part.name}]({stem}.svg)",
                "",
                f"[SVG]({stem}.svg) | [DOT]({stem}.dot)",
            ]
        )
    document = output / f"{name}.md"
    document.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/suites"))
    parser.add_argument("--suite", choices=("all", "flow", "rollups"), default="all")
    args = parser.parse_args(argv)
    if shutil.which("dot") is None:
        parser.error("Install Graphviz's 'dot' executable (for example: apt-get install graphviz)")
    for name, parts in illustrative_parts().items():
        if args.suite in ("all", name):
            print(write_parts_document(parts, f"account_to_survey_results_{name}", args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
