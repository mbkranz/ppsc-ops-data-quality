"""Offline query preview and synthetic validation entry points."""

import argparse
import json
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import great_expectations as gx
import ibis
from great_expectations.core import RunIdentifier

from ppsc_ops_data_quality import demo
from ppsc_ops_data_quality.account_to_survey_results_expectations import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.gx_queries import query_asset_sql
from ppsc_ops_data_quality.runtime import run_validations_with_reports
from ppsc_ops_data_quality.runtime.artifacts import save_suite
from ppsc_ops_data_quality.runtime.duckdb import prepare_validation
from ppsc_ops_data_quality.schemas import history_tables


def preview(output: Path):
    """Compile illustrative Athena comparisons and export native suite definitions."""
    history = history_tables(
        account_database="example_account",
        contact_database="example_contact",
        survey_result_database="example_survey_result",
    )
    output.mkdir(parents=True, exist_ok=False)
    for name, query in demo.comparisons(history).items():
        (output / f"{name}.sql").write_text(query_asset_sql(query) + ";\n", encoding="utf-8")
        suite = flow_account_suite() if name == "flow" else rollup_account_suite()
        save_suite(suite, output / f"{name}.suite.json")
    return {"mode": "preview", "output": str(output), "live_queries": False}


def validate_demo(run_directory: Path, *, s3_uri: str | None = None):
    """Run two native definitions locally and save SQL, suites, results and run facts."""
    run_directory.mkdir(parents=True, exist_ok=False)
    backend = ibis.duckdb.connect()
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    source = context.data_sources.add_pandas(name="synthetic_comparisons")
    identifier = RunIdentifier(run_name=run_directory.name)
    try:
        queries = demo.comparisons(demo.history_tables(backend))
        prepared = []
        for name, query in queries.items():
            suite = (
                flow_account_suite(expected_row_count=1)
                if name == "flow"
                else rollup_account_suite(expected_row_count=1)
            )
            suite = context.suites.add(suite)
            prepared.append(
                prepare_validation(
                    context,
                    source,
                    backend,
                    query,
                    suite,
                    name=name,
                    metadata={"source": "synthetic_history", "run_name": identifier.run_name},
                )
            )
        results = run_validations_with_reports(
            context,
            [definition for definition, _ in prepared],
            run_directory=run_directory / "reports",
            s3_uri=s3_uri,
            sources={
                name: {
                    "source_tables": [
                        "Account_history",
                        "Survey_Result__c_history",
                        *(["Contact_history"] if name == "flow" else []),
                    ],
                    "source_query": backend.compile(query, limit=None),
                    "source_query_dialect": "duckdb",
                }
                for name, query in queries.items()
            },
            run_metadata={
                "source": "synthetic_history",
                "survey_result_id": demo.EVENT_ID,
                "account_before_at": demo.BEFORE_AT.isoformat(),
                "execution_at": demo.EXECUTION_AT.isoformat(),
                "account_after_at": demo.AFTER_AT.isoformat(),
                "flow_run_date": demo.FLOW_RUN_DATE.isoformat(),
            },
            batch_parameters={definition.name: parameters for definition, parameters in prepared},
            run_id=identifier,
        )
        report_manifest = json.loads((run_directory / "reports" / "manifest.json").read_text())
        summary = {
            "mode": "synthetic_duckdb",
            "run_name": identifier.run_name,
            "run_time": identifier.run_time.isoformat(),
            "source": "synthetic_history",
            "report_run_id": report_manifest["run_id"],
            "report_manifest": str(run_directory / "reports" / "manifest.json"),
            "report_s3_uri": (
                f"{s3_uri.rstrip('/')}/runs/{report_manifest['run_id']}/" if s3_uri else None
            ),
            "survey_result_id": demo.EVENT_ID,
            "account_before_at": demo.BEFORE_AT.isoformat(),
            "execution_at": demo.EXECUTION_AT.isoformat(),
            "account_after_at": demo.AFTER_AT.isoformat(),
            "flow_run_date": demo.FLOW_RUN_DATE.isoformat(),
            "versions": {
                name: version(name)
                for name in (
                    "ppsc-ops-data-quality",
                    "great-expectations",
                    "ibis-framework",
                    "sqlglot",
                )
            },
            "success": all(result.success for result in results.values()),
            "validations": {name: result.statistics for name, result in results.items()},
        }
        (run_directory / "run.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        return summary
    finally:
        backend.disconnect()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preview_parser = commands.add_parser("preview", help="Compile Athena examples without AWS")
    preview_parser.add_argument("--output", type=Path)
    demo_parser = commands.add_parser("demo", help="Validate synthetic DuckDB history")
    demo_parser.add_argument("--run-dir", type=Path)
    demo_parser.add_argument("--s3-uri", help="Publish this synthetic run to an existing S3 prefix")
    live_parser = commands.add_parser("validate", help="Validate configured Athena history")
    live_parser.add_argument("--config", type=Path, required=True)
    live_parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            from ppsc_ops_data_quality.runtime.job import validate_athena

            return validate_athena(args.config, args.run_dir)
        if args.command == "preview":
            summary = preview(
                args.output
                or Path("build/previews") / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            )
        else:
            run_directory = args.run_dir or Path("build/runs") / datetime.now(UTC).strftime(
                "%Y%m%dT%H%M%S%fZ"
            )
            summary = validate_demo(run_directory, s3_uri=args.s3_uri)
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("success", True) else 1
