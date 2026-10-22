"""Document GX suites with field diagrams and an optional native Ibis graph.

Expectation diagrams use the comparison schema and actual GX configurations.
Fields are grouped within their exact row condition. Ibis's native exporter is
used unchanged for optional expression diagnostics. No query or validation runs.
Requires the Python graphviz dependency and Graphviz's `dot` executable.
"""

import argparse
import json
import re
import shutil
from datetime import date, datetime
from html import escape
from pathlib import Path

import graphviz
import great_expectations as gx
import ibis
import ibis.expr.types as ir
from ibis.expr.visualize import to_graph

from ppsc_ops_data_quality.account_to_survey_results.gx import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.account_to_survey_results.queries import (
    flow_account_query,
    rollup_account_query,
)
from ppsc_ops_data_quality.account_to_survey_results.schemas import (
    FLOW_ACCOUNT_COMPARISON,
    ROLLUP_ACCOUNT_COMPARISON,
)
from ppsc_ops_data_quality.core.queries import history_tables

NODE_STYLES = {
    "column": {"fillcolor": "honeydew"},
    "expectation": {"fillcolor": "aliceblue"},
    "table": {"fillcolor": "whitesmoke"},
}


def expectation_columns(kwargs: dict) -> list[tuple[str, str]]:
    """Read GX column arguments, preserving each column's argument role."""
    columns = [(key, kwargs[key]) for key in ("column", "column_A", "column_B") if key in kwargs]
    for key in ("column_list", "column_set"):
        columns.extend((key, column) for column in kwargs.get(key, ()))
    return columns


def condition_columns(condition) -> list[str]:
    """Read input columns from a native GX condition, including AND/OR children."""
    if condition is None:
        return []
    if isinstance(condition, str):
        raise TypeError("Suite diagrams require native GX Column row conditions")
    column = getattr(condition, "column", None)
    columns = [column.name] if column is not None else []
    children = getattr(condition, "conditions", ())
    if column is None and not children:
        raise TypeError(f"Unsupported GX row condition: {type(condition).__name__}")
    for child in children:
        columns.extend(condition_columns(child))
    return list(dict.fromkeys(columns))


def row_condition_text(expectation) -> str:
    """Display the actual GX predicate without translating its meaning."""
    condition = getattr(expectation, "row_condition", None)
    return repr(condition) if condition is not None else "All rows"


def expectation_group_name(expectation) -> str:
    """Group paired output fields, identities and table checks for presentation.

    Matching expected__/observed__ suffixes identify a displayed field group;
    this naming convention is not used to infer upstream data lineage.
    """
    config = expectation.configuration
    kwargs = config.kwargs
    if config.type.startswith("expect_table_"):
        return "Schema and table checks"
    if "column_A" in kwargs and "column_B" in kwargs:
        observed = kwargs["column_A"].removeprefix("observed__")
        expected = kwargs["column_B"].removeprefix("expected__")
        if observed == expected:
            return f"Field: {expected}"
        return f"Columns: {kwargs['column_A']} / {kwargs['column_B']}"
    column = kwargs.get("column", "Multiple columns")
    return "Identity checks" if column.endswith("_id") else f"Column: {column}"


def group_expectations(suite: gx.ExpectationSuite) -> dict:
    """Group by exact serialized row condition and then by displayed field name."""
    groups = {}
    for index, expectation in enumerate(suite.expectations):
        condition = expectation.configuration.kwargs.get("row_condition")
        key = (json.dumps(condition, sort_keys=True), expectation_group_name(expectation))
        groups.setdefault(key, []).append((index, expectation))
    return groups


def create_diagram(title: str) -> graphviz.Digraph:
    """Use Graphviz's hierarchical layout with one shared set of display defaults."""
    return graphviz.Digraph(
        graph_attr={
            "label": title,
            "labelloc": "t",
            "rankdir": "LR",
            "fontname": "Helvetica",
            "nodesep": "0.3",
            "ranksep": "0.6",
        },
        node_attr={
            "shape": "box",
            "style": "rounded,filled",
            "fontname": "Helvetica",
            "fontsize": "11",
        },
        edge_attr={"fontname": "Helvetica", "fontsize": "9"},
    )


def build_suite_overview(suite: gx.ExpectationSuite, groups: dict) -> graphviz.Digraph:
    """Show field groups within shared row-condition clusters, once per scope."""
    graph = create_diagram(suite.name)
    graph.node("suite", label=suite.name, **NODE_STYLES["table"])
    scopes = list(dict.fromkeys(condition for condition, _ in groups))
    for scope_index, condition in enumerate(scopes):
        with graph.subgraph(name=f"cluster_scope_{scope_index}") as cluster:
            checks = next(checks for (key, _), checks in groups.items() if key == condition)
            label = row_condition_text(checks[0][1]).replace(" AND ", "\nAND ")
            cluster.attr(label=graphviz.escape(f"Scope {scope_index + 1}: {label}"), color="gray70")
            for index, ((key, name), checks) in enumerate(groups.items()):
                if key == condition:
                    cluster.node(
                        f"group_{index}",
                        label=graphviz.escape(f"{name}\nExpectations: {len(checks)}"),
                        **NODE_STYLES["expectation"],
                    )
                    graph.edge("suite", f"group_{index}")
    return graph


def build_field_diagram(schema: ibis.Schema, name: str, checks: list) -> graphviz.Digraph:
    """Connect actual GX targets to checks inside a single row-condition scope.

    The scope label applies to every check in the cluster. No condition-to-check
    fanout edges or Ibis operation IDs are needed. Table checks bind to a table
    node; their complete column requirements remain in the Markdown configuration.
    """
    conditions = {
        json.dumps(e.configuration.kwargs.get("row_condition"), sort_keys=True) for _, e in checks
    }
    if len(conditions) != 1:
        raise ValueError("A field diagram must have exactly one row-condition scope")
    graph = create_diagram(name)
    column_ids = {}
    with graph.subgraph(name="cluster_scope") as cluster:
        cluster.attr(
            label=graphviz.escape("Row condition: " + row_condition_text(checks[0][1])),
            color="gray70",
        )
        for index, expectation in checks:
            config = expectation.configuration
            targets = expectation_columns(config.kwargs)
            referenced_columns = [column for _, column in targets]
            referenced_columns += condition_columns(getattr(expectation, "row_condition", None))
            for column in referenced_columns:
                if column not in schema:
                    raise ValueError(
                        f"{config.type} references missing comparison column: {column}"
                    )
            expectation_id = f"expectation_{index}"
            cluster.node(
                expectation_id,
                label=f"{index + 1}. {type(expectation).__name__}",
                tooltip=config.meta.get("check_id", config.type),
                **NODE_STYLES["expectation"],
            )
            if config.type.startswith("expect_table_") or not targets:
                cluster.node("comparison", label="Comparison table", **NODE_STYLES["table"])
                cluster.edge("comparison", expectation_id, label="table")
                continue
            for role, column in targets:
                if column not in column_ids:
                    column_ids[column] = f"column_{len(column_ids)}"
                    cluster.node(
                        column_ids[column],
                        label=graphviz.escape(f"{column}\n{schema[column]}"),
                        **NODE_STYLES["column"],
                    )
                cluster.edge(column_ids[column], expectation_id, label=role)
    return graph


def write_diagram(graph: graphviz.Digraph, stem: Path) -> None:
    """Write SVG and editable DOT using the standard Graphviz renderer."""
    Path(f"{stem}.svg").write_bytes(graph.pipe(format="svg"))
    Path(f"{stem}.dot").write_text(graph.source, encoding="utf-8")


def markdown_cell(value) -> str:
    return escape(str(value)).replace("|", "&#124;").replace("\n", " ")


def write_suite_document(
    schema: ibis.Schema,
    suite: gx.ExpectationSuite,
    output: Path,
    *,
    expression: ir.Table | None = None,
) -> Path:
    """Write a suite overview and expandable field sections from authored metadata."""
    output.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", suite.name).strip("._") or "suite"
    groups = group_expectations(suite)
    scopes = list(dict.fromkeys(condition for condition, _ in groups))
    write_diagram(build_suite_overview(suite, groups), output / slug)
    lines = [
        f"# {suite.name}",
        "",
        "Generated by `scripts/generate_suite_diagrams.py` from the comparison schema "
        "and native GX suite builders. Bindings/events are illustrative; no data was queried.",
        "",
        f"{len(suite.expectations)} expectations; {len(schema)} comparison columns.",
        "",
        "The overview groups fields by their exact GX row condition. Expand a field to see "
        "its columns, checks and configuration. Scope labels apply to every contained check; "
        "they do not filter the Ibis input. Green nodes are columns; blue nodes are expectations.",
        "",
        f"![Suite overview grouped by row condition]({slug}.svg)",
        "",
        f"[Overview SVG]({slug}.svg) · [Overview DOT]({slug}.dot)",
        "",
    ]
    for group_index, ((condition, name), checks) in enumerate(groups.items()):
        stem = f"{slug}_{group_index:02d}"
        write_diagram(build_field_diagram(schema, name, checks), output / stem)
        lines.extend(
            [
                "<details>",
                f"<summary>{escape(name)} (scope {scopes.index(condition) + 1}; "
                f"expectations: {len(checks)})</summary>",
                "",
                f"Row condition: `{row_condition_text(checks[0][1])}`",
                "",
                f"![Columns and expectations for {escape(name)}]({stem}.svg)",
                "",
                f"[Field SVG]({stem}.svg) · [Field DOT]({stem}.dot)",
                "",
                "| # | Check ID | Expectation | Target columns | Row condition |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for index, expectation in checks:
            config = expectation.configuration
            targets = expectation_columns(config.kwargs)
            columns = "; ".join(f"{role}: {column}" for role, column in targets) or "Table"
            if "column_set" in config.kwargs:
                columns = (
                    f"Schema: {len(config.kwargs['column_set'])} required columns (listed below)"
                )
            values = (
                index + 1,
                config.meta.get("check_id", config.type),
                type(expectation).__name__,
                columns,
                row_condition_text(expectation),
            )
            lines.append("| " + " | ".join(map(markdown_cell, values)) + " |")
        for _, expectation in checks:
            if expectation.configuration.type.startswith("expect_table_"):
                lines.extend(
                    [
                        "",
                        "```json",
                        json.dumps(expectation.configuration.kwargs, indent=2, ensure_ascii=False),
                        "```",
                    ]
                )
        lines.extend(["", "</details>", ""])
    if expression is not None:
        write_diagram(to_graph(expression), output / f"{slug}_ibis")
        lines.extend(
            [
                "<details>",
                "<summary>Native Ibis expression graph (diagnostic)</summary>",
                "",
                "Unmodified Ibis output; expectation bindings are documented in the field sections.",
                "",
                f"[Native Ibis SVG]({slug}_ibis.svg) · [Native Ibis DOT]({slug}_ibis.dot)",
                "",
                f"![Native Ibis expression graph]({slug}_ibis.svg)",
                "",
                "</details>",
                "",
            ]
        )
    lines.extend(
        [
            "## Suite metadata",
            "",
            "```json",
            json.dumps(suite.meta, indent=2),
            "```",
            "",
            "Python suite builders remain authoritative. These are authored expectations, "
            "not validation outcomes. Optional row-count checks appear only when supplied.",
            "",
        ]
    )
    document = output / f"{slug}.md"
    document.write_text("\n".join(lines), encoding="utf-8")
    return document


def illustrative_comparisons() -> dict[str, ir.Table]:
    """Explicit nonexecuted bindings for optional native expression diagnostics."""
    history = history_tables(
        account_database="example_account",
        contact_database="example_contact",
        survey_result_database="example_survey_result",
    )
    return {
        "flow": flow_account_query(
            history,
            survey_result_id="ILLUSTRATIVE_EVENT",
            account_before_at=datetime(2026, 10, 21, 11, 59, 59),
            execution_at=datetime(2026, 10, 21, 12),
            account_after_at=datetime(2026, 10, 21, 12, 5),
            flow_run_date=date(2026, 10, 21),
        ),
        "rollups": rollup_account_query(history, as_of=datetime(2026, 10, 21, 12, 5)),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/suites"))
    parser.add_argument("--suite", choices=("all", "flow", "rollups"), default="all")
    parser.add_argument(
        "--include-expression-graph",
        action="store_true",
        help="Also render the unmodified native Ibis graph as a diagnostic",
    )
    args = parser.parse_args(argv)
    if shutil.which("dot") is None:
        parser.error("Install Graphviz's 'dot' executable (for example: apt-get install graphviz)")
    schemas = {"flow": FLOW_ACCOUNT_COMPARISON, "rollups": ROLLUP_ACCOUNT_COMPARISON}
    queries = illustrative_comparisons() if args.include_expression_graph else {}
    suites = {"flow": flow_account_suite(), "rollups": rollup_account_suite()}
    for name, suite in suites.items():
        if args.suite in ("all", name):
            print(
                write_suite_document(
                    schemas[name],
                    suite,
                    args.output,
                    expression=queries.get(name),
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
