"""Compilation must consume the verified snapshot, never a caller's mutable copy."""

import json
import shutil
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import ibis
import pytest
from test_account_to_survey_results_expectations import flow_inputs

from ppsc_ops_data_quality.account_to_survey_results import metadata
from ppsc_ops_data_quality.account_to_survey_results.metadata import (
    metadata_inputs,
    metadata_receipt,
    metadata_request,
)
from ppsc_ops_data_quality.account_to_survey_results.queries import flow_account_comparison


def comparison_sql(record, observed):
    return str(ibis.to_sql(flow_account_comparison(record, observed), dialect="duckdb"))


def test_mutating_returned_metadata_cannot_change_receipted_compilation():
    record, observed = flow_inputs()
    expected_sql = comparison_sql(record, observed)
    receipt = metadata_receipt()
    bundle = metadata_inputs()
    original = deepcopy(bundle["flow"])
    try:
        assignment = next(
            node
            for node in bundle["flow"]["Metadata"]["recordUpdates"]
            if node["name"] == "updateAccount2001"
        )
        assignment["inputAssignments"][0]["value"] = {"dateTimeValue": None}
        assert metadata_receipt() == receipt
        assert comparison_sql(record, observed) == expected_sql
    finally:
        bundle["flow"].clear()
        bundle["flow"].update(original)


def test_repeated_loads_and_configuration_return_independent_objects():
    first, second = metadata_inputs(), metadata_inputs()
    assert first == second and first is not second
    first["tables"].clear()
    first["flow"]["Metadata"]["decisions"].clear()
    assert metadata_inputs() == second
    request = metadata_request()
    request.resource_aliases.clear()
    assert metadata_request().resource_aliases
    receipt = metadata_receipt()
    assert (
        receipt["flow_request_sha256"]
        == sha256(metadata_request().model_dump_json().encode()).hexdigest()
    )


def test_configuration_change_rejects_receipt_without_changing_compilation(monkeypatch):
    record, observed = flow_inputs()
    expected_sql = comparison_sql(record, observed)
    monkeypatch.setitem(
        metadata.FLOW_REQUEST.resource_aliases, "getFirstPhysicalMeasurement", "bad"
    )
    assert comparison_sql(record, observed) == expected_sql
    with pytest.raises(ValueError, match="changed after compilation"):
        metadata_receipt()


def test_input_replacement_under_same_name_rejects_receipt(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1] / "src/ppsc_ops_data_quality"
    copied = tmp_path / "package"
    shutil.copytree(root, copied)
    monkeypatch.setattr(metadata, "files", lambda _: copied)
    metadata_receipt()
    path = copied / "account_to_survey_results/metadata/flow.json"
    native = json.loads(path.read_text())
    native["Metadata"]["description"] = "changed under the same name"
    path.write_text(json.dumps(native))
    with pytest.raises(ValueError, match="changed after compilation"):
        metadata_receipt()


def test_changed_compiler_version_rejects_receipt(monkeypatch):
    metadata_receipt()
    monkeypatch.setattr(metadata, "version", lambda _: "different-compiler")
    with pytest.raises(ValueError, match="changed after compilation"):
        metadata_receipt()
