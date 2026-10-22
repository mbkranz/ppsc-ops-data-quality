"""Exercise installed entry points without live credentials or lake data."""

import gzip
import json

import great_expectations as gx
import pyarrow.parquet as pq
import sqlglot

from ppsc_ops_data_quality.cli import main


def test_preview_exports_native_suites_and_athena_selects(tmp_path, capsys):
    output = tmp_path / "preview"
    assert main(["preview", "--output", str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["live_queries"] is False
    for name, count in [("flow", 27), ("rollups", 24)]:
        suite = gx.ExpectationSuite(**json.loads((output / f"{name}.suite.json").read_text()))
        assert len(suite.expectations) == count
        sql = (output / f"{name}.sql").read_text()
        sqlglot.parse_one(sql, read="athena")
        assert '"history"' in sql
    assert main(["preview", "--output", str(output)]) == 2
    assert "FileExistsError" in capsys.readouterr().err


def test_demo_validates_both_suites_and_retains_run_evidence(tmp_path, capsys):
    output = tmp_path / "run"
    assert main(["demo", "--run-dir", str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["success"] is True
    assert summary["source"] == "synthetic_history"
    assert json.loads((output / "run.json").read_text()) == summary
    reports = output / "reports"
    assert len(list((reports / "suites").glob("*.suite.json"))) == 2
    assert (reports / "data_docs" / "index.html").exists()
    assert len(list((reports / "analytics").glob("*.parquet"))) == 2
    expectation_rows = pq.read_table(reports / "analytics" / "expectations.parquet").to_pylist()
    assert len(expectation_rows) == 53
    assert (
        len(
            {
                (row["run_id"], row["validation_definition_name"], row["expectation_index"])
                for row in expectation_rows
            }
        )
        == 53
    )
    assert sum(row["validation_definition_name"] == "flow" for row in expectation_rows) == 28
    assert sum(row["validation_definition_name"] == "rollups" for row in expectation_rows) == 25
    assert pq.read_table(reports / "analytics" / "validations.parquet").num_rows == 2
    for stem, count in [("000_flow", 28), ("001_rollups", 25)]:
        result = json.loads(gzip.decompress((reports / "results" / f"{stem}.json.gz").read_bytes()))
        assert result["success"] is True
        assert result["statistics"]["evaluated_expectations"] == count
        assert (reports / "queries" / f"{stem}.sql").exists()
    original = (output / "run.json").read_bytes()
    assert main(["demo", "--run-dir", str(output)]) == 2
    assert "FileExistsError" in capsys.readouterr().err
    assert (output / "run.json").read_bytes() == original
