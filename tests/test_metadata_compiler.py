"""Behavioral acceptance for metadata-driven construction, independent observations."""

from copy import deepcopy
from pathlib import Path

import ibis
import pytest
from salesforce.entities.field_definitions.rollups import CountRollupRequest, count_rollup
from salesforce.entities.flows.queries import (
    UnsupportedFlowError,
    flow_assignments,
    flow_context,
)
from test_flow_derivations import NEW, OLD, build, fixtures

from ppsc_ops_data_quality.account_to_survey_results import queries as query
from ppsc_ops_data_quality.account_to_survey_results.metadata import (
    FLOW_REQUEST,
    metadata_inputs,
)


def selected(metadata, *, field="Basics_Date_Time__c", index="2001", duplicate=False):
    trigger, surveys, account, contact = fixtures(index)
    record = query.join_account(trigger, contact, account)
    if duplicate:
        record = record.union(record, distinct=False)
    request = FLOW_REQUEST.model_copy(update={"fields": (field,)})
    record = flow_context(
        record,
        {"Survey_Result__c": surveys},
        metadata,
        request,
        flow_run_date=ibis.date("2026-10-23"),
        eligibility=query._eligible,
    )
    projection = flow_assignments(record, metadata, request, eligibility=query._eligible)
    return record.select(projection[f"expected__{field}"])


def test_metadata_mutation_changes_predicates_assignments_and_preserves_null():
    native = metadata_inputs()["flow"]["Metadata"]
    backend = ibis.duckdb.connect()
    try:
        assert backend.execute(selected(native)).iloc[0, 0] == NEW
        changed = deepcopy(native)
        assignment = next(
            node for node in changed["recordUpdates"] if node["name"] == "updateAccount2001"
        )
        assignment["inputAssignments"][0]["value"] = {"dateTimeValue": "2020-01-02 00:00:00"}
        assert str(backend.execute(selected(changed)).iloc[0, 0]) == "2020-01-02 00:00:00"
        assignment["inputAssignments"][0]["value"] = {"dateTimeValue": None}
        assert backend.execute(selected(changed)).isna().all().all()
        changed = deepcopy(native)
        decision = next(node for node in changed["decisions"] if node["name"] == "Survey_Index")
        rule = next(rule for rule in decision["rules"] if rule["name"] == "X2001_The_Basics")
        rule["conditions"][0]["rightValue"]["stringValue"] = "2999"
        assert backend.execute(selected(changed)).iloc[0, 0] == OLD
    finally:
        backend.disconnect()


def test_unrelated_unsupported_formula_does_not_block_a_requested_slice():
    native = deepcopy(metadata_inputs()["flow"]["Metadata"])
    native["formulas"][0]["expression"] = "UNSUPPORTED()"
    selected(native)
    with pytest.raises(UnsupportedFlowError, match="Unsupported native formula"):
        selected(native, field="Age_at_Time_of_Consent__pc", index="1001")


def test_duplicate_input_events_are_retained_through_lookups():
    native = metadata_inputs()["flow"]["Metadata"]
    backend = ibis.duckdb.connect()
    try:
        rows = backend.execute(
            selected(native, field="EHR_Consent_Date_Time__c", index="1003", duplicate=True)
        )
        assert len(rows) == 2 and (rows.iloc[:, 0] == NEW).all()
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


def test_count_adapter_and_source_neutral_projection_execute_without_salesforce_names():
    backend = ibis.duckdb.connect()
    try:
        parent = ibis.memtable({"Id": ["p1", "p1", "p2"]})
        child = ibis.memtable(
            {"ParentId": ["p1", "p1", "other"], "status": ["done", "done", "done"]}
        )
        # Synthetic native metadata proves the adapter; it is not an asserted org rule.
        metadata = {
            "summaryOperation": "count",
            "summaryForeignKey": "Order.ParentId",
            "summaryFilterItems": [
                {"field": "Order.status", "operation": "equals", "value": "done"}
            ],
        }
        result = backend.execute(
            count_rollup(
                parent,
                child,
                metadata,
                CountRollupRequest(output_field="count", child_object="Order"),
            )
        )
        assert sorted(zip(result.Id, result["count"], strict=True)) == [
            ("p1", 2),
            ("p1", 2),
            ("p2", 0),
        ]
    finally:
        backend.disconnect()


def test_live_metadata_mismatch_fails_before_creating_a_gx_context(tmp_path, monkeypatch):
    import re

    from ppsc_ops_data_quality.account_to_survey_results import workflow as validation
    from ppsc_ops_data_quality.account_to_survey_results.workflow import (
        load_validation_configuration,
    )

    example = Path(__file__).resolve().parents[1] / "params.example.yaml"
    path = tmp_path / "runtime.yaml"
    path.write_text(re.sub(r"REPLACE_WITH_[A-Z_]+", "fixture", example.read_text()))
    request = load_validation_configuration(path)
    request = request.model_copy(
        update={"metadata": request.metadata.model_copy(update={"org": "another-org"})}
    )

    def fail(**kwargs):
        raise AssertionError("No context or connection should be created")

    monkeypatch.setattr(validation.gx, "get_context", fail)
    with pytest.raises(ValueError, match="org/version"):
        validation.run_validation(request, run_directory=tmp_path / "run")
    assert not (tmp_path / "run").exists()
