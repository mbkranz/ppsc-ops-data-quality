"""Exercise installed entry points without live credentials or lake data."""

import gzip
import json

import great_expectations as gx
import pyarrow.parquet as pq
import pytest
import sqlglot

from scripts.check_validation import compile_comparisons, validate_synthetic


def test_compilation_exports_native_suites_and_athena_selects(tmp_path, capsys):
    output = tmp_path / "preview"
    summary = compile_comparisons(output)
    assert summary["live_queries"] is False
    for name, count in [("flow", 27), ("rollups", 24)]:
        suite = gx.ExpectationSuite(**json.loads((output / f"{name}.suite.json").read_text()))
        assert len(suite.expectations) == count
        sql = (output / f"{name}.sql").read_text()
        sqlglot.parse_one(sql, read="athena")
        assert '"history"' in sql
    with pytest.raises(FileExistsError):
        compile_comparisons(output)


def test_synthetic_validates_both_suites_and_retains_run_evidence(tmp_path, capsys):
    output = tmp_path / "run"
    summary = validate_synthetic(output)
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
    with pytest.raises(FileExistsError):
        validate_synthetic(output)
    assert (output / "run.json").read_bytes() == original
