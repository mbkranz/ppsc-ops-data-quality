"""Account survey history workflow and its validated request/result boundaries."""

import json
import sys
from collections.abc import Callable
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Self
from uuid import uuid4

import great_expectations as gx
from great_expectations.core import RunIdentifier
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy.engine import URL

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    RelationLocation,
    check_native_columns,
    flow_account_query,
    logical_schema,
    metadata_inputs,
    metadata_receipt,
    projection_lineage,
    rollup_account_query,
    rollup_projection_lineage,
    source_relation,
    to_sqlglot,
)
from ppsc_ops_data_quality.account_to_survey_results.suites import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.io import load_yaml
from ppsc_ops_data_quality.runtime import (
    AthenaConfiguration,
    Configuration,
    DataVersionBinding,
    Name,
    ReportConfiguration,
    check_catalog,
    guard_query_size,
    prepare_query,
    prepare_validation,
    query_asset_sql,
    query_source_tables,
    run_validations_with_reports,
)
from ppsc_ops_data_quality.views import (
    ViewConfiguration,
    ViewRequest,
    create_query_view,
    create_view_sql,
    drop_query_view,
    extract_cte_view,
)


class EventConfiguration(Configuration):
    survey_result_id: Name
    account_before_at: date | datetime
    execution_at: date | datetime
    account_after_at: date | datetime
    eligibility: bool | None
    flow_run_date: date

    @model_validator(mode="after")
    def validate_temporal_order(self) -> Self:
        if isinstance(self.flow_run_date, datetime):
            raise ValueError("flow_run_date must be an org-local date")
        try:
            ordered = self.account_before_at < self.execution_at < self.account_after_at
        except TypeError as error:
            raise ValueError(
                "Temporal bindings must use comparable types and time zones"
            ) from error
        if not ordered:
            raise ValueError("Require account_before_at < execution_at < account_after_at")
        return self


class RollupConfiguration(Configuration):
    as_of: date | datetime


class MetadataSelection(Configuration):
    org: Name
    flow_version_id: Name


class ValidationConfiguration(Configuration):
    input_directory: str
    metadata: MetadataSelection
    athena: AthenaConfiguration
    reports: ReportConfiguration
    locations: dict[str, RelationLocation]
    data_versions: dict[str, DataVersionBinding]
    require_repeatable_reads: bool = True
    event: EventConfiguration
    rollups: RollupConfiguration
    flow_view: ViewConfiguration | None = None

    @model_validator(mode="after")
    def validate_selected_locations(self) -> Self:
        if not self.locations or set(self.locations) != set(self.data_versions):
            raise ValueError("Select exactly one location and data-version binding per dataset")
        identities = [location.identity for location in self.locations.values()]
        if len(set(identities)) != len(identities):
            raise ValueError("Selected dataset locations must be distinct")
        return self


def load_validation_configuration(path: Path) -> ValidationConfiguration:
    values = load_yaml(path)
    if "REPLACE_WITH_" in str(values):
        raise ValueError("Replace the example configuration bindings before connecting")
    return ValidationConfiguration.model_validate(values)


class ValidationOutcome(BaseModel):
    """Completed validations; execution/publication errors propagate separately."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_run_id: str
    report_manifest_uri: str
    success: bool
    validations: dict[str, dict[str, Any]]
    validation_mode: Literal["stable_inputs", "diagnostic"] = "stable_inputs"
    lake_acceptance: str = "unestablished"

    @property
    def exit_code(self) -> int:
        return 0 if self.success else 1


def run_validation(
    request: ValidationConfiguration,
    *,
    run_directory: Path,
    run_metadata: dict[str, Any] | None = None,
    athena_client: Any = None,
    athena_client_factory: Callable[[], Any] | None = None,
) -> ValidationOutcome:
    """Compose domain queries/suites, validate through Athena, and publish evidence.

    The caller supplies validated configuration and a fresh workspace. Both local
    and Glue hosts use this function; the runner retains native partial results.
    """
    inputs = metadata_inputs(Path(request.input_directory))
    compiled_inputs = metadata_receipt(inputs)
    if not compiled_inputs["native_definitions_available"] or compiled_inputs["provisional"]:
        raise ValueError(
            "Live validation requires selected native field captures and reviewed lake DDL; bundled profiles are offline only"
        )
    if (
        request.metadata.org != compiled_inputs["source_org"]
        or request.metadata.flow_version_id != compiled_inputs["flow_version_id"]
    ):
        raise ValueError("Configured metadata org/version does not match the compiled input set")
    check_native_columns(inputs)
    athena = request.athena
    reporting = request.reports
    event = request.event
    query_options = {
        "QueryExecutionContext": {"Catalog": athena.catalog_name, "Database": athena.database},
        "ResultConfiguration": {"OutputLocation": athena.s3_staging_dir},
        "WorkGroup": athena.work_group,
    }
    bindings = inputs["tables"]
    if set(request.locations) != set(bindings):
        raise ValueError("Configured locations do not match the selected APMP dataset set")
    for dataset_id, binding in bindings.items():
        schema = logical_schema(inputs, dataset_id)
        if (
            tuple(binding["history_boundaries"]) != ("valid_from", "valid_to")
            or binding["history_grain"] != "timestamp"
            or any(
                name not in schema or not schema[name].is_timestamp()
                for name in binding["history_boundaries"]
            )
        ):
            raise ValueError(
                f"Flow temporal resolution unestablished for {dataset_id}: {binding['history_grain']} history cannot establish arbitrary intra-day BEFORE/execution/AFTER states"
            )
    history = {
        binding["native_object"]: source_relation(
            inputs, dataset_id, location=request.locations[dataset_id]
        )
        for dataset_id, binding in bindings.items()
    }
    queries = {
        "flow": flow_account_query(history, inputs=inputs, **event.model_dump()),
        "rollups": to_sqlglot(
            rollup_account_query(history, as_of=request.rollups.as_of),
            projection_lineage=rollup_projection_lineage(),
        ),
    }
    for query in queries.values():
        query_source_tables(query.sql(dialect="athena"), locations=request.locations)
    connection_string = URL.create(
        "awsathena+rest",
        host=f"athena.{athena.region}.amazonaws.com",
        port=443,
        database=athena.database,
        query={
            "s3_staging_dir": athena.s3_staging_dir,
            "work_group": athena.work_group,
            "catalog_name": athena.catalog_name,
            **athena.connection_options,
        },
    ).render_as_string(hide_password=False)
    client = athena_client
    if client is None:
        if athena_client_factory is None:
            raise ValueError(
                "Supply an explicit Athena client or client factory for online preflight"
            )
        client = athena_client_factory()
    preflight = check_catalog(
        inputs,
        dataset_ids=tuple(bindings),
        locations=request.locations,
        data_versions=request.data_versions,
        athena_client=client,
        query_options=query_options,
        require_repeatable_reads=request.require_repeatable_reads,
    )
    table_versions = {
        (
            item.location.catalog,
            item.location.database,
            item.location.relation,
        ): item.data_version.snapshot_id
        for item in preflight
        if item.data_version.mode == "iceberg_snapshot"
    }
    repeatability_established = all(item.repeatability_established for item in preflight)
    validation_mode = "stable_inputs" if request.require_repeatable_reads else "diagnostic"
    lake_acceptance = (
        "unestablished"
        if compiled_inputs["provisional"]
        or not request.require_repeatable_reads
        or not repeatability_established
        else "catalog_compatible_semantics_require_review"
    )
    run_configuration_sha256 = sha256(request.model_dump_json().encode()).hexdigest()
    run_directory.mkdir(parents=True, exist_ok=False)
    context = gx.get_context(mode="file", project_root_dir=str(run_directory / "gx"))
    source = context.data_sources.add_sql(
        name="athena", connection_string=connection_string, create_temp_table=False
    )
    engine = source.get_execution_engine()
    listener, statement_sizes = guard_query_size(engine.engine)
    sources = {
        name: {
            "source_tables": query_source_tables(
                query.sql(dialect="athena"), locations=request.locations
            )
        }
        for name, query in queries.items()
    }
    locations = dict(request.locations)
    view_receipt = None
    view_request = None
    view_audit = {}

    def versions_for(query):
        tables = query_source_tables(query.sql(dialect="athena"), locations=locations)
        return {
            identity: value
            for identity, value in table_versions.items()
            if ".".join(identity) in tables
        }

    try:
        if request.flow_view is not None:
            settings = request.flow_view
            view_request = ViewRequest(
                location=RelationLocation(
                    catalog=athena.catalog_name,
                    database=settings.database,
                    relation=settings.prefix + "_" + uuid4().hex,
                ),
                timeout_seconds=settings.timeout_seconds,
            )
            expected, comparison = extract_cte_view(
                queries["flow"], cte_name="Expected_Account", location=view_request.location
            )
            expected = prepare_query(expected, table_versions=versions_for(expected))
            ddl = create_view_sql(expected, view_request)
            locations["flow_expected_view"] = view_request.location
            # Validate both statements before creating any catalog object.
            query_asset_sql(comparison, table_versions=versions_for(comparison))
            view_directory = run_directory / "views"
            view_directory.mkdir()
            (view_directory / "flow_expected.sql").write_text(ddl, encoding="utf-8")
            dependency = {
                "relation": view_request.location.identity,
                "definition_sql": ddl,
                "definition_sha256": sha256(ddl.encode()).hexdigest(),
                "outputs": {p.alias_or_name: p.meta.get("ppsc", {}) for p in expected.selects},
                "lineage": expected.meta.get("ppsc", {}),
            }
            (view_directory / "flow_expected.lineage.json").write_text(
                json.dumps(dependency, indent=2), encoding="utf-8"
            )
            try:
                view_receipt = create_query_view(
                    expected, view_request, athena_client=client, query_options=query_options
                )
            except Exception as creation_error:
                # No ownership receipt: never DROP an existing/ambiguously created view.
                view_audit.update(
                    location=view_request.location.model_dump(mode="json"),
                    creation="failed_or_unknown",
                    error=str(creation_error),
                )
                (view_directory / "receipt.json").write_text(json.dumps(view_audit, indent=2))
                raise
            view_audit.update(view_receipt.model_dump(mode="json"), cleanup="pending")
            (view_directory / "receipt.json").write_text(json.dumps(view_audit, indent=2))
            sources["flow"]["query_dependencies"] = [dependency]
            queries["flow"] = comparison
        prepared = []
        for name, query in queries.items():
            suite = context.suites.add(
                flow_account_suite(
                    expected_row_count=1,
                    provenance=compiled_inputs,
                    lineage=projection_lineage(query),
                )
                if name == "flow"
                else rollup_account_suite()
            )
            prepared.append(
                prepare_validation(
                    context,
                    source,
                    query,
                    suite,
                    name=name,
                    metadata={"run_name": run_directory.name},
                    projection_lineage=projection_lineage(query),
                    table_versions=versions_for(query),
                    sql_path=run_directory / "sql" / f"{name}.sql",
                )
            )
        results = run_validations_with_reports(
            context,
            [definition for definition, _ in prepared],
            run_directory=run_directory / "reports",
            s3_uri=reporting.s3_uri,
            sources={
                definition.name: {
                    **sources[definition.name],
                    "source_query": definition.data.data_asset.query,
                    "source_query_dialect": "athena",
                }
                for definition, _ in prepared
            },
            run_metadata={
                **(run_metadata or {}),
                "metadata_inputs": compiled_inputs,
                "submitted_statement_utf8_bytes": statement_sizes,
                "query_view": view_audit,
                "provenance_version": "native-salesforce",
                "configuration_sha256": run_configuration_sha256,
                "catalog_preflight": [item.model_dump(mode="json") for item in preflight],
                "repeatability_established": repeatability_established,
                "validation_mode": validation_mode,
                "stable_input_assertions": "unestablished"
                if not repeatability_established
                else "repeatability_established_semantics_require_review",
                "lake_acceptance": lake_acceptance,
                "event": event.model_dump(mode="json"),
                "rollups_as_of": request.rollups.as_of.isoformat(),
            },
            batch_parameters={definition.name: parameters for definition, parameters in prepared},
            result_format={
                "result_format": "SUMMARY",
                "unexpected_index_column_names": ["validation_record_id"],
            },
            run_id=RunIdentifier(run_name=run_directory.name),
        )
        manifest = json.loads((run_directory / "reports" / "manifest.json").read_text())
        return ValidationOutcome(
            report_run_id=manifest["run_id"],
            report_manifest_uri=(
                f"{reporting.s3_uri.rstrip('/')}/runs/{manifest['run_id']}/manifest.json"
            ),
            success=all(result.success for result in results.values()),
            validation_mode=validation_mode,
            lake_acceptance=lake_acceptance,
            validations={name: result.statistics for name, result in results.items()},
        )
    finally:
        from sqlalchemy import event as sqlalchemy_event

        active_error = sys.exception()
        try:
            if view_receipt is not None:
                try:
                    query_id = drop_query_view(
                        view_receipt,
                        athena_client=client,
                        query_options=query_options,
                        timeout_seconds=view_request.timeout_seconds,
                    )
                    view_audit.update(cleanup="dropped", cleanup_query_id=query_id)
                except Exception as cleanup_error:
                    view_audit.update(cleanup="failed", cleanup_error=str(cleanup_error))
                    if active_error is not None:
                        raise ExceptionGroup(
                            "Validation and query-view cleanup failed",
                            [active_error, cleanup_error],
                        ) from None
                    raise
                finally:
                    (run_directory / "views" / "receipt.json").write_text(
                        json.dumps(view_audit, indent=2), encoding="utf-8"
                    )
        finally:
            sqlalchemy_event.remove(engine.engine, "before_cursor_execute", listener)
            engine.close()


def prepare_authored_validation(
    context,
    source,
    suite,
    *,
    sql_path: Path,
    contract_path: Path,
    values: dict,
    output_path: Path,
    table_versions=None,
):
    """Explicit file execution path with a caller-built native suite and scalar values."""
    from .queries import SqlContract, bind_authored_select

    contract = SqlContract.model_validate(load_yaml(contract_path))
    query = bind_authored_select(
        sql_path.read_text(), contract, values=values, suite_name=suite.name
    )
    query.meta["ppsc"]["sidecar_sha256"] = sha256(contract_path.read_bytes()).hexdigest()
    return prepare_validation(
        context,
        source,
        query,
        suite,
        name=contract.definition_id,
        projection_lineage=projection_lineage(query),
        table_versions=table_versions,
        sql_path=output_path,
    )
