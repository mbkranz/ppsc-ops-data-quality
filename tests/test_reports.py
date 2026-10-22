"""Native Data Docs and JSON/Parquet reports, using an in-memory S3 test double."""

import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import duckdb
import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd
import pyarrow.parquet as pq
import pytest
import sqlglot
from great_expectations.core import RunIdentifier
from great_expectations.expectations.row_conditions import Column

from ppsc_ops_data_quality.runtime.reports import (
    publish_report_files,
    run_validations_with_reports,
)
from ppsc_ops_data_quality.schemas.validation_reports import (
    EXPECTATION_RUN_RESULTS,
    VALIDATION_RUN_RESULTS,
)


class MemoryS3:
    def __init__(self):
        self.objects = {}
        self.calls = []

    def put_object(self, **request):
        assert request["IfNoneMatch"] == "*"
        key = request["Key"]
        if key in self.objects:
            raise RuntimeError("precondition failed")
        self.objects[key] = request
        self.calls.append(key)


def report_inputs():
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    source = context.data_sources.add_pandas(name="fixture_source")
    suite = context.suites.add(
        gx.ExpectationSuite(
            name="fixture_suite",
            expectations=[
                gxe.ExpectColumnValuesToBeInSet(
                    column="value",
                    value_set=[1],
                    row_condition=Column("in_scope") == True,
                    meta={"check_id": "value_is_one", "source_requirement": "synthetic fixture"},
                )
            ],
        )
    )
    definitions, parameters, sources = [], {}, {}
    for name, value in (("passing", 1), ("failing", 0), ("later", 1)):
        batch = source.add_dataframe_asset(name=name).add_batch_definition_whole_dataframe("whole")
        definition = context.validation_definitions.add(
            gx.ValidationDefinition(name=name, data=batch, suite=suite)
        )
        definitions.append(definition)
        parameters[name] = {"dataframe": pd.DataFrame({"value": [value], "in_scope": [True]})}
        sources[name] = {
            "source_tables": [f"fixtures.{name}"],
            "source_query": f"SELECT value, in_scope FROM fixtures.{name}",
            "source_query_dialect": "duckdb",
        }
    return context, definitions, parameters, sources


def test_native_reports_publish_json_html_and_typed_parquet(tmp_path):
    context, definitions, parameters, sources = report_inputs()
    client = MemoryS3()
    directory = tmp_path / "run"
    results = run_validations_with_reports(
        context,
        definitions,
        run_directory=directory,
        sources=sources,
        batch_parameters=parameters,
        s3_uri="s3://reports-bucket/quality",
        s3_client=client,
        run_metadata={"source_snapshot": "fixture_v1"},
        run_id=RunIdentifier(
            run_name="fixture_run", run_time=datetime(2026, 10, 22, 0, 1, tzinfo=UTC)
        ),
    )
    assert [result.success for result in results.values()] == [True, False, True]
    manifest = json.loads((directory / "manifest.json").read_text())
    artifact_id = manifest["run_id"]
    assert client.calls[-1] == f"quality/runs/{artifact_id}/manifest.json"
    assert manifest["success"] is False
    assert manifest["run_status"] == "completed"
    assert any("/data_docs/validations/" in key and key.endswith(".html") for key in client.objects)
    assert any("/data_docs/static/" in key for key in client.objects)
    assert all(".parquet" in key for key in client.objects if "/analytics/" in key)
    raw_key = f"quality/runs/{artifact_id}/results/000_passing.json.gz"
    request = client.objects[raw_key]
    assert request["ContentType"] == "application/json"
    assert request["ContentEncoding"] == "gzip"
    assert json.loads(gzip.decompress(request["Body"])) == results["passing"].to_json_dict()

    validations = pq.read_table(directory / "analytics" / "validations.parquet")
    expectations = pq.read_table(directory / "analytics" / "expectations.parquet")
    assert validations.schema == VALIDATION_RUN_RESULTS.to_pyarrow()
    assert expectations.schema == EXPECTATION_RUN_RESULTS.to_pyarrow()
    assert validations.num_rows == expectations.num_rows == 3
    rows = validations.to_pylist()
    assert {row["validation_definition_name"] for row in rows} == set(sources)
    for row in rows:
        query = sources[row["validation_definition_name"]]["source_query"]
        assert row["source_query"] == query
        assert row["source_query_sha256"] == hashlib.sha256(query.encode()).hexdigest()
        assert row["source_tables"] == sources[row["validation_definition_name"]]["source_tables"]
        assert row["run_time_utc"] == datetime(2026, 10, 22, 0, 1)
        assert row["run_name"] == "fixture_run"
        assert row["run_id"] == artifact_id
        assert row["raw_result_uri"].startswith("s3://reports-bucket/quality/runs/")
    item = expectations.to_pylist()[0]
    assert item["check_id"] == "value_is_one"
    assert "in_scope" in item["row_condition_json"]
    assert json.loads(item["expectation_meta_json"])["source_requirement"] == "synthetic fixture"
    assert (
        f"quality/analytics/validations/run_date=2026-10-22/{artifact_id}.parquet" in client.objects
    )
    assert (
        f"quality/analytics/expectations/run_date=2026-10-22/{artifact_id}.parquet"
        in client.objects
    )

    with duckdb.connect() as connection:
        observed = connection.execute(
            "SELECT validation_definition_name, source_tables[1], "
            "json_extract_string(expectation_kwargs_json, '$.column'), success "
            "FROM read_parquet(?) ORDER BY validation_definition_name",
            [str(directory / "analytics" / "expectations.parquet")],
        ).fetchall()
    assert observed == [
        ("failing", "fixtures.failing", "value", False),
        ("later", "fixtures.later", "value", True),
        ("passing", "fixtures.passing", "value", True),
    ]


def test_execution_error_publishes_earlier_results_and_marks_missing_results(tmp_path):
    context, definitions, parameters, sources = report_inputs()
    client = MemoryS3()
    original = gx.ValidationDefinition.run

    def execute(definition, **kwargs):
        if definition.name == "failing":
            raise RuntimeError("synthetic execution failure")
        return original(definition, **kwargs)

    directory = tmp_path / "partial"
    with patch.object(gx.ValidationDefinition, "run", execute):
        with pytest.raises(RuntimeError, match="synthetic execution failure"):
            run_validations_with_reports(
                context,
                definitions,
                run_directory=directory,
                sources=sources,
                batch_parameters=parameters,
                s3_uri="s3://reports-bucket/quality",
                s3_client=client,
            )
    manifest = json.loads((directory / "manifest.json").read_text())
    assert manifest["run_status"] == "execution_error"
    assert manifest["success"] is False
    assert manifest["execution_error"]["type"] == "RuntimeError"
    rows = pq.read_table(directory / "analytics" / "validations.parquet").to_pylist()
    assert [row["validation_status"] for row in rows] == ["passed", "no_result", "no_result"]
    assert rows[1]["success"] is None
    assert rows[1]["raw_result_uri"] is None
    assert pq.read_table(directory / "analytics" / "expectations.parquet").num_rows == 1
    assert len(list((directory / "results").glob("*.json.gz"))) == 1
    assert client.calls[-1].endswith("/manifest.json")


def test_upload_failure_never_writes_completion_marker_or_hides_errors(tmp_path):
    raw = tmp_path / "result.json.gz"
    raw.write_bytes(gzip.compress(b"{}\n"))
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}")
    client = Mock()
    client.put_object.side_effect = OSError("S3 unavailable")
    with pytest.raises(OSError, match="S3 unavailable"):
        publish_report_files(
            {manifest: "runs/id/manifest.json", raw: "runs/id/result.json.gz"},
            s3_uri="s3://reports-bucket/prefix",
            manifest_path=manifest,
            s3_client=client,
        )
    assert client.put_object.call_count == 1
    assert client.put_object.call_args.kwargs["Key"].endswith("result.json.gz")


def test_both_validation_and_publication_errors_propagate(tmp_path):
    context, definitions, parameters, sources = report_inputs()
    client = Mock()
    client.put_object.side_effect = OSError("synthetic S3 failure")
    directory = tmp_path / "both_fail"
    with patch.object(
        gx.ValidationDefinition, "run", side_effect=RuntimeError("synthetic GX error")
    ):
        with pytest.raises(ExceptionGroup) as raised:
            run_validations_with_reports(
                context,
                definitions,
                run_directory=directory,
                sources=sources,
                batch_parameters=parameters,
                s3_uri="s3://reports-bucket/quality",
                s3_client=client,
            )
    assert [type(error) for error in raised.value.exceptions] == [RuntimeError, OSError]
    assert pq.read_table(directory / "analytics" / "expectations.parquet").num_rows == 0
    assert (
        pq.read_table(directory / "analytics" / "expectations.parquet").schema
        == EXPECTATION_RUN_RESULTS.to_pyarrow()
    )
    assert not any(
        call.kwargs["Key"].endswith("/manifest.json") for call in client.put_object.call_args_list
    )


def test_report_preflight_and_overwrite_reject_before_validation(tmp_path):
    context, definitions, parameters, sources = report_inputs()
    directory = tmp_path / "exists"
    directory.mkdir()
    with patch.object(gx.ValidationDefinition, "run") as execute:
        with pytest.raises(FileExistsError):
            run_validations_with_reports(
                context, definitions, run_directory=directory, sources=sources
            )
        with pytest.raises(ValueError, match="exactly"):
            run_validations_with_reports(
                context, definitions, run_directory=tmp_path / "a", sources={}
            )
        with pytest.raises(ValueError, match="s3://"):
            run_validations_with_reports(
                context,
                definitions,
                run_directory=tmp_path / "b",
                sources=sources,
                s3_uri="https://reports-bucket",
                batch_parameters=parameters,
            )
        execute.assert_not_called()


def test_catalog_ddl_columns_match_report_schemas():
    ddl = Path("sql/validation_reports_catalog.sql").read_text()
    statements = sqlglot.parse(ddl, read="athena")
    assert len(statements) == 2
    for statement, schema in zip(
        statements, (VALIDATION_RUN_RESULTS, EXPECTATION_RUN_RESULTS), strict=True
    ):
        assert [column.name for column in statement.this.expressions] == list(schema.names)
    assert "run_date STRING" in ddl
    assert "run_date=${run_date}/" in ddl
