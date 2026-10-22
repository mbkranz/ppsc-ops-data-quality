"""Generate a Markdown document and annotated native Ibis graph for each GX suite.

Provenance: Ibis 12's ibis.expr.visualize.to_graph() and native GX suite builders.
Query bindings are illustrative, from demo.comparisons(); no data is fetched and
no GX validation is executed. Extensions connect final Ibis output projections
to their GX expectations and native Column row conditions. Source lineage stays
in the actual Ibis graph; these edges describe validation bindings, not Flow logic.

Requires the Python graphviz development dependency and Graphviz's `dot` executable.
Run `uv run poe suite-diagrams` from the repository root. Generated documentation
is intentionally replaced on regeneration; validation-run evidence is unaffected.
"""

import argparse
import json
import re
import shutil
import textwrap
from pathlib import Path

import great_expectations as gx
import ibis
import ibis.expr.operations as ops
import ibis.expr.types as ir
from graphviz import escape
from ibis.expr.visualize import to_graph

from ppsc_ops_data_quality.account_to_survey_results_expectations import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.demo import comparisons
from ppsc_ops_data_quality.schemas import history_tables


def condition_columns(condition) -> list[str]:
    """Read column references from GX's native condition tree, including AND/OR.

    No string parsing or predicate reimplementation is performed. The current
    suites use native Column conditions; reject legacy condition strings rather
    than imply that their source columns were resolved.
    """
    if condition is None:
        return []
    if isinstance(condition, str):
        raise TypeError("Suite diagrams require native GX Column row conditions")
    column = getattr(condition, "column", None)
    columns = [column.name] if column is not None else []
    for child in getattr(condition, "conditions", ()):
        columns.extend(condition_columns(child))
    return list(dict.fromkeys(columns))


def expectation_columns(kwargs: dict) -> list[tuple[str, str]]:
    """Return explicit GX target columns with their argument roles.

    Column pairs retain both A and B; multicolumn and schema checks retain every
    listed column. Table-level checks without column arguments bind to the final
    comparison relation instead.
    """
    columns = [(key, kwargs[key]) for key in ("column", "column_A", "column_B") if key in kwargs]
    for key in ("column_list", "column_set"):
        columns.extend((key, column) for column in kwargs.get(key, ()))
    return columns


def _label(text: str) -> str:
    return escape("\n".join(textwrap.fill(line, width=48) for line in text.splitlines()))


def _ibis_node_attributes(node):
    # Hide repeated relation schemas; the final projected column nodes below show
    # names/types explicitly. Keep native dependency edges and all operations.
    if isinstance(node, ops.Literal):
        value = node.value.isoformat() if hasattr(node.value, "isoformat") else repr(node.value)
        return {"label": _label(f"Literal\n{value}\n:: {node.dtype}")}
    if isinstance(node, ops.PhysicalTable):
        namespace = node.namespace
        name = ".".join(filter(None, (namespace.catalog, namespace.database, node.name)))
        return {"label": _label(f"{type(node).__name__}\n{name}"), "fillcolor": "#edf2f7"}
    if isinstance(node, ops.Relation):
        return {"label": type(node).__name__}
    return {}


def annotated_graph(
    comparison: ir.Table, suite: gx.ExpectationSuite, *, include_lineage: bool = True
):
    """Extend Ibis's own graph with GX targets and separate scope dependencies.

    Ibis 12 names graph nodes str(hash(operation)). This version-specific bridge
    is isolated here and tested against native output. Explicit output aliases
    remain separate nodes even when two fields share the same underlying value.
    include_lineage=False uses Ibis's unbound comparison schema for the compact
    binding view. It does not claim to show the upstream transformations. This
    function returns Graphviz objects without rendering or executing a query.
    """
    expression = comparison if include_lineage else ibis.table(comparison.schema(), name=suite.name)
    graph = to_graph(
        expression,
        node_attr={"fontsize": "10", "style": "filled", "fillcolor": "white"},
        node_attr_getter=_ibis_node_attributes,
        edge_attr={"color": "#a0aec0", "arrowsize": "0.6"},
    )
    title = (
        "Ibis dependencies + GX expectations"
        if include_lineage
        else "Comparison columns + GX expectations"
    )
    graph.attr(
        label=f"{suite.name}\n{title}",
        labelloc="t",
        fontsize="16",
        rankdir="BT" if include_lineage else "LR",
    )
    output_ids = {column: f"output_{index}" for index, column in enumerate(comparison.columns)}
    relation_id = str(hash(expression.op()))
    for column, node_id in output_ids.items():
        graph.node(
            node_id,
            label=_label(f"{column}\n:: {comparison.schema()[column]}"),
            shape="ellipse",
            fillcolor="#e6fffa",
            color="#2c7a7b",
        )
        # These comparison queries end in a JoinChain whose values map is the
        # actual final projection. Do not infer lineage from column-name matches.
        value_id = str(hash(comparison.op().values[column])) if include_lineage else relation_id
        graph.edge(value_id, node_id, label="projects", color="#2c7a7b", fontsize="8")

    conditions = {}
    for index, expectation in enumerate(suite.expectations):
        config = expectation.configuration.to_json_dict()
        kwargs = config["kwargs"]
        check_id = config.get("meta", {}).get("check_id", f"expectation_{index:03d}")
        node_id = f"expectation_{index}"
        graph.node(
            node_id,
            label=_label(f"{check_id}\n{type(expectation).__name__}"),
            shape="box",
            fillcolor="#ebf8ff",
            color="#2b6cb0",
            style="rounded,filled",
        )
        targets = expectation_columns(kwargs)
        # The compact view binds schema assertions to the comparison table; the
        # detailed native graph retains their individual required-column edges.
        if not include_lineage and config["type"].startswith("expect_table_"):
            targets = []
        for role, column in targets:
            if column not in output_ids:
                raise ValueError(f"{check_id} references missing Ibis output column: {column}")
            graph.edge(output_ids[column], node_id, label=role, color="#2b6cb0", fontsize="8")
        if not targets:
            graph.edge(relation_id, node_id, label="table", color="#2b6cb0", fontsize="8")
        condition = getattr(expectation, "row_condition", None)
        if condition is None:
            continue
        key = json.dumps(kwargs["row_condition"], sort_keys=True)
        if key not in conditions:
            condition_id = f"condition_{len(conditions)}"
            conditions[key] = condition_id
            graph.node(
                condition_id,
                label=_label(f"GX row_condition\n{condition!r}"),
                shape="diamond",
                fillcolor="#fffaf0",
                color="#c05621",
            )
            for column in condition_columns(condition):
                if column not in output_ids:
                    raise ValueError(
                        f"{check_id} row condition references missing column: {column}"
                    )
                graph.edge(output_ids[column], condition_id, color="#c05621", style="dashed")
        graph.edge(
            conditions[key],
            node_id,
            label="applies when True",
            color="#c05621",
            style="dashed",
            fontsize="8",
        )
    return graph


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_suite_document(comparison: ir.Table, suite: gx.ExpectationSuite, output: Path) -> Path:
    """Write compact and full native SVG/DOT plus one suite Markdown document."""
    output.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", suite.name).strip("._") or "suite"
    for suffix, include_lineage in (("", False), ("_ibis", True)):
        graph = annotated_graph(comparison, suite, include_lineage=include_lineage)
        (output / f"{slug}{suffix}.svg").write_bytes(graph.pipe(format="svg"))
        (output / f"{slug}{suffix}.dot").write_text(graph.source, encoding="utf-8")
    lines = [
        f"# {suite.name}",
        "",
        "Generated by `scripts/generate_suite_diagrams.py` from the authored Ibis comparison "
        "and native GX suite builder. Bindings/events are illustrative; no data was queried.",
        "",
        f"{len(suite.expectations)} expectations; {len(comparison.columns)} comparison columns.",
        "",
        "The compact view reads left to right: the Ibis comparison schema feeds green output columns; "
        "blue edges attach GX expectations to their target columns. Dashed orange edges "
        "show the independent row condition and its input columns. Table/schema checks "
        "attach to the comparison relation. These are validation bindings, "
        "not additional Ibis filters.",
        "",
        f"![Ibis comparison columns with GX expectations and row conditions]({slug}.svg)",
        "",
        f"[Open binding SVG for zooming]({slug}.svg) · [Binding DOT source]({slug}.dot)",
        "",
        f"[Full native Ibis graph with expectations]({slug}_ibis.svg) · "
        f"[Full native DOT source]({slug}_ibis.dot)",
        "",
        "The full graph includes every Ibis operation, source table, join, formula and "
        "literal (including the launch cutoff). It reads bottom to top and retains "
        "individual column edges for schema assertions. Open its SVG to zoom into lineage.",
        "",
        "## Expectations",
        "",
        "| # | Check ID | Expectation | Target columns | Row condition |",
        "| --- | --- | --- | --- | --- |",
    ]
    schema_details = []
    for index, expectation in enumerate(suite.expectations):
        config = expectation.configuration.to_json_dict()
        targets = expectation_columns(config["kwargs"])
        columns = "; ".join(f"{role}: {column}" for role, column in targets) or "Table"
        if "column_set" in config["kwargs"]:
            columns = (
                f"Schema: {len(config['kwargs']['column_set'])} required columns (listed below)"
            )
            schema_details.extend(
                [
                    f"### {config.get('meta', {}).get('check_id', config['type'])}",
                    "",
                    "```json",
                    json.dumps(config["kwargs"], indent=2, ensure_ascii=False),
                    "```",
                    "",
                ]
            )
        condition = getattr(expectation, "row_condition", None)
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    index + 1,
                    config.get("meta", {}).get("check_id", f"expectation_{index:03d}"),
                    type(expectation).__name__,
                    columns,
                    repr(condition) if condition is not None else "All rows (no row condition)",
                )
            )
            + " |"
        )
    if schema_details:
        lines.extend(["", "## Schema expectations", "", *schema_details])
    lines.extend(
        [
            "",
            "## Query and suite scope",
            "",
            "```json",
            json.dumps(suite.meta, indent=2, ensure_ascii=False),
            "```",
            "",
            "Python suite builders remain authoritative. This document describes authored "
            "expectations, not validation outcomes. Optional independent row-count checks "
            "appear only when included in the supplied suite.",
            "",
        ]
    )
    document = output / f"{slug}.md"
    document.write_text("\n".join(lines), encoding="utf-8")
    return document


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/suites"))
    parser.add_argument("--suite", choices=("all", "flow", "rollups"), default="all")
    args = parser.parse_args(argv)
    if shutil.which("dot") is None:
        parser.error("Install Graphviz's 'dot' executable (for example: apt-get install graphviz)")
    queries = comparisons(
        history_tables(
            account_database="example_account",
            contact_database="example_contact",
            survey_result_database="example_survey_result",
        )
    )
    suites = {"flow": flow_account_suite(), "rollups": rollup_account_suite()}
    for name, suite in suites.items():
        if args.suite in ("all", name):
            print(write_suite_document(queries[name], suite, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
