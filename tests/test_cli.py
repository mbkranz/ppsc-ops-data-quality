"""Exercise installed entry points without live credentials or lake data."""

import json

import great_expectations as gx
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
    assert len(list((output / "suites").glob("*.suite.json"))) == 2
    for name, count in [("flow", 28), ("rollups", 25)]:
        result = json.loads((output / "results" / f"{name}.json").read_text())
        assert result["success"] is True
        assert result["statistics"]["evaluated_expectations"] == count
        assert (output / "sql" / f"{name}.sql").exists()
    original = (output / "run.json").read_bytes()
    assert main(["demo", "--run-dir", str(output)]) == 2
    assert "FileExistsError" in capsys.readouterr().err
    assert (output / "run.json").read_bytes() == original
