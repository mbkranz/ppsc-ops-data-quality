"""Suite documents preserve GX targets/scopes without Ibis-internal bindings."""

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import great_expectations as gx
import great_expectations.expectations as gxe
import ibis
import pytest
from great_expectations.expectations.row_conditions import Column

from ppsc_ops_data_quality.account_to_survey_results.gx import flow_account_suite
from ppsc_ops_data_quality.core.queries import history_tables
from scripts.check_validation import comparisons

spec = importlib.util.spec_from_file_location(
    "generate_suite_diagrams", Path("scripts/generate_suite_diagrams.py")
)
diagrams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagrams)


def query_expressions():
    return comparisons(
        history_tables(
            account_database="example_account",
            contact_database="example_contact",
            survey_result_database="example_survey_result",
        )
    )


def test_field_graph_connects_both_columns_and_preserves_combined_scope():
    query = query_expressions()["flow"]
    suite = flow_account_suite(expected_row_count=1)
    groups = diagrams.group_expectations(suite)
    assert len({condition for condition, _ in groups}) == 3  # All rows, launch, CABOR.
    for (_, name), checks in groups.items():
        graph = diagrams.build_field_diagram(query.schema(), name, checks)
        source = graph.source
        assert "Row condition: " + diagrams.row_condition_text(checks[0][1]) in source
        for index, _ in checks:
            assert f"expectation_{index}" in source
        if name == "Field: CABOR_Completion_Date__c":
            assert len(checks) == 1
            index, expectation = checks[0]
            assert diagrams.condition_columns(expectation.row_condition) == [
                "survey_completion_occurred_on_or_after_launch",
                "cabor_lookup_is_deterministic",
            ]
            assert "AND cabor_lookup_is_deterministic == True" in source
            assert f"column_0 -> expectation_{index} [label=column_A]" in source
            assert f"column_1 -> expectation_{index} [label=column_B]" in source
        if name == "Schema and table checks":
            assert "label=table" in source


def test_documents_have_one_expandable_section_per_group_and_all_expectations(tmp_path):
    assert diagrams.main(["--output", str(tmp_path)]) == 0
    for name, count in (("flow", 27), ("rollups", 24)):
        slug = f"account_to_survey_results_{name}"
        markdown = (tmp_path / f"{slug}.md").read_text()
        assert f"{count} expectations;" in markdown
        assert "Row condition" in markdown
        assert f"]({slug}.svg)" in markdown
        assert not (tmp_path / f"{slug}_ibis.svg").exists()
        groups = list(tmp_path.glob(f"{slug}_[0-9][0-9].svg"))
        assert markdown.count("<details>") == markdown.count("</details>") == len(groups)
        expectation_nodes = []
        for path in groups:
            root = ET.parse(path).getroot()
            titles = [node.text for node in root.iter("{http://www.w3.org/2000/svg}title")]
            expectation_nodes.extend(
                t for t in titles if t.startswith("expectation_") and "->" not in t
            )
        assert len(expectation_nodes) == count
        assert set(expectation_nodes) == {f"expectation_{i}" for i in range(count)}
        if name == "flow":
            assert "survey_completion_occurred_on_or_after_launch" in markdown
            assert "cabor_lookup_is_deterministic" in markdown
        else:
            assert "All rows" in markdown


def test_expression_diagnostic_uses_native_ibis_export_without_gx_overlay(tmp_path):
    table = ibis.table({"a": "int64"}, name="source")
    query = table.mutate(a=table.a + 1)
    suite = gx.ExpectationSuite(
        name="diagnostic", expectations=[gxe.ExpectColumnValuesToNotBeNull(column="a")]
    )
    diagrams.write_suite_document(query.schema(), suite, tmp_path, expression=query)
    native = (tmp_path / "diagnostic_ibis.dot").read_text()
    assert native == diagrams.to_graph(query).source
    assert "expectation_0" not in native
    assert "Native Ibis expression graph (diagnostic)" in (tmp_path / "diagnostic.md").read_text()
    ET.parse(tmp_path / "diagnostic_ibis.svg")


def test_invalid_columns_and_mixed_scopes_fail_explicitly():
    query = ibis.table({"a": "int64", "scope": "boolean"}, name="source")
    invalid = gxe.ExpectColumnValuesToNotBeNull(column="missing")
    with pytest.raises(ValueError, match="missing comparison column"):
        diagrams.build_field_diagram(query.schema(), "Invalid", [(0, invalid)])
    invalid_condition = gxe.ExpectColumnValuesToNotBeNull(
        column="a", row_condition=Column("missing") == True
    )
    with pytest.raises(ValueError, match="missing comparison column"):
        diagrams.build_field_diagram(query.schema(), "Invalid", [(0, invalid_condition)])
    first = gxe.ExpectColumnValuesToNotBeNull(column="a", row_condition=Column("scope") == True)
    second = gxe.ExpectColumnValuesToNotBeNull(column="a", row_condition=Column("scope") == False)
    suite = gx.ExpectationSuite(name="scopes", expectations=[first, second])
    assert len(diagrams.group_expectations(suite)) == 2
    with pytest.raises(ValueError, match="exactly one row-condition scope"):
        diagrams.build_field_diagram(query.schema(), "Mixed", [(0, first), (1, second)])
    with pytest.raises(TypeError, match="native GX"):
        diagrams.condition_columns("a > 1")
    assert json.dumps(first.configuration.kwargs["row_condition"], sort_keys=True) != json.dumps(
        second.configuration.kwargs["row_condition"], sort_keys=True
    )
