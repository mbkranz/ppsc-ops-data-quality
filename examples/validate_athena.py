"""Run configured Athena comparisons. Invoke only with verified local bindings."""

import argparse
import json
import sys
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
from ppsc_ops_data_quality.runtime import run_validations
from ppsc_ops_data_quality.runtime.athena import prepare_validation
from ppsc_ops_data_quality.schemas import (
    ACCOUNT_HISTORY_VALIDATION_INPUT,
    CONTACT_HISTORY_VALIDATION_INPUT,
    SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
    history_tables,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    text = args.config.read_text()
    if "REPLACE_WITH_" in text:
        raise ValueError("Replace the example configuration bindings before connecting")
    config = tomllib.loads(text)
    athena = config["athena"]
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
    args.run_dir.mkdir(parents=True, exist_ok=False)
    context = gx.get_context(mode="file", project_root_dir=str(args.run_dir / "gx"))
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
                    metadata={"run_name": args.run_dir.name},
                    sql_path=args.run_dir / "sql" / f"{name}.sql",
                )
            )
        results = run_validations(
            [definition for definition, _ in prepared],
            suite_directory=args.run_dir / "suites",
            batch_parameters={definition.name: parameters for definition, parameters in prepared},
            run_id=RunIdentifier(run_name=args.run_dir.name),
        )
        print(json.dumps({name: result.statistics for name, result in results.items()}, indent=2))
        return 0 if all(result.success for result in results.values()) else 1
    finally:
        engine.close()


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        exit_code = 2
    raise SystemExit(exit_code)
