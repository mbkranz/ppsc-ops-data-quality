"""Cross-source and independent-Flow acceptance of the shared consumer boundary."""

import json
from hashlib import sha256

import great_expectations as gx
import ibis
import pandas as pd
import pytest
from ppsc_metadata.artifacts import load_metadata_bundle
from ppsc_metadata.sources.salesforce_flow import FlowRequest
from ppsc_metadata.sources.salesforce_rollup import RollupRequest
from pydantic import ValidationError

from ppsc_ops_data_quality.core.comparison import (
    ComparisonSpec,
    KeyBinding,
    ValueBinding,
    compare_values,
)
from ppsc_ops_data_quality.core.comparison_gx import comparison_suite
from ppsc_ops_data_quality.sources.salesforce import flow_comparison, native_rollup_comparison


@pytest.fixture
def backend():
    connection = ibis.duckdb.connect()
    yield connection
    connection.disconnect()


def validate(backend, comparison, spec):
    suite = comparison_suite(spec, name="independent_source")
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    batch = (
        context.data_sources.add_pandas(name="source")
        .add_dataframe_asset(name="comparison")
        .add_batch_definition_whole_dataframe("whole")
        .get_batch(batch_parameters={"dataframe": backend.execute(comparison)})
    )
    result = batch.validate(
        suite,
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": suite.meta["finding_key_columns"],
        },
    )
    assert not any(item.exception_info.get("raised_exception") for item in result.results)
    return {item.expectation_config.meta["check_id"]: item for item in result.results}


def migration_spec():
    return ComparisonSpec(
        keys=(
            KeyBinding(name="tenant", expected="organization", observed="site"),
            KeyBinding(name="response", expected="response", observed="response_id"),
        ),
        values=(
            ValueBinding(
                name="answer",
                expected="mapped_answer",
                observed="QID42",
                deterministic="known",
                assigned="written",
                required="displayed",
                must_be_null="hidden",
            ),
        ),
        scope="eligible",
    )


def migration_inputs():
    # These are prepared mapping/display-rule outputs, not a second interpreter
    # for Qualtrics logic. Typed false, zero and sentinels remain physical values.
    expected = ibis.memtable(
        {
            "organization": ["a", "b", "a", "a"],
            "response": ["r1", "r1", "r2", "r3"],
            "mapped_answer": [0, -99, None, 7],
            "known": [True] * 4,
            "written": [False, True, True, False],
            "displayed": [True, False, False, False],
            "hidden": [False, False, True, False],
            "eligible": [True] * 4,
        },
        schema={
            "organization": "string",
            "response": "string",
            "mapped_answer": "int64",
            "known": "boolean",
            "written": "boolean",
            "displayed": "boolean",
            "hidden": "boolean",
            "eligible": "boolean",
        },
    )
    observed = ibis.memtable(
        {
            "site": ["a", "b", "a", "a"],
            "response_id": ["r1", "r1", "r2", "r3"],
            "QID42": [0, -99, None, 7],
        },
        schema={"site": "string", "response_id": "string", "QID42": "int64"},
    )
    return expected, observed


def test_migration_columns_composite_grain_and_native_gx(backend):
    expected, observed = migration_inputs()
    spec = migration_spec()
    result = validate(backend, compare_values(expected, observed, spec), spec)
    assert all(item.success for item in result.values())
    # Both-null pairs are visible as native coverage, not a compared answer.
    assert result["answer_equals_expected"].result["missing_count"] == 1
    changed = observed.mutate(QID42=ibis.ifelse(observed.response_id == "r3", 99, observed.QID42))
    result = validate(backend, compare_values(expected, changed, spec), spec)
    assert not result["answer_equals_expected"].success  # assignment false still compares
    assert (
        result["answer_equals_expected"].result["unexpected_index_list"][0][
            "expected_key__response"
        ]
        == "r3"
    )


@pytest.mark.parametrize("side", ["expected", "observed"])
def test_duplicates_preserve_fanout_and_block_equality(backend, side):
    expected, observed = migration_inputs()
    if side == "expected":
        expected = expected.union(expected.filter(expected.response == "r2"), distinct=False)
    else:
        observed = observed.union(observed.filter(observed.response_id == "r2"), distinct=False)
    comparison = compare_values(expected, observed, migration_spec())
    frame = backend.execute(comparison)
    assert len(frame) == 5
    assert not frame.loc[frame.expected_key__response == "r2", "comparison_keys_are_valid"].any()
    assert not validate(backend, comparison, migration_spec())["comparison_grain_valid"].success


def test_unmatched_observations_and_missing_expected_keys_survive(backend):
    expected, observed = migration_inputs()
    expected = expected.mutate(
        response=ibis.ifelse(
            expected.response == "r3", ibis.null().cast("string"), expected.response
        )
    )
    comparison = compare_values(expected, observed, migration_spec())
    frame = backend.execute(comparison)
    assert len(frame) == 5  # missing expected key and independently unmatched observation
    assert (frame.comparison_keys_are_valid == False).sum() == 2
    result = validate(backend, comparison, migration_spec())
    assert not result["comparison_grain_valid"].success
    assert not result["computation_complete"].success


@pytest.mark.parametrize("column", ["known", "written", "displayed", "hidden", "eligible"])
def test_unknown_evidence_is_incomplete_instead_of_success(backend, column):
    expected, observed = migration_inputs()
    expected = expected.mutate({column: ibis.null().cast("boolean")})
    result = validate(
        backend, compare_values(expected, observed, migration_spec()), migration_spec()
    )
    assert not result["scope_known" if column == "eligible" else "computation_complete"].success


def test_bindings_reject_collisions_and_implicit_key_casts():
    expected, observed = migration_inputs()
    with pytest.raises(ValueError, match="key types must match"):
        compare_values(expected, observed.mutate(response_id=ibis.literal(1)), migration_spec())
    with pytest.raises(ValueError, match="value types must match"):
        compare_values(expected, observed.mutate(QID42=ibis.literal(False)), migration_spec())
    with pytest.raises(ValueError, match="value types must match"):
        compare_values(expected, observed.mutate(QID42=ibis.literal("0")), migration_spec())
    with pytest.raises(ValueError, match="must be boolean"):
        compare_values(expected.mutate(known=ibis.literal(1)), observed, migration_spec())
    with pytest.raises(ValidationError, match="output names collide"):
        ComparisonSpec(
            keys=migration_spec().keys,
            values=(
                ValueBinding(name="a", expected="x", observed="y", assigned="z"),
                ValueBinding(name="a__assigned", expected="x", observed="y"),
            ),
        )


def verified_inputs(tmp_path, object_name, field, literal):
    # Different native objects, target fields, Flow names/versions and values;
    # these do not copy the deployed Account/survey fixture.
    flow = {
        "Id": f"version-{object_name}",
        "FullName": f"set-{object_name}",
        "Metadata": {
            "start": {
                "scheduledPaths": [
                    {"pathType": "AsyncAfterCommit", "connector": {"targetReference": "write"}}
                ]
            },
            "recordUpdates": [
                {
                    "name": "write",
                    "object": object_name,
                    "filters": [
                        {
                            "field": "Id",
                            "operator": "EqualTo",
                            "value": {"elementReference": "$Record.target"},
                        }
                    ],
                    "inputAssignments": [{"field": field, "value": literal}],
                }
            ],
        },
    }
    contract = {
        "apiVersion": "v3.2.0",
        "kind": "DataContract",
        "id": object_name,
        "version": "1",
        "schema": [
            {
                "name": object_name,
                "properties": [
                    {"name": "Key", "logicalType": "string"},
                    {"name": field, "logicalType": "integer"},
                ],
            }
        ],
    }
    rollups = {
        f"{object_name}.{field}": {"summaryOperation": "count", "summaryForeignKey": "Line.owner"}
    }
    artifacts = []
    for filename, role, payload in (
        ("contract.json", "contract", contract),
        ("flow.json", "flow", flow),
        ("rollups.json", "rollup", rollups),
    ):
        raw = json.dumps(payload).encode()
        (tmp_path / filename).write_bytes(raw)
        artifacts.append({"path": filename, "role": role, "sha256": sha256(raw).hexdigest()})
    manifest = {
        "org": "synthetic",
        "flow_name": flow["FullName"],
        "flow_version_id": flow["Id"],
        "source_revision": "a" * 40,
        "provisional": True,
        "coverage": "independent synthetic objects only",
        "artifacts": artifacts,
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return load_metadata_bundle(tmp_path, tmp_path / "manifest.json")


@pytest.mark.parametrize(
    "object_name,field,value",
    [("Case", "PriorityRank__c", 0), ("Order__c", "MigrationStatus__c", -99)],
)
def test_independent_verified_flows_have_no_account_defaults(
    tmp_path, backend, object_name, field, value
):
    inputs = verified_inputs(tmp_path, object_name, field, {"numberValue": value})
    request = FlowRequest(
        object_name=object_name,
        fields=(field,),
        before_prefix="before.",
        target_reference="$Record.target",
    )
    spec = ComparisonSpec(
        keys=(KeyBinding(name="target", expected="target", observed="external_key"),),
        values=(
            ValueBinding(
                name=field,
                expected="computed",
                observed="destination",
                deterministic="known",
                assigned="assigned",
            ),
        ),
    )
    record = ibis.memtable({"target": ["x"], f"before.{field}": [4], "eligible": [True]})
    observed = ibis.memtable({"external_key": ["x"], "destination": [value]})
    comparison = flow_comparison(
        record, observed, request, spec, inputs=inputs, eligibility=lambda r: r.eligible
    )
    assert all(item.success for item in validate(backend, comparison, spec).values())
    retained = flow_comparison(
        record.mutate(eligible=False),
        observed.mutate(destination=ibis.literal(4, type="int64")),
        request,
        spec,
        inputs=inputs,
        eligibility=lambda r: r.eligible,
    )
    assert all(item.success for item in validate(backend, retained, spec).values())
    unknown = flow_comparison(
        record.mutate(eligible=ibis.null().cast("boolean")),
        observed,
        request,
        spec,
        inputs=inputs,
        eligibility=lambda r: r.eligible,
    )
    assert not validate(backend, unknown, spec)["computation_complete"].success
    with pytest.raises(ValueError, match="determinism and assignment"):
        flow_comparison(
            record,
            observed,
            request,
            ComparisonSpec(
                keys=spec.keys,
                values=(ValueBinding(name=field, expected="computed", observed="destination"),),
            ),
            inputs=inputs,
            eligibility=lambda r: r.eligible,
        )


def test_rollup_on_non_account_object_with_custom_parent_key(tmp_path, backend):
    inputs = verified_inputs(tmp_path, "Invoice__c", "LineCount__c", {"numberValue": 0})
    parent = ibis.memtable({"Key": ["i1", "i2"]})
    child = ibis.memtable({"owner": ["i1", "i1"]})
    observed = ibis.memtable({"Key": ["i1", "i2", "unexpected"], "LineCount__c": [2, 0, 0]})
    comparison = native_rollup_comparison(
        parent,
        child,
        observed,
        RollupRequest(
            parent_key="Key", output_field="LineCount__c", child_object="Line", empty_value=0
        ),
        source_field="Invoice__c.LineCount__c",
        inputs=inputs,
    )
    frame = backend.execute(comparison)
    assert not any("account" in name for name in frame.columns)
    assert sorted(frame.expected__LineCount__c.dropna()) == [0, 2]
    assert not frame.loc[
        frame.observed_key__parent == "unexpected", "comparison_keys_are_valid"
    ].any()


@pytest.mark.parametrize(
    "dtype,value", [("boolean", False), ("string", '["a|b","-99"]'), ("decimal(12,2)", "0.00")]
)
def test_field_names_and_physical_values_are_not_interpreted(backend, dtype, value):
    expected = ibis.memtable({"key": ["r"]}).mutate({"source.raw": ibis.literal(value).cast(dtype)})
    observed = ibis.memtable({"external": ["r"]}).mutate(
        {"target raw": ibis.literal(value).cast(dtype)}
    )
    spec = ComparisonSpec(
        keys=(KeyBinding(name="row", expected="key", observed="external"),),
        values=(ValueBinding(name="mapped", expected="source.raw", observed="target raw"),),
    )
    assert all(
        item.success
        for item in validate(backend, compare_values(expected, observed, spec), spec).values()
    )


def test_generic_reconciliation_sql_executes_after_shared_renderer(backend):
    from ppsc_ops_data_quality.core.queries.sql import to_sqlglot

    expected, observed = migration_inputs()
    expected = backend.create_table("migration_expected", expected)
    observed = backend.create_table("survey_observed", observed)
    comparison = compare_values(expected, observed, migration_spec())
    query = to_sqlglot(comparison)
    direct = (
        backend.execute(comparison)
        .sort_values(["expected_key__tenant", "expected_key__response"])
        .reset_index(drop=True)
    )
    rendered = (
        backend.con.execute(query.sql(dialect="duckdb"))
        .fetchdf()
        .sort_values(["expected_key__tenant", "expected_key__response"])
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(direct, rendered, check_dtype=False)
    assert "FULL OUTER JOIN" in to_sqlglot(comparison).sql(dialect="athena")


def test_shared_adapters_do_not_import_the_account_workflow():
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import ppsc_ops_data_quality.sources.salesforce; import ppsc_ops_data_quality.core.comparison_gx; assert not any('account_to_survey_results' in name for name in sys.modules)",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_existing_flow_can_use_explicit_shared_adapter_without_legacy_aliases(backend):
    from test_account_to_survey_results_expectations import flow_inputs

    from ppsc_ops_data_quality.account_to_survey_results.metadata import (
        metadata_inputs,
        metadata_request,
    )
    from ppsc_ops_data_quality.account_to_survey_results.queries import flow_account_comparison

    record, observed = flow_inputs()
    request = metadata_request()
    spec = ComparisonSpec(
        keys=(
            KeyBinding(name="event", expected="Id", observed="survey_result_id"),
            KeyBinding(name="target", expected="Participant__r.Account.Id", observed="Id"),
        ),
        values=tuple(
            ValueBinding(
                name=field,
                expected=f"computed_{index}",
                observed=field,
                deterministic=f"known_{index}",
                assigned=f"assigned_{index}",
            )
            for index, field in enumerate(request.fields)
        ),
    )
    comparison = flow_comparison(
        record,
        observed,
        request,
        spec,
        inputs=metadata_inputs(),
        eligibility=lambda r: r.Completion_Status__c == "Complete",
    )
    legacy = backend.execute(flow_account_comparison(record, observed))
    shared = backend.execute(comparison)
    for field in request.fields:
        pd.testing.assert_series_equal(shared[f"expected__{field}"], legacy[f"expected__{field}"])
    assert all(item.success for item in validate(backend, comparison, spec).values())
