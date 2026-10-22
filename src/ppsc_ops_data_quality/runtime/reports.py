"""Build native Data Docs, archive GX JSON, and publish typed discovery tables.

Native results remain authoritative. The Parquet projections have explicit Ibis
schemas and versioned, stable columns; heterogeneous GX details remain JSON text.
No GX context/connection configuration, credentials or batch DataFrames are copied.
S3 writes use the caller's client or the standard boto3 credential chain. This
module creates no bucket, website, IAM policy, Glue table or Athena query execution.
"""

import gzip
import hashlib
import json
import mimetypes
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import great_expectations as gx
import pyarrow as pa
import pyarrow.parquet as pq
from great_expectations.core import RunIdentifier

from ppsc_ops_data_quality.schemas.validation_reports import (
    EXPECTATION_RUN_RESULTS,
    VALIDATION_RUN_RESULTS,
)

from .artifacts import validation_artifact_stem
from .runner import _validate_targets, run_validations


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _s3_location(uri: str) -> tuple[str, str]:
    parsed = urlsplit(uri)
    if parsed.scheme != "s3" or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError("Report destination must be s3://bucket/optional-prefix")
    return parsed.netloc, parsed.path.strip("/")


def publish_report_files(
    files: Mapping[Path, str], *, s3_uri: str, manifest_path: Path, s3_client=None
) -> None:
    """Upload an explicit artifact allowlist, then the manifest as a completion marker.

    The mapping assigns each local path its key relative to s3_uri. Upload complete
    Data Docs assets, not just HTML. IfNoneMatch='*' refuses overwritten evidence;
    a failed upload propagates and leaves no new completion marker. S3 objects are
    individually atomic; this is not a multi-object transaction. No public ACL or
    website hosting is enabled. Bucket encryption/access policy is caller-owned.
    """
    bucket, prefix = _s3_location(s3_uri)
    if s3_client is None:
        import boto3

        s3_client = boto3.client("s3")
    ordered = [path for path in files if path != manifest_path] + [manifest_path]
    for path in ordered:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        options = {}
        if path.name.endswith(".json.gz"):
            content_type = "application/json"
            options["ContentEncoding"] = "gzip"
        s3_client.put_object(
            Bucket=bucket,
            Key="/".join(part for part in (prefix, files[path]) if part),
            Body=path.read_bytes(),
            ContentType=content_type,
            IfNoneMatch="*",
            **options,
        )


def _write_discovery_tables(
    definitions, sources, directory, identity, artifact_uri, run_metadata, expectation_parameters
):
    validations = []
    expectations = []
    for index, definition in enumerate(definitions):
        stem = validation_artifact_stem(index, definition.name)
        source = sources[definition.name]
        raw_path = directory / "results" / f"{stem}.json.gz"
        payload = json.loads(gzip.decompress(raw_path.read_bytes())) if raw_path.exists() else None
        base = {
            **identity,
            "validation_definition_name": definition.name,
            "validation_definition_id": str(definition.id) if definition.id else None,
            "suite_name": definition.suite.name,
            "data_source_name": definition.data.data_asset.datasource.name,
            "data_asset_name": definition.data.data_asset.name,
            "source_tables": list(source["source_tables"]),
            "source_query_dialect": source["source_query_dialect"],
            "source_query": source["source_query"],
            "source_query_sha256": hashlib.sha256(source["source_query"].encode()).hexdigest(),
            "source_query_uri": artifact_uri(f"queries/{stem}.sql"),
            "raw_result_uri": artifact_uri(f"results/{stem}.json.gz") if payload else None,
            "data_docs_uri": artifact_uri("data_docs/index.html"),
            "run_metadata_json": _json(run_metadata),
            "expectation_parameters_json": _json(expectation_parameters.get(definition.name, {})),
        }
        statistics = payload.get("statistics", {}) if payload else {}
        validations.append(
            {
                **base,
                "validation_status": ("passed" if payload["success"] else "failed")
                if payload
                else "no_result",
                "success": payload["success"] if payload else None,
                **{
                    key: statistics.get(key)
                    for key in (
                        "evaluated_expectations",
                        "successful_expectations",
                        "unsuccessful_expectations",
                        "success_percent",
                    )
                },
                "statistics_json": _json(statistics) if payload else None,
            }
        )
        for expectation_index, item in enumerate(payload.get("results", []) if payload else []):
            config = item.get("expectation_config") or {}
            kwargs = config.get("kwargs", {})
            meta = config.get("meta", {})
            metrics = item.get("result", {})
            exception = item.get("exception_info", {})
            expectations.append(
                {
                    **base,
                    "expectation_index": expectation_index,
                    "check_id": meta.get("check_id"),
                    "expectation_type": config.get("type"),
                    "column_name": kwargs.get("column"),
                    "column_a": kwargs.get("column_A"),
                    "column_b": kwargs.get("column_B"),
                    "success": item.get("success"),
                    **{
                        key: metrics.get(key)
                        for key in (
                            "element_count",
                            "missing_count",
                            "unexpected_count",
                            "unexpected_percent",
                        )
                    },
                    "raised_exception": exception.get("raised_exception", False),
                    "row_condition_json": _json(kwargs["row_condition"])
                    if "row_condition" in kwargs
                    else None,
                    "expectation_kwargs_json": _json(kwargs),
                    "expectation_meta_json": _json(meta),
                    "result_json": _json(metrics),
                    "exception_info_json": _json(exception),
                }
            )
    for name, rows, schema in (
        ("validations", validations, VALIDATION_RUN_RESULTS),
        ("expectations", expectations, EXPECTATION_RUN_RESULTS),
    ):
        path = directory / "analytics" / f"{name}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(
            pa.Table.from_pylist(rows, schema=schema.to_pyarrow()), path, compression="snappy"
        )


def run_validations_with_reports(
    context,
    definitions: Sequence[gx.ValidationDefinition],
    *,
    run_directory: str | Path,
    sources: Mapping[str, Mapping[str, object]],
    s3_uri: str | None = None,
    s3_client=None,
    batch_parameters: Mapping[str, Mapping[str, object]] | None = None,
    expectation_parameters: Mapping[str, Mapping[str, object]] | None = None,
    run_metadata: Mapping[str, object] | None = None,
    run_id: RunIdentifier | None = None,
    result_format: str | dict = "SUMMARY",
):
    """Execute a run and retain native HTML/JSON plus two Athena discovery datasets.

    Use a fresh, run-scoped GX context containing the registered definitions.
    sources requires source_tables (a list), source_query (the actual submitted
    comparison SQL) and source_query_dialect for every definition. These are caller
    facts, not inferred from a GX batch or parsed SQL. run_metadata holds explicit
    serializable temporal bindings, code/source pins, etc. DataFrame batch parameters
    and connection configuration are never serialized by this function.

    Native JSON is saved immediately per returned result. On an execution error,
    report earlier results and mark missing results 'no_result'; do not invent GX
    results for an exception. Build native Data Docs from the context and upload
    only an artifact allowlist. The manifest is uploaded last. Validation errors
    and publishing errors propagate; simultaneous errors form an ExceptionGroup.
    Ordinary failed expectations are retained and do not stop subsequent checks.

    Without s3_uri this performs the same local acceptance workflow without AWS.
    Every invocation gets a UUID artifact run_id, distinct from the caller's GX
    run_name label. UTC run_date partitions do not use high-cardinality run IDs.
    """
    definitions = tuple(definitions)
    _validate_targets(
        definitions,
        batch_parameters=batch_parameters,
        expectation_parameters=expectation_parameters,
    )
    if set(sources) != {definition.name for definition in definitions}:
        raise ValueError("sources must identify exactly the Validation Definitions in this run")
    for source in sources.values():
        if not isinstance(source.get("source_tables"), (list, tuple)) or not all(
            isinstance(table, str) and table for table in source["source_tables"]
        ):
            raise ValueError("source_tables must be an explicit list of table identifiers")
        for key in ("source_query", "source_query_dialect"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise ValueError(f"{key} must be supplied explicitly")
    if s3_uri is not None:
        _s3_location(s3_uri)
    run_metadata = dict(run_metadata or {})
    expectation_parameters = dict(expectation_parameters or {})
    _json(run_metadata)
    _json(expectation_parameters)
    identifier = run_id or RunIdentifier(run_time=datetime.now(UTC))
    timestamp = identifier.run_time.astimezone(UTC).replace(tzinfo=None)
    timestamp = timestamp.replace(microsecond=timestamp.microsecond // 1000 * 1000)
    artifact_id = uuid4().hex
    directory = Path(run_directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    docs_directory = directory / "data_docs"
    site_name = f"run_{artifact_id}"
    context.add_data_docs_site(
        site_name=site_name,
        site_config={
            "class_name": "SiteBuilder",
            "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
            "store_backend": {
                "class_name": "TupleFilesystemStoreBackend",
                "base_directory": str(docs_directory),
            },
        },
    )
    artifact_prefix = f"runs/{artifact_id}"

    def artifact_uri(relative):
        return (
            f"{s3_uri.rstrip('/')}/{artifact_prefix}/{relative}"
            if s3_uri
            else (directory / relative).as_uri()
        )

    for index, definition in enumerate(definitions):
        query_path = (
            directory / "queries" / f"{validation_artifact_stem(index, definition.name)}.sql"
        )
        query_path.parent.mkdir(parents=True, exist_ok=True)
        query_path.write_text(sources[definition.name]["source_query"], encoding="utf-8")
    error = None
    results = {}
    try:
        results = run_validations(
            definitions,
            suite_directory=directory / "suites",
            result_directory=directory / "results",
            batch_parameters=batch_parameters,
            expectation_parameters=expectation_parameters,
            run_id=identifier,
            result_format=result_format,
        )
    except Exception as validation_error:
        error = validation_error
    identity = {
        "report_schema_version": 1,
        "run_id": artifact_id,
        "run_name": identifier.run_name,
        "run_time_utc": timestamp,
        "run_status": "execution_error" if error else "completed",
        "gx_version": version("great-expectations"),
    }
    try:
        context.build_data_docs(site_names=[site_name])
        if not (docs_directory / "index.html").exists():
            raise RuntimeError("GX did not create the Data Docs index")
        _write_discovery_tables(
            definitions,
            sources,
            directory,
            identity,
            artifact_uri,
            run_metadata,
            expectation_parameters,
        )
        files = {
            path: f"{artifact_prefix}/{path.relative_to(directory).as_posix()}"
            for folder in ("results", "suites", "queries", "data_docs")
            for path in (directory / folder).rglob("*")
            if path.is_file()
        }
        partition = f"run_date={timestamp.date().isoformat()}"
        for name in ("validations", "expectations"):
            path = directory / "analytics" / f"{name}.parquet"
            files[path] = f"analytics/{name}/{partition}/{artifact_id}.parquet"
        manifest = directory / "manifest.json"
        manifest.write_text(
            _json(
                {
                    **identity,
                    "run_time_utc": timestamp.isoformat(),
                    "success": False
                    if error
                    else all(result.success for result in results.values()),
                    "execution_error": {"type": type(error).__name__, "message": str(error)}
                    if error
                    else None,
                    "validation_definitions": [definition.name for definition in definitions],
                    "run_metadata": run_metadata,
                    "artifacts": list(files.values()),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        files[manifest] = f"{artifact_prefix}/manifest.json"
        if s3_uri:
            publish_report_files(files, s3_uri=s3_uri, manifest_path=manifest, s3_client=s3_client)
    except Exception as reporting_error:
        if error:
            raise ExceptionGroup(
                "Validation and report publication both failed", [error, reporting_error]
            ) from None
        raise
    if error:
        raise error
    return results
