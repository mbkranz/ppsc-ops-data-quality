"""Explicit SQL query / native GX suite selection and one-run result handling."""

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import UTC, date, datetime
from importlib.metadata import version
from pathlib import Path

import great_expectations as gx
from great_expectations.core import RunIdentifier
from great_expectations.data_context.types.base import (
    DataContextConfig,
    InMemoryStoreBackendDefaults,
)

from .athena import (
    check_physical_schema,
    inspect_tables,
    snapshot_time,
    source_table,
    sqlalchemy_url,
)
from .batches import account_reference_counts, current_state, state_at
from .config import Config, load_config, validate_bindings, validate_config
from .gx import account, account_contact_relation, account_contact_relation_to_account

# Keep full failure counts while bounding diagnostic samples.
RESULT_FORMAT = {
    "result_format": "COMPLETE",
    "partial_unexpected_count": 200,
    "return_unexpected_index_query": False,
}


def build_queries(config: Config, as_of: date | None, lake_as_of: datetime) -> list[tuple]:
    """Keep the complete runtime selection visible in one place."""
    account_history = source_table(config.tables["account"], lake_as_of)
    acr_history = source_table(config.tables["account_contact_relation"], lake_as_of)
    if as_of is None:
        account_state = current_state(account_history)
        acr_state = current_state(acr_history)
    else:
        account_state = state_at(account_history, as_of)
        acr_state = state_at(acr_history, as_of)
    relationship = account_reference_counts(acr_state, account_state)
    relations = {"account_state": account_state, "account_contact_relation_state": acr_state}
    return [
        ("account", account_state, account.build_suite(relations)),
        ("account_contact_relation", acr_state, account_contact_relation.build_suite(relations)),
        (
            "account_contact_relation_to_account",
            relationship,
            account_contact_relation_to_account.build_suite(relations),
        ),
    ]


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def _exception_messages(value) -> list[str]:
    """GX can nest exceptions under metric IDs instead of a top-level flag."""
    if isinstance(value, dict):
        if value.get("raised_exception"):
            return [value.get("exception_message") or "GX reported an execution error"]
        return [message for child in value.values() for message in _exception_messages(child)]
    if isinstance(value, list):
        return [message for child in value for message in _exception_messages(child)]
    return []


def summarize_result(name: str, result: dict) -> dict:
    rules = []
    for item in result["results"]:
        expectation = item["expectation_config"]
        details = item.get("result", {})
        errors = _exception_messages(item.get("exception_info", {}))
        status = "error" if errors else ("pass" if item.get("success") else "fail")
        count = details.get("unexpected_count")
        if expectation["type"] == "unexpected_rows_expectation":
            count = details.get("observed_value")
        sample = details.get("details", {}).get("unexpected_rows")
        if sample is None:
            sample = details.get("partial_unexpected_list", [])
        rules.append(
            {
                "rule_id": expectation.get("meta", {}).get("rule_id", expectation["type"]),
                "expectation_type": expectation["type"],
                "status": status,
                "unexpected_count": None if errors else count,
                "sample_count": len(sample),
                "errors": errors,
            }
        )
    errors = _exception_messages(result.get("exception_info", {}))
    if errors or any(rule["status"] == "error" for rule in rules):
        status = "error"
    else:
        status = "pass" if result["success"] else "fail"
    return {"asset": name, "status": status, "rules": rules, "errors": errors}


def exit_code(summary: dict) -> int:
    if summary["errors"] or any(asset["status"] == "error" for asset in summary["assets"]):
        return 2
    return 1 if any(asset["status"] == "fail" for asset in summary["assets"]) else 0


def run_validations(queries: list[tuple], connection_string: str, output: Path) -> dict:
    """Execute native SQL validations; a local SQL connection is used only by tests."""
    context = gx.get_context(
        mode="ephemeral",
        project_config=DataContextConfig(
            analytics_enabled=False,
            store_backend_defaults=InMemoryStoreBackendDefaults(),
            progress_bars={"globally": False},
            data_docs_sites={
                "local": {
                    "class_name": "SiteBuilder",
                    "store_backend": {
                        "class_name": "TupleFilesystemStoreBackend",
                        "base_directory": str((output / "data_docs").resolve()),
                    },
                    "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
                }
            },
        ),
    )
    datasource = context.data_sources.add_sql(
        name="validation", connection_string=connection_string, create_temp_table=False
    )
    summary = {"status": "running", "assets": [], "errors": []}
    try:
        for name, query, suite in queries:
            try:
                asset = datasource.add_query_asset(name=name, query=query)
                batch = asset.add_batch_definition_whole_table(name="selected_population")
                suite = context.suites.add(suite)
                validation = context.validation_definitions.add(
                    gx.ValidationDefinition(name=name, data=batch, suite=suite)
                )
                result = validation.run(
                    result_format=RESULT_FORMAT, run_id=RunIdentifier(run_name=output.name)
                ).to_json_dict()
                write_json(output / "results" / f"{name}.json", result)
                summary["assets"].append(summarize_result(name, result))
            except Exception as error:
                failure = {
                    "asset": name,
                    "status": "error",
                    "rules": [],
                    "errors": [f"{type(error).__name__}: {error}"],
                }
                summary["assets"].append(failure)
                write_json(output / "results" / f"{name}.error.json", failure)
        try:
            context.build_data_docs()
        except Exception as error:
            summary["errors"].append(f"Data Docs: {type(error).__name__}: {error}")
    finally:
        # Close native GX SQL resources even when validation/reporting fails.
        datasource.get_execution_engine().close()
    summary["status"] = {0: "pass", 1: "fail", 2: "error"}[exit_code(summary)]
    return summary


def code_identity() -> dict:
    root = Path(__file__).resolve().parents[2]
    identity = {"revision": None, "dirty": None, "lock_sha256": None}
    if (root / ".git").exists():
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
        )
        if revision.returncode == 0:
            identity["revision"] = revision.stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False
        )
        identity["dirty"] = bool(status.stdout) if status.returncode == 0 else None
    lock = root / "uv.lock"
    if lock.is_file():
        identity["lock_sha256"] = hashlib.sha256(lock.read_bytes()).hexdigest()
    return identity


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Account and ACR state in Athena")
    parser.add_argument("--config", default="params.local.yaml")
    population = parser.add_mutually_exclusive_group(required=True)
    population.add_argument("--as-of", type=date.fromisoformat, help="Effective date (YYYY-MM-DD)")
    population.add_argument("--current", action="store_true", help="Select is_current = true")
    parser.add_argument("--lake-as-of", type=snapshot_time, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Write SQL and suites without AWS")
    parser.add_argument(
        "--output", type=Path, help="Parent directory for a new unique run directory"
    )
    args = parser.parse_args(argv)
    output = None
    run = None
    try:
        config = load_config(args.config)
        validate_config(config, live=not args.dry_run)
        validate_bindings(config)
        if not args.dry_run and args.as_of and not config.interval_convention_confirmed:
            raise ValueError(
                "Confirm [valid_from, valid_to) and set interval_convention_confirmed: true"
            )
        now = datetime.now(UTC)
        run_id = now.strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
        output = (args.output or config.output) / run_id
        output.mkdir(parents=True, exist_ok=False)
        run = {
            "run_id": run_id,
            "started_at": now.isoformat(),
            "mode": "preview" if args.dry_run else "live",
            "population": "as_of" if args.as_of else "current",
            "effective_date": args.as_of.isoformat() if args.as_of else None,
            "lake_as_of": args.lake_as_of.isoformat(),
            "config": config.as_dict(),
            "code": code_identity(),
            "versions": {
                name: version(name)
                for name in (
                    "ppsc-ops-data-quality",
                    "great-expectations",
                    "sqlglot",
                    "PyAthena",
                    "SQLAlchemy",
                )
            },
            "load_completion_status": "evidence_provided"
            if config.load_completion_evidence
            else "unresolved",
            "status": "preparing",
        }
        write_json(output / "run.json", run)
        queries = build_queries(config, args.as_of, args.lake_as_of)
        (output / "sql").mkdir()
        for name, sql, suite in queries:
            (output / "sql" / f"{name}.sql").write_text(sql + "\n")
            write_json(output / "suites" / f"{name}.json", suite.to_json_dict())
        if args.dry_run:
            summary = {"status": "preview", "assets": [], "errors": []}
        else:
            run["preflight"] = inspect_tables(config, lake_as_of=args.lake_as_of)
            write_json(output / "run.json", run)
            check_physical_schema(config, run["preflight"])
            summary = run_validations(
                queries, sqlalchemy_url(config).render_as_string(hide_password=False), output
            )
        summary["run_id"] = run_id
        run["status"] = summary["status"]
        run["finished_at"] = datetime.now(UTC).isoformat()
        write_json(output / "run.json", run)
        write_json(output / "summary.json", summary)
        print(f"{summary['status'].upper()}: {output}")
        if run["load_completion_status"] == "unresolved":
            print("Load completeness is unresolved; see run.json before interpreting findings.")
        for asset in summary["assets"]:
            print(f"  {asset['asset']}: {asset['status']}")
            for rule in asset["rules"]:
                count = rule["unexpected_count"]
                suffix = (
                    f"; unexpected={count}; sample={rule['sample_count']}"
                    if count is not None
                    else ""
                )
                print(f"    {rule['rule_id']}: {rule['status']}{suffix}")
        return exit_code(summary)
    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        print(f"ERROR: {message}", file=sys.stderr)
        if output is not None:
            write_json(
                output / "summary.json", {"status": "error", "assets": [], "errors": [message]}
            )
            if run is not None:
                run.update(status="error", finished_at=datetime.now(UTC).isoformat())
                write_json(output / "run.json", run)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
