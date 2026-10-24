"""Development-only compilation, fixtures and synthetic validation checks."""

import argparse
import gzip
import json
from datetime import UTC, date, datetime
from importlib.metadata import version
from pathlib import Path

import great_expectations as gx
import ibis
import pyarrow as pa
import pyarrow.parquet as pq
from great_expectations.core import RunIdentifier

from ppsc_ops_data_quality.account_to_survey_results.gx import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.account_to_survey_results.lineage import PROJECTION_LINEAGE
from ppsc_ops_data_quality.account_to_survey_results.metadata import metadata_receipt
from ppsc_ops_data_quality.account_to_survey_results.queries import (
    ROLLUP_ACCOUNT_FIELDS,
    add_flow_context,
    expected_account_values,
    expected_survey_rollups,
    flow_account_query,
    join_account,
    rollup_account_query,
)
from ppsc_ops_data_quality.core.queries import history_tables, snapshot
from ppsc_ops_data_quality.core.queries.sql import to_sqlglot
from ppsc_ops_data_quality.core.schemas import (
    ACCOUNT_HISTORY_VALIDATION_INPUT,
    CONTACT_HISTORY_VALIDATION_INPUT,
    SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
)
from ppsc_ops_data_quality.gx_queries import query_asset_sql
from ppsc_ops_data_quality.runtime import run_validations_with_reports
from ppsc_ops_data_quality.runtime.artifacts import save_suite
from ppsc_ops_data_quality.runtime.duckdb import prepare_validation

EVENT_ID = "synthetic_basics_event"
BEFORE_AT = datetime(2026, 10, 21, 11, 59, 59)
EXECUTION_AT = datetime(2026, 10, 21, 12)
AFTER_AT = datetime(2026, 10, 21, 12, 5)
FLOW_RUN_DATE = date(2026, 10, 21)


def comparisons(history):
    """Compose examples with independently declared BEFORE and AFTER boundaries."""
    return {
        "flow": flow_account_query(
            history,
            survey_result_id=EVENT_ID,
            account_before_at=BEFORE_AT,
            execution_at=EXECUTION_AT,
            account_after_at=AFTER_AT,
            flow_run_date=FLOW_RUN_DATE,
        ),
        "rollups": rollup_account_query(history, as_of=AFTER_AT),
    }


def synthetic_history_tables(backend):
    """Create small DuckDB history tables; observed AFTER values are explicit.

    One completed Basics survey updates the Account timestamp and count. Expected
    values are computed by the existing query builders, not used to construct the
    observed rows. All identifiers are synthetic. No files or AWS services are read.
    """
    account = {field: None for field in ACCOUNT_HISTORY_VALIDATION_INPUT}
    account.update(
        Id="synthetic_account",
        PersonContactId="synthetic_contact",
        IsPersonAccount=True,
        valid_from=datetime(2026, 1, 1),
        valid_to=AFTER_AT,
        is_current=False,
        loaded_at=AFTER_AT,
    )
    account.update({field: 0 for field in ROLLUP_ACCOUNT_FIELDS})
    after = dict(
        account,
        valid_from=AFTER_AT,
        valid_to=None,
        is_current=True,
        Basics_Date_Time__c=EXECUTION_AT,
        PP1_Basics_Survey_Complete__pc=1,
    )
    contact = {
        "Id": "synthetic_contact",
        "AccountId": "synthetic_account",
        "Birthdate": date(2000, 1, 1),
        "valid_from": datetime(2026, 1, 1),
        "valid_to": None,
        "is_current": True,
        "loaded_at": AFTER_AT,
    }
    survey = {field: None for field in SURVEY_RESULT_HISTORY_VALIDATION_INPUT}
    survey.update(
        Id=EVENT_ID,
        Participant__c="synthetic_contact",
        Survey_Index_Number__c="2001",
        Completion_Status__c="Complete",
        Consent_Status__c="Yes",
        Consent_Revoked__c=False,
        Completion_Status_Timestamp__c=EXECUTION_AT,
        valid_from=EXECUTION_AT,
        valid_to=None,
        is_current=True,
        loaded_at=AFTER_AT,
    )
    history = {}
    for name, schema, rows in (
        ("Account", ACCOUNT_HISTORY_VALIDATION_INPUT, [account, after]),
        ("Contact", CONTACT_HISTORY_VALIDATION_INPUT, [contact]),
        ("Survey_Result__c", SURVEY_RESULT_HISTORY_VALIDATION_INPUT, [survey]),
    ):
        table = pa.Table.from_pylist(rows, schema=schema.to_pyarrow())
        history[name] = backend.create_table(name + "_history", ibis.memtable(table))
    return history


def compile_comparisons(output: Path):
    """Compile illustrative Athena comparisons and export native suite definitions."""
    history = history_tables(
        account_database="example_account",
        contact_database="example_contact",
        survey_result_database="example_survey_result",
    )
    output.mkdir(parents=True, exist_ok=False)
    for name, query in comparisons(history).items():
        (output / f"{name}.sql").write_text(
            query_asset_sql(query, projection_lineage=PROJECTION_LINEAGE) + ";\n", encoding="utf-8"
        )
        suite = flow_account_suite() if name == "flow" else rollup_account_suite()
        assert len(suite.expectations) == (27 if name == "flow" else 24)
        save_suite(suite, output / f"{name}.suite.json")
    return {"mode": "compile", "output": str(output), "live_queries": False}


def render_examples(output: Path):
    """Regenerate the checked-in illustrative expected and GX comparison SQL."""
    history = history_tables(
        account_database="example_account",
        contact_database="example_contact",
        survey_result_database="example_survey_result",
    )
    event_id = "EXAMPLE_VERIFIED_SURVEY_EVENT"
    AccountBefore = snapshot(history["Account"], as_of=BEFORE_AT).alias("Account_Before")
    Contact = snapshot(history["Contact"], as_of=EXECUTION_AT).alias("Contact_At_Execution")
    Survey = snapshot(history["Survey_Result__c"], as_of=EXECUTION_AT).alias(
        "Survey_Results_At_Execution"
    )
    Trigger = Survey.filter(Survey.Id == event_id).alias("Trigger_Survey_Result")
    Record = add_flow_context(
        join_account(Trigger, Contact, AccountBefore),
        Survey,
        flow_run_date=ibis.literal(FLOW_RUN_DATE),
    )
    expected = {
        "flow": expected_account_values(Record),
        "rollups": expected_survey_rollups(
            snapshot(history["Account"], as_of=EXECUTION_AT).alias("Account_At_Snapshot"),
            Survey,
        ),
    }
    comparison = {
        "flow": flow_account_query(
            history,
            survey_result_id=event_id,
            account_before_at=BEFORE_AT,
            execution_at=EXECUTION_AT,
            account_after_at=AFTER_AT,
            flow_run_date=FLOW_RUN_DATE,
        ),
        "rollups": rollup_account_query(history, as_of=EXECUTION_AT),
    }
    header = (
        "-- ILLUSTRATIVE bindings/event/times; source profiles are defined in core/schemas/.\n"
        "-- Direct SELECTs over history. Verify physical catalog types before execution.\n"
        "-- Execution: 2026-10-21 12:00; BEFORE: 11:59:59; settled AFTER: 12:05.\n\n"
    )
    output.mkdir(parents=True, exist_ok=True)
    for filename, queries, is_comparison in (
        ("account_to_survey_results.sql", expected, False),
        ("account_to_survey_results_gx_comparison.sql", comparison, True),
    ):
        statements = []
        for name, query in queries.items():
            sql = (
                query_asset_sql(query, projection_lineage=PROJECTION_LINEAGE)
                if is_comparison
                else to_sqlglot(query, projection_lineage=PROJECTION_LINEAGE).sql(
                    dialect="athena", pretty=True
                )
            )
            statements.append(f"-- {name}\n{sql};\n")
        (output / filename).write_text(header + "\n".join(statements), encoding="utf-8")
    return {"mode": "render", "output": str(output), "live_queries": False}


def validate_synthetic(run_directory: Path, *, s3_uri: str | None = None):
    """Run two native definitions locally and save SQL, suites, results and run facts."""
    run_directory.mkdir(parents=True, exist_ok=False)
    backend = ibis.duckdb.connect()
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    source = context.data_sources.add_pandas(name="synthetic_comparisons")
    identifier = RunIdentifier(run_name=run_directory.name)
    try:
        queries = comparisons(synthetic_history_tables(backend))
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
                "metadata_inputs": metadata_receipt().model_dump(mode="json"),
                "source": "synthetic_history",
                "survey_result_id": EVENT_ID,
                "account_before_at": BEFORE_AT.isoformat(),
                "execution_at": EXECUTION_AT.isoformat(),
                "account_after_at": AFTER_AT.isoformat(),
                "flow_run_date": FLOW_RUN_DATE.isoformat(),
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
            "survey_result_id": EVENT_ID,
            "account_before_at": BEFORE_AT.isoformat(),
            "execution_at": EXECUTION_AT.isoformat(),
            "account_after_at": AFTER_AT.isoformat(),
            "flow_run_date": FLOW_RUN_DATE.isoformat(),
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
        verify_synthetic_evidence(run_directory)
        return summary
    finally:
        backend.disconnect()


def verify_synthetic_evidence(directory: Path) -> None:
    """Check the complete evidence contract, also when using an installed wheel."""
    reports = directory / "reports"
    rows = pq.read_table(reports / "analytics/expectations.parquet").to_pylist()
    assert len(rows) == 53
    assert (
        len({(r["run_id"], r["validation_definition_name"], r["expectation_index"]) for r in rows})
        == 53
    )
    assert pq.read_table(reports / "analytics/validations.parquet").num_rows == 2
    assert (reports / "data_docs/index.html").is_file()
    assert (reports / "manifest.json").is_file()
    for stem, count in (("000_flow", 28), ("001_rollups", 25)):
        result = json.loads(gzip.decompress((reports / "results" / f"{stem}.json.gz").read_bytes()))
        assert result["success"] is True
        assert result["statistics"]["evaluated_expectations"] == count
        assert (reports / "queries" / f"{stem}.sql").is_file()
        suite = json.loads((reports / "suites" / f"{stem}.suite.json").read_text())
        assert len(suite["expectations"]) == count


def main(argv=None):
    parser = argparse.ArgumentParser(description="Credential-free development verification")
    parser.add_argument("check", choices=["compile", "synthetic", "render"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.check == "render":
        summary = render_examples(args.output or Path("sql"))
    else:
        output = args.output or Path("build/checks") / (
            args.check + "-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        )
        summary = (
            compile_comparisons(output) if args.check == "compile" else validate_synthetic(output)
        )
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("success", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
