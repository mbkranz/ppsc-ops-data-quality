"""Run configured Athena comparisons. Invoke only with verified local bindings."""

import json
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

import great_expectations as gx
from great_expectations.core import RunIdentifier
from pydantic import BaseModel, ConfigDict
from sqlalchemy.engine import URL

from ppsc_ops_data_quality.account_to_survey_results.gx import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.account_to_survey_results.lineage import PROJECTION_LINEAGE
from ppsc_ops_data_quality.account_to_survey_results.metadata import (
    metadata_inputs,
    metadata_receipt,
)
from ppsc_ops_data_quality.account_to_survey_results.queries import (
    flow_account_query,
    rollup_account_query,
)
from ppsc_ops_data_quality.runtime import run_validations_with_reports
from ppsc_ops_data_quality.runtime.athena import prepare_validation, query_source_tables
from ppsc_ops_data_quality.runtime.preflight import check_catalog
from ppsc_ops_data_quality.sources.apmp import logical_schema, source_relation

from .configuration import ValidationConfiguration


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
    compiled_inputs = metadata_receipt()
    if (
        request.metadata.org != compiled_inputs["org"]
        or request.metadata.flow_version_id != compiled_inputs["flow_version_id"]
    ):
        raise ValueError("Configured metadata org/version does not match the compiled input set")
    athena = request.athena
    reporting = request.reports
    event = request.event
    inputs = metadata_inputs()
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
        "flow": flow_account_query(history, **event.model_dump()),
        "rollups": rollup_account_query(history, as_of=request.rollups.as_of),
    }
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
        query_options={
            "QueryExecutionContext": {"Catalog": athena.catalog_name, "Database": athena.database},
            "ResultConfiguration": {"OutputLocation": athena.s3_staging_dir},
            "WorkGroup": athena.work_group,
        },
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
    try:
        prepared = []
        for name, query in queries.items():
            suite = context.suites.add(
                flow_account_suite(expected_row_count=1)
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
                    projection_lineage=PROJECTION_LINEAGE,
                    table_versions=table_versions,
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
                    "source_tables": query_source_tables(
                        definition.data.data_asset.query, locations=request.locations
                    ),
                    "source_query": definition.data.data_asset.query,
                    "source_query_dialect": "athena",
                }
                for definition, _ in prepared
            },
            run_metadata={
                **(run_metadata or {}),
                "metadata_inputs": compiled_inputs,
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
        engine.close()
