"""Explicit runtime operations."""

from __future__ import annotations

import gzip
import hashlib
import json
import mimetypes
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from time import monotonic, sleep
from typing import Annotated, Any, Literal, Self
from urllib.parse import urlsplit
from uuid import uuid4

import great_expectations as gx
import ibis
import pyarrow as pa
import pyarrow.parquet as pq
import sqlglot
from great_expectations.core import ExpectationSuiteValidationResult, RunIdentifier
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope

from ppsc_ops_data_quality.io import RelationLocation

Name = Annotated[str, Field(min_length=1)]


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def s3_location(uri: str) -> tuple[str, str]:
    """Return bucket/key for an explicit S3 location, rejecting URL modifiers."""
    location = urlsplit(uri)
    if (
        location.scheme != "s3"
        or not location.netloc
        or not location.path.strip("/")
        or location.query
        or location.fragment
        or ".." in location.path.split("/")
    ):
        raise ValueError("Expected an explicit S3 bucket and key/prefix")
    return location.netloc, location.path.lstrip("/")


class AthenaConfiguration(Configuration):
    region: Name
    database: Name
    s3_staging_dir: Name
    work_group: Name
    catalog_name: Name = "AwsDataCatalog"
    connection_options: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_connection(self) -> Self:
        s3_location(self.s3_staging_dir)
        reserved = {"s3_staging_dir", "work_group", "catalog_name"}
        if reserved.intersection(self.connection_options):
            raise ValueError("Connection options must not override declared Athena settings")
        return self


class ReportConfiguration(Configuration):
    s3_uri: Name

    @model_validator(mode="after")
    def validate_destination(self) -> Self:
        s3_location(self.s3_uri)
        return self


def validation_artifact_stem(index: int, name: str) -> str:
    """Use the sequence to disambiguate names that sanitize to the same label."""
    label = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")[:100]
    return f"{index:03d}_{label or 'validation'}"


def save_result(result: ExpectationSuiteValidationResult, path: str | Path) -> Path:
    """Archive native GX JSON as one UTF-8 JSON line in a gzip file.

    The decoded object is exactly result.to_json_dict(); no envelope or field
    normalization is added. This is an audit copy, not a GX ValidationResultsStore.
    Refuse overwrite. Compression has a deterministic header for reproducibility.
    """
    payload = (
        json.dumps(
            result.to_json_dict(), ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
        + "\n"
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as output:
        output.write(gzip.compress(payload.encode("utf-8"), mtime=0))
    return destination


def save_suite(suite: gx.ExpectationSuite, path: str | Path) -> Path:
    """Write native GX suite JSON, preserving expectations, IDs and metadata.

    Provenance: ExpectationSuite.to_json_dict(). The input is the registered suite
    attached to the Validation Definition, after builder arguments such as source
    row counts have been applied. This does not rebuild the suite or mutate it.
    GX $PARAMETER placeholders remain symbolic; record their runtime values in
    the run metadata separately. No dataframe or connection configuration is saved.

    Existing files are rejected so another run's audit snapshot is not replaced.
    Serialization and I/O errors propagate before that definition is evaluated.
    Reload with gx.ExpectationSuite(**json.loads(path.read_text())).
    """
    payload = json.dumps(suite.to_json_dict(), indent=2, ensure_ascii=False, allow_nan=False)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as output:
        output.write(payload + "\n")
    return destination


REPORT_IDENTITY = {
    "report_schema_version": "int32",
    "run_id": "string",
    "run_name": "string",
    "run_time_utc": "timestamp(3)",
    "run_status": "string",
    "gx_version": "string",
    "validation_definition_name": "string",
    "validation_definition_id": "string",
    "suite_name": "string",
    "data_source_name": "string",
    "data_asset_name": "string",
    "source_tables": "array<string>",
    "source_query_dialect": "string",
    "source_query": "string",
    "source_query_sha256": "string",
    "source_query_uri": "string",
    "raw_result_uri": "string",
    "data_docs_uri": "string",
    "run_metadata_json": "string",
    "expectation_parameters_json": "string",
}


VALIDATION_RUN_RESULTS = ibis.schema(
    {
        **REPORT_IDENTITY,
        "validation_status": "string",
        "success": "boolean",
        "evaluated_expectations": "int64",
        "successful_expectations": "int64",
        "unsuccessful_expectations": "int64",
        "success_percent": "float64",
        "statistics_json": "string",
    }
)


EXPECTATION_RUN_RESULTS = ibis.schema(
    {
        **REPORT_IDENTITY,
        "expectation_index": "int64",
        "check_id": "string",
        "expectation_type": "string",
        "column_name": "string",
        "column_a": "string",
        "column_b": "string",
        "success": "boolean",
        "element_count": "int64",
        "missing_count": "int64",
        "unexpected_count": "int64",
        "unexpected_percent": "float64",
        "raised_exception": "boolean",
        "row_condition_json": "string",
        "expectation_kwargs_json": "string",
        "expectation_meta_json": "string",
        "result_json": "string",
        "exception_info_json": "string",
    }
)


def _validate_targets(definitions, **parameters):
    names = [definition.name for definition in definitions]
    if len(names) != len(set(names)):
        raise ValueError("Validation Definition names must be unique within a run")
    for label, mapping in parameters.items():
        unknown = set(mapping or {}) - set(names)
        if unknown:
            raise ValueError(f"{label} references unknown definitions: {sorted(unknown)}")


def run_validations(
    definitions: Sequence[gx.ValidationDefinition],
    *,
    suite_directory: str | Path,
    result_directory: str | Path | None = None,
    batch_parameters: Mapping[str, Mapping[str, object]] | None = None,
    expectation_parameters: Mapping[str, Mapping[str, object]] | None = None,
    run_id: RunIdentifier | None = None,
    result_format: str | dict = "SUMMARY",
) -> dict[str, ExpectationSuiteValidationResult]:
    """Run definitions sequentially and return native results keyed by name.

    Provenance: GX ValidationDefinition.run(). Parameters are keyed by definition
    name so separate DataFrame validations never receive another definition's
    data. A shared RunIdentifier groups the invocation. Immediately before each
    run, serialize definition.suite to the explicit run-scoped suite_directory.
    Filenames include sequence and a readable sanitized definition name. Existing
    snapshots are never overwritten. GX stores results through the Context.
    When result_directory is supplied, also archive each returned native result
    immediately as gzip JSON, including failed expectations. Completed earlier
    results survive a later execution error. Execution errors have no native result.
    The runner needs no Ibis expression or engine API.

    An expectation failure is a returned unsuccessful result and does not stop
    later definitions. Execution/configuration errors propagate immediately;
    earlier results can already be stored by GX. Duplicate names and unknown
    parameter targets are rejected before any validation runs. An empty sequence
    returns an empty result mapping. No implicit retries, Checkpoint actions or
    boolean-to-process-exit conversion are performed. Use a native Checkpoint
    directly if all definitions share compatible parameters and require actions.
    """
    definitions = tuple(definitions)
    _validate_targets(
        definitions,
        batch_parameters=batch_parameters,
        expectation_parameters=expectation_parameters,
    )
    if run_id is None:
        run_id = RunIdentifier(run_time=datetime.now(UTC))
    results = {}
    for index, definition in enumerate(definitions):
        stem = validation_artifact_stem(index, definition.name)
        suite_path = Path(suite_directory) / f"{stem}.suite.json"
        save_suite(definition.suite, suite_path)
        results[definition.name] = definition.run(
            batch_parameters=dict((batch_parameters or {}).get(definition.name, {})),
            expectation_parameters=dict((expectation_parameters or {}).get(definition.name, {})),
            run_id=run_id,
            result_format=result_format,
        )
        if result_directory is not None:
            save_result(results[definition.name], Path(result_directory) / f"{stem}.json.gz")
    return results


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


class DataVersionBinding(BaseModel):
    """A selected snapshot is applied to SQL, not merely recorded in a receipt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["mutable", "iceberg_snapshot"] = "mutable"
    snapshot_id: str | None = Field(default=None, pattern=r"^[1-9][0-9]*$")

    @model_validator(mode="after")
    def validate_snapshot(self):
        if (self.mode == "iceberg_snapshot") != (self.snapshot_id is not None):
            raise ValueError("Select a positive snapshot_id exactly for iceberg_snapshot mode")
        return self


class RelationPreflight(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_id: str
    location: RelationLocation
    compatible: bool
    checked_at: datetime
    catalog_sha256: str
    additional_columns: tuple[str, ...]
    data_version: DataVersionBinding
    source_sql: str
    schema_query_execution_id: str | None = None
    repeatability_established: bool
    limitations: tuple[str, ...]


def _column_type(column: dict[str, Any]) -> str:
    declared = column["Type"]
    if declared.casefold() == "decimal":
        precision = column.get("Precision")
        scale = column.get("Scale", 0)
        if (
            not isinstance(precision, int)
            or not isinstance(scale, int)
            or not 1 <= precision <= 38
            or not 0 <= scale <= precision
        ):
            raise ValueError(f"Exact decimal precision/scale unavailable for {column['Name']}")
        return f"decimal({precision},{scale})"
    return declared


def _catalog_schema(columns: list[dict[str, Any]], *, fields: tuple[str, ...] | None = None):
    if fields is not None:
        columns = [column for column in columns if column["Name"] in fields]
    schema = exp.Schema(
        expressions=[
            exp.ColumnDef(
                this=exp.to_identifier(column["Name"], quoted=True),
                kind=exp.DataType.build(_column_type(column), dialect="athena"),
            )
            for column in columns
        ]
    )
    return ibis.Schema.from_sqlglot(schema, dialect="athena")


def _qualified_table(location: RelationLocation) -> exp.Table:
    return exp.Table(
        this=exp.to_identifier(location.relation, quoted=True),
        db=exp.to_identifier(location.database, quoted=True),
        catalog=exp.to_identifier(location.catalog, quoted=True),
    )


def snapshot_sql(location: RelationLocation, columns: tuple[str, ...], snapshot_id: str) -> str:
    """Use SQLGlot's native Athena version node for a bounded schema probe."""
    table = _qualified_table(location)
    table.set(
        "version",
        exp.Version(this="VERSION", expression=exp.Literal.number(snapshot_id), kind="AS OF"),
    )
    return (
        exp.select(*(exp.column(column, quoted=True) for column in columns))
        .from_(table)
        .limit(0)
        .sql(dialect="athena")
    )


def _query_schema(athena_client: Any, sql: str, *, query_options: dict, timeout_seconds: float):
    execution = athena_client.start_query_execution(QueryString=sql, **query_options)[
        "QueryExecutionId"
    ]
    deadline = monotonic() + timeout_seconds
    while True:
        state = athena_client.get_query_execution(QueryExecutionId=execution)["QueryExecution"][
            "Status"
        ]
        if state["State"] == "SUCCEEDED":
            break
        if state["State"] in {"FAILED", "CANCELLED"}:
            raise ValueError(
                f"Snapshot schema preflight failed: {state.get('StateChangeReason', state['State'])}"
            )
        if monotonic() >= deadline:
            athena_client.stop_query_execution(QueryExecutionId=execution)
            raise TimeoutError("Snapshot schema preflight exceeded its bounded timeout")
        sleep(0.25)
    response = athena_client.get_query_results(QueryExecutionId=execution, MaxResults=1)
    columns = response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
    return _catalog_schema(columns), execution


def check_catalog(
    inputs: dict,
    *,
    dataset_ids: tuple[str, ...],
    locations: dict[str, RelationLocation],
    data_versions: dict[str, DataVersionBinding],
    athena_client: Any,
    query_options: dict,
    require_repeatable_reads: bool = True,
    timeout_seconds: float = 45,
) -> tuple[RelationPreflight, ...]:
    """Block drift before validation queries; never claim saved hashes certify live tables.

    The supplied client performs the online operation. Snapshot schema probes use
    the exact selected ID later applied by the shared query renderer. Separate
    table snapshots do not establish business-time or cross-table atomicity.
    """
    if not dataset_ids or len(set(dataset_ids)) != len(dataset_ids):
        raise ValueError("Select nonempty unique dataset IDs for catalog preflight")
    if set(locations) != set(dataset_ids) or set(data_versions) != set(dataset_ids):
        raise ValueError("Each selected dataset requires one location and data-version binding")
    results = []
    for dataset_id in dataset_ids:
        binding = inputs["tables"][dataset_id]
        location = locations[dataset_id]
        version = data_versions[dataset_id]
        expected = ibis.schema(binding["fields"])
        try:
            response = athena_client.get_table_metadata(
                CatalogName=location.catalog,
                DatabaseName=location.database,
                TableName=location.relation,
            )
        except Exception as error:
            raise ValueError(
                f"Catalog compatibility unestablished for {location.identity}: {type(error).__name__}"
            ) from error
        observed = response.get("TableMetadata")
        if not isinstance(observed, dict):
            raise ValueError(f"Catalog metadata unavailable for {location.identity}")
        if observed.get("Name") != location.relation:
            raise ValueError(f"Catalog identity changed for {location.identity}")
        if observed.get("TableType", "").upper() not in {
            "EXTERNAL_TABLE",
            "MANAGED_TABLE",
            "VIRTUAL_VIEW",
        }:
            raise ValueError(f"Catalog relation kind unavailable for {location.identity}")
        kind = "view" if observed["TableType"].upper() == "VIRTUAL_VIEW" else "table"
        if kind != binding["kind"]:
            raise ValueError(f"Catalog relation kind changed for {location.identity}")
        if kind == "view":
            # GetTableMetadata does not establish the deployed SQL/dependencies.
            # A matching column list alone cannot certify a changed view.
            raise ValueError(
                f"View definition/dependencies remain unverified for {location.identity}; capture and verify deployed view evidence"
            )
        partitions = tuple(column["Name"] for column in observed.get("PartitionKeys", []))
        if partitions != tuple(binding["partition_columns"]):
            raise ValueError(f"Catalog partition declarations changed for {location.identity}")
        # Permit the same exact partition declaration exposed in both API lists,
        # but never accept name collisions as harmless unreferenced additions.
        unique = {}
        casefolded = {}
        for declarations in (observed.get("Columns", []), observed.get("PartitionKeys", [])):
            group_names = set()
            for column in declarations:
                name = column["Name"]
                folded = name.casefold()
                if folded in casefolded and casefolded[folded] != name:
                    raise ValueError(
                        f"Catalog case-colliding column names changed for {location.identity}: {casefolded[folded]}, {name}"
                    )
                if name in group_names:
                    raise ValueError(f"Duplicate catalog column declaration: {name}")
                if name in unique and _column_type(unique[name]) != _column_type(column):
                    raise ValueError(f"Conflicting catalog declarations for {name}")
                group_names.add(name)
                casefolded[folded] = name
                unique[name] = column
        missing_names = set(expected.names).difference(unique)
        if missing_names:
            raise ValueError(
                f"Catalog schema changed for {location.identity}: missing={sorted(missing_names)}"
            )
        catalog_schema = _catalog_schema(list(unique.values()), fields=expected.names)
        missing = set(expected.names).difference(catalog_schema.names)
        changed = [
            name
            for name in expected.names
            if name in catalog_schema and expected[name] != catalog_schema[name]
        ]
        if missing or changed:
            raise ValueError(
                f"Catalog schema changed for {location.identity}: missing={sorted(missing)}, changed={changed}"
            )
        source_sql = (
            exp.select(*(exp.column(name, quoted=True) for name in expected.names))
            .from_(_qualified_table(location))
            .sql(dialect="athena")
        )
        query_id = None
        limitations = []
        repeatable = False
        if version.mode == "iceberg_snapshot":
            if str(observed.get("Parameters", {}).get("table_type", "")).upper() != "ICEBERG":
                raise ValueError(
                    f"Snapshot binding requires an observed Iceberg table: {location.identity}"
                )
            source_sql = snapshot_sql(location, expected.names, version.snapshot_id)
            historical_schema, query_id = _query_schema(
                athena_client,
                source_sql,
                query_options=query_options,
                timeout_seconds=timeout_seconds,
            )
            if historical_schema != expected:
                raise ValueError(
                    f"Selected Iceberg historical schema differs from saved definition: {location.identity}"
                )
            repeatable = True
            limitations.append(
                "Separate table snapshots establish no cross-table transaction or business-time alignment"
            )
        else:
            limitations.append(
                "Mutable input: observation window cannot guarantee repeatable reads across GX metric queries"
            )
            if require_repeatable_reads:
                raise ValueError(
                    f"Stable-input assertion unestablished for mutable relation {location.identity}; select an Iceberg snapshot or run explicitly diagnostic comparisons"
                )
        if binding["provisional"] or any(
            table["provisional"] for table in inputs["tables"].values()
        ):
            limitations.append(
                "Provisional source/mapping evidence; live semantic acceptance remains outstanding"
            )
        results.append(
            RelationPreflight(
                dataset_id=dataset_id,
                location=location,
                compatible=True,
                checked_at=datetime.now(UTC),
                catalog_sha256=sha256(
                    json.dumps(observed, sort_keys=True, default=str).encode()
                ).hexdigest(),
                additional_columns=tuple(name for name in unique if name not in expected.names),
                data_version=version,
                source_sql=source_sql,
                schema_query_execution_id=query_id,
                repeatability_established=repeatable,
                limitations=tuple(limitations),
            )
        )
    return tuple(results)


def query_asset_sql(
    comparison: exp.Select,
    *,
    projection_lineage: Mapping[str, Mapping[str, object]] | None = None,
    table_versions: Mapping[tuple[str, str, str], str] | None = None,
) -> str:
    """Return one Athena SELECT, with lineage comments and no terminal semicolon.

    Compose Ibis first. to_sqlglot() resolves and annotates the final projections.
    Shared CTEs remain inside a named input relation with an explicit SELECT list.
    No SQL string substitution is performed.
    The SQL text carries comments; structured meta remains in the annotated AST
    and canonical lineage mapping rather than being serialized into SQL.
    """
    query = prepare_query(
        comparison, projection_lineage=projection_lineage, table_versions=table_versions
    )
    sql = query.sql(dialect="athena", pretty=False, comments=False)
    # https://docs.aws.amazon.com/athena/latest/ug/service-limits.html
    if len(sql.encode("utf-8")) > 262_144:
        raise ValueError("Comparison SQL exceeds Athena's 262144-byte query limit")
    return sql


def query_batch_definition(
    data_source,
    comparison: exp.Select,
    *,
    name: str,
    metadata: Mapping[str, object] | None = None,
    projection_lineage: Mapping[str, Mapping[str, object]] | None = None,
    table_versions: Mapping[tuple[str, str, str], str] | None = None,
):
    """Register a native Query Asset and return its whole-query Batch Definition.

    data_source is an existing GX SQL Data Source using the Athena SQLAlchemy
    connection. Use a run-scoped ephemeral Context or a unique asset name for
    distinct SQL bindings; existing assets are never silently overwritten.
    Metadata records run facts; it does not bind SQL parameters or filter rows.

    The caller explicitly retrieves/validates the batch. No custom expectations,
    temporary tables, view DDL, context creation or checkpoint setup is performed.
    A whole-query batch does not guarantee one SQL execution for all expectations.
    """
    asset = data_source.add_query_asset(
        name=name,
        query=query_asset_sql(
            comparison, projection_lineage=projection_lineage, table_versions=table_versions
        ),
        batch_metadata=dict(metadata or {}),
    )
    return asset.add_batch_definition_whole_table(name="whole_comparison")


def query_source_tables(query_sql: str, *, locations: Mapping[str, RelationLocation]) -> list[str]:
    """Report only selected physical sources actually read by the submitted query."""
    selected = {
        (location.catalog, location.database, location.relation): location.identity
        for location in locations.values()
    }
    used = set()
    for scope in traverse_scope(sqlglot.parse_one(query_sql, read="athena")):
        for node, source in scope.selected_sources.values():
            if not isinstance(node, exp.Table) or isinstance(source, Scope):
                continue  # CTEs and derived aliases are not physical data sources.
            identity = (node.catalog, node.db, node.name)
            if identity not in selected:
                raise ValueError(
                    f"Validation query references an unselected physical relation: {node.sql(dialect='athena')}"
                )
            used.add(identity)
    return [identity for key, identity in selected.items() if key in used]


def prepare_validation(
    context,
    data_source,
    comparison: exp.Select,
    suite: gx.ExpectationSuite,
    *,
    name: str,
    metadata: Mapping[str, object] | None = None,
    projection_lineage: Mapping[str, Mapping[str, object]] | None = None,
    table_versions: Mapping[tuple[str, str, str], str] | None = None,
    sql_path: str | Path | None = None,
) -> tuple[gx.ValidationDefinition, dict]:
    """Return (ValidationDefinition, batch parameters) for one Athena comparison.

    Provenance: GX 1.24 QueryAsset -> whole-query BatchDefinition ->
    ValidationDefinition. query_batch_definition() performs Ibis compilation
    and SQLGlot lineage attachment. No SQL files are read for execution.

    Supply an existing SQL Data Source and a suite registered in the same Context.
    The SQL Data Source must use the configured Athena SQLAlchemy connection;
    credentials, schema bindings, temporal parameters and source pins belong to
    the caller. Unique run-scoped names prevent conflicting asset replacement.

    sql_path optionally saves the exact SELECT assigned to the Query Asset for
    audit/review. GX's actual metric queries may wrap that SELECT. No batch is
    fetched here, no views are created and Context configuration is not invented.
    The caller owns the Context, connection and result-store lifecycle.
    """
    batch_definition = query_batch_definition(
        data_source,
        comparison,
        name=name,
        metadata=metadata,
        projection_lineage=projection_lineage,
        table_versions=table_versions,
    )
    if sql_path is not None:
        path = Path(sql_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(batch_definition.data_asset.query, encoding="utf-8")
        path.with_suffix(".lineage.json").write_text(
            json.dumps(
                {
                    "ppsc": comparison.meta.get("ppsc", {}),
                    "query_sha256": sha256(batch_definition.data_asset.query.encode()).hexdigest(),
                    "table_versions": [
                        {"relation": list(k), "snapshot_id": v}
                        for k, v in (table_versions or {}).items()
                    ],
                    "outputs": {
                        p.alias_or_name: p.meta.get("ppsc", {}) for p in comparison.selects
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    definition = context.validation_definitions.add(
        gx.ValidationDefinition(name=name, data=batch_definition, suite=suite)
    )
    return definition, {}


def _select_first(query: exp.Query) -> exp.Query:
    """Retain shared CTEs inside one explicit SELECT-first GX input relation."""
    with_clause = query.args.get("with_")
    if with_clause is None:
        return query
    if with_clause.args.get("recursive"):
        raise ValueError("Recursive CTEs cannot be rendered as a SELECT-first Query Asset")
    scopes = list(traverse_scope(query))
    physical_names = {
        node.name.casefold()
        for scope in scopes
        for node, source in scope.selected_sources.values()
        if isinstance(node, exp.Table) and not isinstance(source, Scope)
    }
    reserved = physical_names | {cte.alias_or_name.casefold() for cte in with_clause.expressions}
    renamed = {}
    for cte in with_clause.expressions:
        if cte.alias_or_name.casefold() not in physical_names:
            continue
        candidate = cte.alias_or_name + "_Input"
        while candidate.casefold() in reserved:
            candidate += "_2"
        reserved.add(candidate.casefold())
        renamed[id(cte.this)] = candidate
        cte.set("alias", exp.TableAlias(this=exp.to_identifier(candidate, quoted=True)))
    # Rename only references resolved to that CTE, preserving physical tables
    # with the same spelling and all existing column/table aliases.
    for scope in scopes:
        for alias, (node, source) in scope.selected_sources.items():
            if (
                isinstance(node, exp.Table)
                and isinstance(source, Scope)
                and id(source.expression) in renamed
            ):
                if not node.alias:
                    node.set("alias", exp.TableAlias(this=exp.to_identifier(alias, quoted=True)))
                node.set("this", exp.to_identifier(renamed[id(source.expression)], quoted=True))
    return exp.select(
        *[
            exp.column(projection.alias_or_name, table="Comparison_Rows", quoted=True)
            for projection in query.selects
        ]
    ).from_(query.subquery("Comparison_Rows"))


def prepare_query(
    comparison: exp.Select, *, projection_lineage=None, table_versions=None, locations=None
) -> exp.Select:
    """Validate native SELECT outputs, physical reads and version bindings by SQL scope."""
    if not isinstance(comparison, exp.Select):
        raise TypeError("Runtime requires a final SQLGlot SELECT")
    query = comparison.copy()
    names = [p.alias_or_name for p in query.selects]
    if (
        not names
        or any(not n for n in names)
        or len(set(n.casefold() for n in names)) != len(names)
    ):
        raise ValueError("Comparison requires explicit unique output aliases")
    if any(p.is_star for p in query.selects) or any(
        w.args.get("recursive") for w in query.find_all(exp.With)
    ):
        raise ValueError("Wildcard outputs and recursive CTEs are unsupported")
    if locations is not None:
        query_source_tables(query.sql(dialect="athena"), locations=locations)
    used_versions = set()
    for scope in traverse_scope(query):
        for node, source in scope.selected_sources.values():
            if not isinstance(node, exp.Table) or isinstance(source, Scope):
                continue
            identity = (node.catalog, node.db, node.name)
            snapshot = (table_versions or {}).get(identity)
            existing = node.args.get("version")
            if snapshot is not None:
                if not re.fullmatch(r"[1-9][0-9]*", snapshot):
                    raise ValueError("Iceberg snapshot IDs must be positive decimal integers")
                desired = exp.Version(
                    this="VERSION", expression=exp.Literal.number(snapshot), kind="AS OF"
                )
                if existing is not None and existing != desired:
                    raise ValueError("Conflicting physical snapshot versions")
                node.set("version", desired)
                used_versions.add(identity)
            elif existing is not None:
                raise ValueError("Undeclared physical snapshot version")
    if set(table_versions or {}) - used_versions:
        raise ValueError("Snapshot binding names an unread physical relation")
    evidence = dict(query.meta.get("ppsc", {}))
    original_lineage = {p.alias_or_name: p.meta.get("ppsc") for p in query.selects}
    query = _select_first(query)
    query.meta["ppsc"] = evidence
    for projection in query.selects:
        metadata = (projection_lineage or original_lineage).get(projection.alias_or_name)
        if metadata is not None:
            projection.meta["ppsc"] = metadata
    return query


def guard_query_size(engine, *, max_bytes: int = 262_144):
    """Measure every SQLAlchemy-submitted GX statement and reject excess before execution.

    Return the listener and a mutable list of sizes for explicit run evidence.
    The caller removes the listener when closing its engine.
    """
    from sqlalchemy import event

    sizes = []

    def check(connection, cursor, statement, parameters, context, executemany):
        size = len(statement.encode("utf-8"))
        sizes.append(size)
        if size > max_bytes:
            raise ValueError(f"GX statement exceeds Athena {max_bytes}-byte limit: {size}")

    event.listen(engine, "before_cursor_execute", check)
    return check, sizes
