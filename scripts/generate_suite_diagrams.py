"""Render native Flow graph lineage and the explicit Ops temporal roles."""

import argparse
from pathlib import Path

import graphviz
from salesforce.entities.flows import to_sqlglot

from ppsc_ops_data_quality.account_to_survey_results.queries import metadata_inputs


def generate(output: Path) -> Path:
    inputs = metadata_inputs()
    query = to_sqlglot(
        inputs["flow"],
        object_name="Account",
        target_reference="$Record.Participant__r.AccountId",
        simplify=True,
    )
    evidence = query.meta["ppsc"]
    graph = graphviz.Digraph("Flow", format="svg")
    graph.attr(rankdir="LR")
    for node in evidence["source_graph"]["declarations"]:
        graph.node(node["local_id"], label=node["kind"] + ": " + node["name"])
    # Original source graph is preserved independently of SQL CTE folding.
    for connection in evidence["source_graph"]["connections"]:
        source = connection.get("source") or connection.get("source_id")
        target = connection.get("target") or connection.get("target_id")
        if source is not None and target is not None:
            graph.edge(str(source), str(target))
    for role in [
        "Account BEFORE",
        "Contact at execution",
        "Survey lookups at execution",
        "Account AFTER",
    ]:
        graph.node(role, shape="box", style="filled", fillcolor="#DCEBFF")
    graph.edge("Account BEFORE", "Expected state")
    graph.edge("Survey lookups at execution", "Expected state")
    graph.edge("Contact at execution", "Expected state")
    graph.edge("Expected state", "GX comparison")
    graph.edge("Account AFTER", "GX comparison")
    output.mkdir(parents=True, exist_ok=True)
    path = Path(graph.render(filename="account-flow", directory=str(output), cleanup=True))
    (output / "account-flow.lineage.json").write_text(
        __import__("json").dumps(evidence["source_graph"], indent=2) + "\n"
    )
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/diagrams"))
    print(generate(parser.parse_args().output))


if __name__ == "__main__":
    main()
