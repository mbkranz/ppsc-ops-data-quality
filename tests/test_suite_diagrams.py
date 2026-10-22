"""Real Ibis graphs preserve GX column bindings and compound row conditions."""

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import great_expectations as gx
import great_expectations.expectations as gxe
import ibis
import pytest

from ppsc_ops_data_quality.account_to_survey_results_expectations import (
    flow_account_suite,
)
from ppsc_ops_data_quality.demo import comparisons
from ppsc_ops_data_quality.schemas import history_tables

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


def test_graph_connects_expectations_to_columns_and_compound_condition():
    query = query_expressions()["flow"]
    suite = flow_account_suite(expected_row_count=1)
    source = diagrams.annotated_graph(query, suite).source
    for index, expectation in enumerate(suite.expectations):
        kwargs = expectation.configuration.kwargs
        for role, column in diagrams.expectation_columns(kwargs):
            field_id = query.columns.index(column)
            assert f"output_{field_id} -> expectation_{index} [label={role}" in source
    cabor = next(
        index
        for index, e in enumerate(suite.expectations)
        if e.meta["check_id"] == "observed_CABOR_Completion_Date__c_equals_expected"
    )
    condition = suite.expectations[cabor].row_condition
    assert diagrams.condition_columns(condition) == [
        "survey_completion_occurred_on_or_after_launch",
        "cabor_lookup_is_deterministic",
    ]
    assert f"condition_1 -> expectation_{cabor}" in source
    for column in diagrams.condition_columns(condition):
        assert f"output_{query.columns.index(column)} -> condition_1" in source
    # The cutoff is in the native Ibis expression graph, not inferred from GX text.
    assert "2024-12-16" in source
    assert "GreaterEqual" in source
    assert str(hash(query.op())) in source
    assert "label=table" in source  # Optional count attaches to the final relation.


def test_write_both_suite_documents_with_valid_svg_and_no_validation(tmp_path):
    assert diagrams.main(["--output", str(tmp_path)]) == 0
    for name, count in (("flow", 27), ("rollups", 24)):
        slug = f"account_to_survey_results_{name}"
        markdown = (tmp_path / f"{slug}.md").read_text()
        assert f"{count} expectations;" in markdown
        assert "Row condition" in markdown
        assert f"]({slug}.svg)" in markdown
        root = ET.parse(tmp_path / f"{slug}.svg").getroot()
        titles = [node.text for node in root.iter("{http://www.w3.org/2000/svg}title")]
        for index in range(count):
            assert f"expectation_{index}" in titles
        dot = (tmp_path / f"{slug}.dot").read_text()
        if name == "flow":
            assert "applies when True" in dot
            assert "survey_completion_occurred_on_or_after_launch" in markdown
            assert "cabor_lookup_is_deterministic" in markdown
        else:
            assert "condition_0" not in dot
            assert "All rows (no row condition)" in markdown


def test_invalid_column_binding_fails_instead_of_drawing_false_lineage():
    query = ibis.table({"a": "int64"}, name="source").select("a")
    suite = gx.ExpectationSuite(
        name="invalid", expectations=[gxe.ExpectColumnValuesToNotBeNull(column="missing")]
    )
    with pytest.raises(ValueError, match="missing Ibis output column"):
        diagrams.annotated_graph(query, suite)
    with pytest.raises(TypeError, match="native GX"):
        diagrams.condition_columns("a > 1")
