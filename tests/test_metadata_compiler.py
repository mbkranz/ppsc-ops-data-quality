"""Standalone local builders retain independent native-Flow acceptance behavior."""

from pathlib import Path

import ibis
import pytest
from test_flow_derivations import NEW, OLD, build, fixtures

from ppsc_ops_data_quality.account_to_survey_results import queries as query
from ppsc_ops_data_quality.account_to_survey_results.metadata import (
    load_definition_inputs,
    metadata_receipt,
)
from ppsc_ops_data_quality.core.projection import conditional_values


def test_duplicate_input_events_are_retained_through_lookups():
    trigger, surveys, account, contact = fixtures("1003")
    record = query.join_account(trigger, contact, account)
    record = record.union(record, distinct=False)
    record = query.add_flow_context(record, surveys, flow_run_date=ibis.date("2026-10-23"))
    backend = ibis.duckdb.connect()
    try:
        rows = backend.execute(query.expected_account_values(record))
        assert len(rows) == 2 and (rows.EHR_Consent_Date_Time__c == NEW).all()
    finally:
        backend.disconnect()


@pytest.mark.parametrize("permission", [None, "1007"])
@pytest.mark.parametrize("earliest", [None, OLD])
def test_assent_truth_table_uses_native_and_default_branch(permission, earliest):
    backend = ibis.duckdb.connect()
    try:
        row = backend.execute(build("1008", prior=permission, earliest=earliest)).iloc[0]
        assert row.Earliest_Primary_Consent_Date_for_Report__c == (
            OLD if permission and earliest else NEW
        )
    finally:
        backend.disconnect()


def test_source_neutral_ordered_assignments_preserve_null_false_zero_and_before():
    backend = ibis.duckdb.connect()
    try:
        record = ibis.memtable(
            {"old": [7, 7, 7], "first": [True, False, False], "second": [True, True, False]}
        )
        projection = conditional_values(
            {"score": record.old},
            [
                (record.first, {"score": ibis.null().cast("int64")}),
                (record.second, {"score": ibis.literal(0)}),
            ],
        )
        values = backend.execute(record.select(projection["score"]))
        assert values.iloc[0].isna().all() and values.iloc[1, 0] == 0 and values.iloc[2, 0] == 7
    finally:
        backend.disconnect()


def test_pinned_definitions_cover_code_schema_and_native_source_identity():
    root = Path(__file__).resolve().parents[1] / "src/ppsc_ops_data_quality"
    receipt = metadata_receipt()
    assert receipt.manifest.version == "ops-definitions/v2" and receipt.manifest.provisional
    assert {"code", "schema", "selection", "lineage", "flow", "source"} == {
        a.role for a in receipt.manifest.artifacts
    }
    assert load_definition_inputs(root).flow["Id"] == "301SL00000dpJqKYAU"


def test_live_metadata_mismatch_fails_before_creating_a_gx_context(tmp_path, monkeypatch):
    import re

    from ppsc_ops_data_quality.account_to_survey_results import validation
    from ppsc_ops_data_quality.account_to_survey_results.configuration import (
        load_validation_configuration,
    )

    path = tmp_path / "runtime.yaml"
    path.write_text(
        re.sub(r"REPLACE_WITH_[A-Z_]+", "fixture", Path("params.example.yaml").read_text())
    )
    request = load_validation_configuration(path)
    request = request.model_copy(
        update={"metadata": request.metadata.model_copy(update={"org": "another-org"})}
    )

    def fail(**kwargs):
        raise AssertionError("No context or connection should be created")

    monkeypatch.setattr(validation.gx, "get_context", fail)
    with pytest.raises(ValueError, match="org/version/hash"):
        validation.run_validation(request, run_directory=tmp_path / "run")
    assert not (tmp_path / "run").exists()
