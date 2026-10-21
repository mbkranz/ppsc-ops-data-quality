"""Exercise the actual runner and preview CLI without live AWS access."""

import json
import sqlite3
from pathlib import Path

import great_expectations as gx
import pytest

from ppsc_ops_data_quality import run
from ppsc_ops_data_quality.gx import (
    account,
    account_contact_relation,
    account_contact_relation_to_account,
)

CONFIG = Path(__file__).resolve().parents[1] / "params.yaml"


def fixture_connection(tmp_path, children):
    """The batch-function tests separately establish how parent counts are built."""
    database = tmp_path / "run_fixture.sqlite"
    with sqlite3.connect(database) as connection:
        connection.executescript(
            "CREATE TABLE account (id TEXT, valid_from TEXT, valid_to TEXT, "
            "is_current INTEGER, loaded_at TEXT);"
            "CREATE TABLE acr (id TEXT, valid_from TEXT, valid_to TEXT, "
            "is_current INTEGER, loaded_at TEXT, account_id TEXT, "
            "matching_account_versions INTEGER);"
        )
        connection.execute(
            "INSERT INTO account VALUES (?, ?, ?, ?, ?)",
            ("parent", "2020-01-01", None, 1, "2026-01-01"),
        )
        connection.executemany(
            "INSERT INTO acr VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (identifier, "2020-01-01", None, 1, "2026-01-01", reference, count)
                for identifier, reference, count in children
            ],
        )
    return f"sqlite:///{database}"


@pytest.mark.parametrize("missing_parents", [0, 205])
def test_native_validation_run_saves_results_and_data_docs(tmp_path, missing_parents):
    children = [("valid", "parent", 1)]
    children += [(f"missing-{number}", "absent", 0) for number in range(missing_parents)]
    connection = fixture_connection(tmp_path, children)
    output = tmp_path / "output"
    output.mkdir()
    queries = [
        ("account", "SELECT * FROM account", account.build_suite()),
        ("account_contact_relation", "SELECT * FROM acr", account_contact_relation.build_suite()),
        (
            "account_contact_relation_to_account",
            "SELECT * FROM acr",
            account_contact_relation_to_account.build_suite(),
        ),
    ]

    summary = run.run_validations(queries, connection, output)

    assert summary["status"] == ("fail" if missing_parents else "pass")
    assert run.exit_code(summary) == (1 if missing_parents else 0)
    assert summary["errors"] == []
    assert (output / "data_docs" / "index.html").is_file()
    assert {path.stem for path in (output / "results").glob("*.json")} == {
        name for name, _, _ in queries
    }
    for name, _, _ in queries:
        native = json.loads((output / "results" / f"{name}.json").read_text())
        assert native["results"]
        assert native["meta"]["run_id"]["run_name"] == "output"
    relationship = summary["assets"][2]
    finding = next(
        rule
        for rule in relationship["rules"]
        if rule["rule_id"] == "account_contact_relation_to_account.parent.exists"
    )
    assert finding["unexpected_count"] == missing_parents
    assert finding["sample_count"] == min(missing_parents, 200)


def test_execution_error_takes_precedence_over_an_ordinary_data_failure(tmp_path):
    connection = fixture_connection(tmp_path, [("missing", "absent", 0)])
    output = tmp_path / "mixed"
    output.mkdir()
    broken = gx.ExpectationSuite(
        name="broken",
        expectations=[
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query="SELECT unknown_column FROM {batch}",
                catch_exceptions=True,
                meta={"rule_id": "broken.query"},
            )
        ],
    )
    summary = run.run_validations(
        [
            (
                "data_failure",
                "SELECT * FROM acr",
                account_contact_relation_to_account.build_suite(),
            ),
            ("execution_error", "SELECT * FROM account", broken),
        ],
        connection,
        output,
    )

    assert summary["status"] == "error"
    assert run.exit_code(summary) == 2
    assert summary["assets"][0]["status"] == "fail"
    error_asset = summary["assets"][1]
    assert error_asset["status"] == "error"
    rule = error_asset["rules"][0]
    assert rule["status"] == "error"
    assert rule["unexpected_count"] is None
    assert any("unknown_column" in message for message in rule["errors"])
    native = json.loads((output / "results" / "execution_error.json").read_text())
    exceptions = native["results"][0]["exception_info"]
    assert all(info["raised_exception"] for info in exceptions.values())
    assert (output / "data_docs" / "index.html").is_file()


@pytest.mark.parametrize(
    ("selection", "population", "effective_date"),
    [(["--as-of", "2026-10-15"], "as_of", "2026-10-15"), (["--current"], "current", None)],
)
def test_dry_run_writes_only_preview_artifacts_without_live_calls(
    tmp_path, monkeypatch, selection, population, effective_date
):
    def live_call(*args, **kwargs):
        pytest.fail("The dry run attempted to use a live validation entry point")

    for name in ("inspect_tables", "check_physical_schema", "run_validations", "sqlalchemy_url"):
        monkeypatch.setattr(run, name, live_call)
    monkeypatch.setattr(run.gx, "get_context", live_call)
    preview = tmp_path / "preview"

    code = run.main(
        [
            "--config",
            str(CONFIG),
            "--dry-run",
            "--output",
            str(preview),
            "--lake-as-of",
            "2026-10-17T07:00:00-05:00",
            *selection,
        ]
    )

    assert code == 0
    outputs = list(preview.iterdir())
    assert len(outputs) == 1
    output = outputs[0]
    assert {path.name for path in output.iterdir()} == {"run.json", "summary.json", "sql", "suites"}
    record = json.loads((output / "run.json").read_text())
    summary = json.loads((output / "summary.json").read_text())
    assert record["mode"] == "preview"
    assert record["status"] == summary["status"] == "preview"
    assert record["population"] == population
    assert record["effective_date"] == effective_date
    assert record["lake_as_of"] == "2026-10-17T12:00:00+00:00"
    assert record["load_completion_status"] == "unresolved"
    assert record["run_id"] == summary["run_id"] == output.name
    assert summary["assets"] == summary["errors"] == []
    names = {"account", "account_contact_relation", "account_contact_relation_to_account"}
    assert {path.stem for path in (output / "sql").glob("*.sql")} == names
    assert {path.stem for path in (output / "suites").glob("*.json")} == names
    for path in (output / "sql").glob("*.sql"):
        sql = path.read_text()
        expected_sources = 2 if path.stem == "account_contact_relation_to_account" else 1
        assert sql.count("FOR TIMESTAMP AS OF") == expected_sources
    for path in (output / "suites").glob("*.json"):
        assert gx.ExpectationSuite(**json.loads(path.read_text())).expectations


@pytest.mark.parametrize("selection", [[], ["--current", "--as-of", "2026-10-15"]])
def test_cli_requires_exactly_one_population_selection(tmp_path, selection):
    with pytest.raises(SystemExit) as error:
        run.main(
            [
                "--config",
                str(CONFIG),
                "--dry-run",
                "--output",
                str(tmp_path / "unused"),
                "--lake-as-of",
                "2026-10-17T12:00:00Z",
                *selection,
            ]
        )
    assert error.value.code == 2
    assert not (tmp_path / "unused").exists()
