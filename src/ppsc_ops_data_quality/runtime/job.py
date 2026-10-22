"""Run configured Athena comparisons. Invoke only with verified local bindings."""

import json
import tomllib
from pathlib import Path

import great_expectations as gx
import ibis
from great_expectations.core import RunIdentifier
from sqlalchemy.engine import URL

from ppsc_ops_data_quality.account_to_survey_results_expectations import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.queries import flow_account_query, rollup_account_query
from ppsc_ops_data_quality.runtime import run_validations_with_reports
from ppsc_ops_data_quality.runtime.athena import prepare_validation
from ppsc_ops_data_quality.schemas import (
    ACCOUNT_HISTORY_VALIDATION_INPUT,
    CONTACT_HISTORY_VALIDATION_INPUT,
    SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
    history_tables,
)


def validate_athena(config_path: Path, run_directory: Path, *, run_metadata=None):
    """Run both suite builders through Athena and publish reports.

    Local CLI and Glue share this implementation. Failed expectations return 1;
    execution and publication errors propagate to the hosting entry point.
    """
    text = config_path.read_text()
    if "REPLACE_WITH_" in text:
        raise ValueError("Replace the example configuration bindings before connecting")
    config = tomllib.loads(text)
    athena = config["athena"]
    reporting = config["reports"]
    event = config["event"]
    overrides = config.get("schema_overrides", {})
    history = history_tables(
        **config["databases"],
        account_schema=ibis.schema(
            {**ACCOUNT_HISTORY_VALIDATION_INPUT.fields, **overrides.get("account", {})}
        ),
        contact_schema=ibis.schema(
            {**CONTACT_HISTORY_VALIDATION_INPUT.fields, **overrides.get("contact", {})}
        ),
        survey_result_schema=ibis.schema(
            {**SURVEY_RESULT_HISTORY_VALIDATION_INPUT.fields, **overrides.get("survey_result", {})}
        ),
    )
    queries = {
        "flow": flow_account_query(history, **event),
        "rollups": rollup_account_query(history, as_of=config["rollups"]["as_of"]),
    }
    connection_string = URL.create(
        "awsathena+rest",
        host=f"athena.{athena['region']}.amazonaws.com",
        port=443,
        database=athena["database"],
        query={
            "s3_staging_dir": athena["s3_staging_dir"],
            "work_group": athena["work_group"],
            "catalog_name": athena["catalog_name"],
            **athena.get("connection_options", {}),
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
                    sql_path=run_directory / "sql" / f"{name}.sql",
                )
            )
        results = run_validations_with_reports(
            context,
            [definition for definition, _ in prepared],
            run_directory=run_directory / "reports",
            s3_uri=reporting["s3_uri"],
            sources={
                definition.name: {
                    "source_tables": [
                        f"{athena['catalog_name']}.{database}.history"
                        for key, database in config["databases"].items()
                        if definition.name == "flow" or key != "contact_database"
                    ],
                    "source_query": definition.data.data_asset.query,
                    "source_query_dialect": "athena",
                }
                for definition, _ in prepared
            },
            run_metadata={
                **(run_metadata or {}),
                "event": {
                    key: value.isoformat() if hasattr(value, "isoformat") else value
                    for key, value in event.items()
                },
                "rollups_as_of": config["rollups"]["as_of"].isoformat(),
            },
            batch_parameters={definition.name: parameters for definition, parameters in prepared},
            run_id=RunIdentifier(run_name=run_directory.name),
        )
        manifest = json.loads((run_directory / "reports" / "manifest.json").read_text())
        print(
            json.dumps(
                {
                    "report_run_id": manifest["run_id"],
                    "report_manifest_uri": (
                        f"{reporting['s3_uri'].rstrip('/')}/runs/{manifest['run_id']}/manifest.json"
                    ),
                    "success": all(result.success for result in results.values()),
                    "validations": {name: result.statistics for name, result in results.items()},
                },
                indent=2,
            )
        )
        return 0 if all(result.success for result in results.values()) else 1
    finally:
        engine.close()
