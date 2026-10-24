"""Prepared evidence remains independent of observations and records NULL coverage."""

import json
import shutil
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import great_expectations as gx
import ibis
import pytest
import yaml
from ibis.common.exceptions import IntegrityError
from ppsc_metadata.artifacts import load_metadata_bundle
from ppsc_metadata.contracts import contract_yaml
from ppsc_metadata.sources.salesforce_rollup import RollupRequest
from test_account_to_survey_results_expectations import NEW, OLD, flow_inputs

from ppsc_ops_data_quality.account_to_survey_results import queries
from ppsc_ops_data_quality.account_to_survey_results.gx import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.account_to_survey_results.metadata import (
    COMPILER_WHEEL_SHA256,
    expected_value_contract,
    metadata_inputs,
)


@pytest.fixture
def backend():
    value = ibis.duckdb.connect()
    yield value
    value.disconnect()


def validate(frame, suite):
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    batch = (
        context.data_sources.add_pandas(name="evidence")
        .add_dataframe_asset(name="comparison")
        .add_batch_definition_whole_dataframe("whole")
        .get_batch(batch_parameters={"dataframe": frame})
    )
    result = batch.validate(
        suite,
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": ["validation_record_id"],
        },
    )
    assert all(not item.exception_info.get("raised_exception", False) for item in result.results)
    return result


def failed(result):
    return {item.expectation_config.meta["check_id"] for item in result.results if not item.success}


def test_assignment_is_provenance_and_retained_before_values_are_still_checked(backend):
    record, observed = flow_inputs()
    observed = observed.mutate(Lifestyle_Date_Time__c=ibis.timestamp(NEW))
    frame = backend.execute(queries.flow_account_comparison(record, observed))
    row = frame.iloc[0]
    assert row["expected__Basics_Date_Time__c__assigned"]
    assert not row["expected__Lifestyle_Date_Time__c__assigned"]
    assert row["expected__Lifestyle_Date_Time__c"] == OLD
    result = validate(frame, flow_account_suite())
    assert failed(result) == {"observed_Lifestyle_Date_Time__c_equals_expected"}
    item = next(item for item in result.results if not item.success)
    assert item.result["unexpected_index_list"][0]["validation_record_id"] == "s1"


def test_assigned_null_and_unknown_scope_remain_distinct(backend):
    record, observed = flow_inputs(completion_timestamp=None)
    frame = backend.execute(queries.flow_account_comparison(record, observed))
    assert frame.iloc[0]["expected__Basics_Date_Time__c__assigned"]
    assert frame["expected__Basics_Date_Time__c"].isna().all()
    assert "flow_scope_is_known" in failed(validate(frame, flow_account_suite()))


def test_unknown_eligibility_cannot_pass_as_an_unassigned_negative_finding(backend):
    record, observed = flow_inputs()
    record = record.mutate(Completion_Status__c=ibis.null().cast("string"))
    frame = backend.execute(queries.flow_account_comparison(record, observed))
    assert not frame.iloc[0].flow_evidence_is_complete
    assert frame["expected__Basics_Date_Time__c__assigned"].isna().all()
    result = validate(frame, flow_account_suite())
    assert "flow_computation_is_complete" in failed(result)


@pytest.mark.parametrize("unknown", [False, True])
def test_independent_presence_flags_and_native_gx(backend, unknown):
    record, observed = flow_inputs()
    field = "Lifestyle_Date_Time__c"
    record = record.mutate({f"Participant__r.Account.{field}": ibis.null().cast("timestamp")})
    observed = observed.mutate({field: ibis.null().cast("timestamp")})
    required = ibis.null().cast("boolean") if unknown else record.Survey_Index_Number__c == "2001"
    comparison = queries.flow_account_comparison(
        record,
        observed,
        required={"Basics_Date_Time__c": required},
        must_be_null={field: record.Survey_Index_Number__c == "2001"},
    )
    frame = backend.execute(comparison)
    suite = flow_account_suite(
        required_fields=("Basics_Date_Time__c",), must_be_null_fields=(field,)
    )
    result = validate(frame, suite)
    assert result.success is (not unknown)
    if unknown:
        assert frame["expected__Basics_Date_Time__c_required"].isna().all()
        assert "flow_computation_is_complete" in failed(result)
    else:
        frame[f"observed__{field}"] = OLD
        assert f"observed_{field}_must_be_null" in failed(validate(frame, suite))


def test_false_required_does_not_invent_must_be_null_and_observed_dependency_is_rejected(backend):
    record, observed = flow_inputs()
    frame = backend.execute(
        queries.flow_account_comparison(
            record,
            observed,
            required={"Basics_Date_Time__c": ibis.literal(False)},
        )
    )
    assert not frame.iloc[0]["expected__Basics_Date_Time__c_required"]
    assert "expected__Basics_Date_Time__c_must_be_null" not in frame.columns
    with pytest.raises(IntegrityError):
        queries.flow_account_comparison(
            record,
            observed,
            required={"Basics_Date_Time__c": observed.Basics_Date_Time__c.notnull()},
        )


def test_invalid_join_grain_blocks_field_comparison_but_preserves_structural_failure(backend):
    record, observed = flow_inputs()
    frame = backend.execute(
        queries.flow_account_comparison(record, observed.union(observed, distinct=False))
    )
    assert len(frame) == 2 and not frame.comparison_keys_are_valid.any()
    result = validate(frame, flow_account_suite())
    assert "one_comparison_row_per_survey_event" in failed(result)
    pair = next(
        item
        for item in result.results
        if item.expectation_config.meta["check_id"]
        == "observed_Basics_Date_Time__c_equals_expected"
    )
    assert pair.result["element_count"] == 0


def test_both_null_native_pair_coverage_is_recorded(backend):
    record, observed = flow_inputs()
    frame = backend.execute(queries.flow_account_comparison(record, observed))
    frame["expected__Age_at_Time_of_Consent__pc"] = None
    frame["observed__Age_at_Time_of_Consent__pc"] = None
    result = validate(frame, flow_account_suite())
    pair = next(
        item
        for item in result.results
        if item.expectation_config.meta["check_id"]
        == "observed_Age_at_Time_of_Consent__pc_equals_expected"
    )
    assert pair.success and pair.result["element_count"] == 1 and pair.result["missing_count"] == 1
    assert pair.result["unexpected_count"] == 0


def test_expected_contract_has_stable_before_references_and_native_source_paths():
    source = metadata_inputs()
    before = source.contract.model_dump(mode="json", by_alias=True, exclude_unset=True)
    contract = expected_value_contract()
    assert source.contract.model_dump(mode="json", by_alias=True, exclude_unset=True) == before
    expected = next(obj for obj in contract.schema_ if obj.name == "AccountExpected")
    for prop in expected.properties:
        assert prop.physicalName == f"expected__{prop.name}"
        definitions = prop.authoritativeDefinitions
        assert any(item.type == "transformationImplementation" for item in definitions)
        assert any(
            item.type == "fieldReference" and "/AccountBefore/" in item.url for item in definitions
        )
        for item in definitions:
            if item.type == "transformationImplementation":
                pointer = item.url.split("#", 1)[1]
                value = source.flow
                for token in pointer.strip("/").split("/"):
                    value = value[int(token)] if isinstance(value, list) else value[token]
                assert value is not None
    root = Path(__file__).resolve().parents[1]
    assert (
        sha256(
            (root / "vendor/1eedb2ab/ppsc_metadata-0.2.0-py3-none-any.whl").read_bytes()
        ).hexdigest()
        == COMPILER_WHEEL_SHA256
    )


@pytest.mark.parametrize(
    "operation,empty,expected",
    [
        ("count", 0, [2, 0]),
        ("sum", 0, [Decimal("0.30"), Decimal("0.00")]),
        ("min", None, [Decimal("0.10"), None]),
        ("max", None, [Decimal("0.20"), None]),
    ],
)
def test_selected_rollup_handoff_is_loaded_and_executed(
    tmp_path, backend, operation, empty, expected
):
    root = Path(__file__).resolve().parents[1] / "src/ppsc_ops_data_quality"
    copied = tmp_path / "package"
    shutil.copytree(root, copied)
    contract = metadata_inputs().contract
    document = yaml.safe_load(contract_yaml(contract))
    document["schema"][0]["properties"].append(
        {
            "id": "NativeValue",
            "name": "NativeValue",
            "logicalType": "number",
            "customProperties": [
                {"vendor": "ppsc", "property": "decimal", "value": {"precision": 12, "scale": 2}}
            ],
        }
    )
    contract_path = copied / "core/schemas/validation-inputs.odcs.yaml"
    contract_path.write_text(yaml.safe_dump(document))
    path = copied / "account_to_survey_results/metadata/rollups.json"
    path.write_text(
        json.dumps(
            {
                "Account.NativeValue": {
                    "summaryOperation": operation,
                    "summaryForeignKey": "Child.parent",
                    "summarizedField": "Child.amount",
                }
            }
        )
    )
    manifest_path = copied / "account_to_survey_results/metadata/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["artifacts"][0]["sha256"] = sha256(contract_path.read_bytes()).hexdigest()
    manifest["artifacts"].append(
        {
            "path": str(path.relative_to(copied)),
            "role": "rollup",
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
    )
    manifest_path.write_text(json.dumps(manifest))
    inputs = load_metadata_bundle(copied, manifest_path)
    parent = ibis.memtable({"Id": ["p1", "p2"]})
    child = ibis.memtable(
        {"parent": ["p1", "p1"], "amount": [Decimal("0.10"), Decimal("0.20")]},
        schema={"parent": "string", "amount": "decimal(12,2)"},
    )
    observed = parent.mutate(
        NativeValue=ibis.literal(Decimal("0.30")).cast(
            {
                "count": "int64",
                "sum": "decimal(38,2)",
                "min": "decimal(12,2)",
                "max": "decimal(12,2)",
            }[operation]
        )
    )
    result = queries.native_rollup_comparison(
        parent,
        child,
        observed,
        RollupRequest(output_field="NativeValue", child_object="Child", empty_value=empty),
        source_field="Account.NativeValue",
        inputs=inputs,
    )
    assert (
        backend.to_pyarrow(result.order_by("validation_record_id"))[
            "expected__NativeValue"
        ].to_pylist()
        == expected
    )


def test_missing_native_rollup_has_no_workbook_fallback():
    parent = ibis.table({"Id": "string"}, name="Parent")
    with pytest.raises(ValueError, match="No verified native rollup selected"):
        queries.native_rollup_comparison(
            parent,
            parent,
            parent,
            RollupRequest(
                output_field="Count_of_Completed_EHR_Auth__pc", child_object="Child", empty_value=0
            ),
            source_field="Account.Count_of_Completed_EHR_Auth__pc",
            inputs=metadata_inputs(),
        )


def test_source_parent_duplicates_cannot_disappear_in_rollup_aggregation(backend):
    account = ibis.memtable(
        {"Id": ["a1", "a1"], "PersonContactId": ["c1", "c1"], "IsPersonAccount": [True, True]}
    )
    survey = ibis.memtable(
        {
            "Participant__c": ["c1"],
            "Completion_Status__c": ["Complete"],
            "Survey_Index_Number__c": ["1001"],
            "Consent_Status__c": ["Yes"],
            "Consent_Revoked__c": [False],
        }
    )
    observed = ibis.memtable(
        {
            "Id": ["a1"],
            **{
                field: [2 if field == "Count_of_Completed_Primary_Consent__pc" else 0]
                for field in queries.ROLLUP_ACCOUNT_FIELDS
            },
        }
    )
    frame = backend.execute(queries.rollup_account_comparison(account, survey, observed))
    assert len(frame) == 1 and not frame.iloc[0].comparison_keys_are_valid
    assert failed(validate(frame, rollup_account_suite())) == {
        "rollup_source_parent_keys_are_valid"
    }
