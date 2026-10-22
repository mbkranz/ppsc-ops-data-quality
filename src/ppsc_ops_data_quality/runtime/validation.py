"""Run configured Athena comparisons. Invoke only with verified local bindings."""

import json
from pathlib import Path
from typing import Any

import great_expectations as gx
import ibis
from great_expectations.core import RunIdentifier
from pydantic import BaseModel, ConfigDict
from sqlalchemy.engine import URL

from ppsc_ops_data_quality.account_to_survey_results.gx import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.account_to_survey_results.lineage import PROJECTION_LINEAGE
from ppsc_ops_data_quality.account_to_survey_results.queries import (
    flow_account_query,
    rollup_account_query,
)
from ppsc_ops_data_quality.core.queries import history_tables
from ppsc_ops_data_quality.core.schemas import (
    ACCOUNT_HISTORY_VALIDATION_INPUT,
    CONTACT_HISTORY_VALIDATION_INPUT,
    SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
)
from ppsc_ops_data_quality.runtime import run_validations_with_reports
from ppsc_ops_data_quality.runtime.athena import prepare_validation

from .configuration import ValidationConfiguration


class ValidationOutcome(BaseModel):
    """Completed validations; execution/publication errors propagate separately."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    report_run_id: str
    report_manifest_uri: str
    success: bool
    validations: dict[str, dict[str, Any]]

    @property
    def exit_code(self) -> int:
        return 0 if self.success else 1


def run_validation(
    request: ValidationConfiguration,
    *,
    run_directory: Path,
    run_metadata: dict[str, Any] | None = None,
) -> ValidationOutcome:
    """Compose domain queries/suites, validate through Athena, and publish evidence.

    The caller supplies validated configuration and a fresh workspace. Both local
    and Glue hosts use this function; the runner retains native partial results.
    """
    athena = request.athena
    reporting = request.reports
    event = request.event
    overrides = request.schema_overrides
    history = history_tables(
        **request.databases.model_dump(),
        account_schema=ibis.schema(
            {**ACCOUNT_HISTORY_VALIDATION_INPUT.fields, **overrides.account}
        ),
        contact_schema=ibis.schema(
            {**CONTACT_HISTORY_VALIDATION_INPUT.fields, **overrides.contact}
        ),
        survey_result_schema=ibis.schema(
            {**SURVEY_RESULT_HISTORY_VALIDATION_INPUT.fields, **overrides.survey_result}
        ),
    )
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
                    "source_tables": [
                        f"{athena.catalog_name}.{database}.history"
                        for key, database in request.databases.model_dump().items()
                        if definition.name == "flow" or key != "contact_database"
                    ],
                    "source_query": definition.data.data_asset.query,
                    "source_query_dialect": "athena",
                }
                for definition, _ in prepared
            },
            run_metadata={
                **(run_metadata or {}),
                "event": event.model_dump(mode="json"),
                "rollups_as_of": request.rollups.as_of.isoformat(),
            },
            batch_parameters={definition.name: parameters for definition, parameters in prepared},
            run_id=RunIdentifier(run_name=run_directory.name),
        )
        manifest = json.loads((run_directory / "reports" / "manifest.json").read_text())
        return ValidationOutcome(
            report_run_id=manifest["run_id"],
            report_manifest_uri=(
                f"{reporting.s3_uri.rstrip('/')}/runs/{manifest['run_id']}/manifest.json"
            ),
            success=all(result.success for result in results.values()),
            validations={name: result.statistics for name, result in results.items()},
        )
    finally:
        engine.close()
