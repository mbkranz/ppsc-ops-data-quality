"""Runtime adapters and runner using native GX, DuckDB and SQLAlchemy/SQLite."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import great_expectations as gx
import great_expectations.expectations as gxe
import ibis
import pyarrow as pa
import sqlalchemy as sa
from great_expectations.core import RunIdentifier
from test_account_to_survey_results_expectations import flow_inputs
from test_snapshot import example_queries

from ppsc_ops_data_quality.account_to_survey_results import expected_survey_rollups
from ppsc_ops_data_quality.account_to_survey_results_expectations import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.queries import (
    ROLLUP_ACCOUNT_FIELDS,
    flow_account_comparison,
    rollup_account_comparison,
)
from ppsc_ops_data_quality.runtime.artifacts import save_suite
from ppsc_ops_data_quality.runtime.athena import prepare_validation as prepare_athena
from ppsc_ops_data_quality.runtime.duckdb import prepare_validation as prepare_duckdb
from ppsc_ops_data_quality.runtime.runner import run_validations
from ppsc_ops_data_quality.schemas import ACCOUNT_VALIDATION_INPUT, SURVEY_RESULT_VALIDATION_INPUT


def make_context():
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    return context


def rollup_comparison():
    row = {name: None for name in ACCOUNT_VALIDATION_INPUT}
    row.update(Id="a1", PersonContactId="c1", IsPersonAccount=True)
    row.update({field: 0 for field in ROLLUP_ACCOUNT_FIELDS})
    account = ibis.memtable(
        pa.Table.from_pylist([row], schema=ACCOUNT_VALIDATION_INPUT.to_pyarrow())
    )
    survey = ibis.memtable(
        pa.Table.from_pylist([], schema=SURVEY_RESULT_VALIDATION_INPUT.to_pyarrow())
    )
    return rollup_account_comparison(expected_survey_rollups(account, survey), account)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.suite_directory = Path(temporary.name) / "suites"

    def test_duckdb_runs_full_flow_and_rollup_with_distinct_frames(self):
        context = make_context()
        source = context.data_sources.add_pandas(name="local_runtime")
        backend = ibis.duckdb.connect()
        expected, after = flow_inputs()
        flow_suite = context.suites.add(flow_account_suite(expected_row_count=1))
        rollup_suite = context.suites.add(rollup_account_suite(expected_row_count=1))
        with tempfile.TemporaryDirectory() as directory:
            sql_path = Path(directory) / "sql" / "flow.sql"
            flow, flow_params = prepare_duckdb(
                context,
                source,
                backend,
                flow_account_comparison(expected, after),
                flow_suite,
                name="flow",
                sql_path=sql_path,
                metadata={"run_id": "test_run"},
            )
            rollup, rollup_params = prepare_duckdb(
                context,
                source,
                backend,
                rollup_comparison(),
                rollup_suite,
                name="rollups",
            )
            self.assertIsInstance(flow, gx.ValidationDefinition)
            self.assertIsNot(flow_params["dataframe"], rollup_params["dataframe"])
            self.assertEqual(
                sql_path.read_text(),
                backend.compile(flow_account_comparison(expected, after), limit=None),
            )
            results = run_validations(
                [flow, rollup],
                batch_parameters={flow.name: flow_params, rollup.name: rollup_params},
                suite_directory=self.suite_directory,
            )
            self.assertTrue(all(result.success for result in results.values()))
            saved = json.loads((self.suite_directory / "000_flow.suite.json").read_text())
            self.assertEqual(saved, flow.suite.to_json_dict())
            loaded = gx.ExpectationSuite(**saved)
            self.assertEqual(loaded.to_json_dict(), flow.suite.to_json_dict())
            self.assertEqual(len(saved["expectations"]), 28)
            self.assertTrue(any(e.get("meta", {}).get("ppsc") for e in saved["expectations"]))
            self.assertEqual(
                json.loads((self.suite_directory / "001_rollups.suite.json").read_text()),
                rollup.suite.to_json_dict(),
            )
            self.assertEqual(set(results), {"flow", "rollups"})
            self.assertEqual(results["flow"].meta["run_id"], results["rollups"].meta["run_id"])
            self.assertEqual(results["flow"].statistics["evaluated_expectations"], 28)
            self.assertEqual(results["rollups"].statistics["evaluated_expectations"], 25)
        backend.disconnect()

    def test_failed_expectation_does_not_skip_later_definition(self):
        context = make_context()
        source = context.data_sources.add_pandas(name="local_failures")
        backend = ibis.duckdb.connect()
        suite = context.suites.add(
            gx.ExpectationSuite(
                name="positive",
                expectations=[gxe.ExpectColumnValuesToBeInSet(column="value", value_set=[1])],
            )
        )
        bad, bad_params = prepare_duckdb(
            context, source, backend, ibis.memtable({"value": [0]}), suite, name="bad"
        )
        good, good_params = prepare_duckdb(
            context, source, backend, ibis.memtable({"value": [1]}), suite, name="good"
        )
        results = run_validations(
            [bad, good],
            batch_parameters={"bad": bad_params, "good": good_params},
            suite_directory=self.suite_directory,
        )
        self.assertFalse(results["bad"].success)
        self.assertTrue(results["good"].success)
        backend.disconnect()

    def test_athena_adapter_compiles_complex_queries_without_executing_them(self):
        context = make_context()
        suite = context.suites.add(flow_account_suite())
        source = context.data_sources.add_sqlite(name="compile_only", connection_string="sqlite://")
        with tempfile.TemporaryDirectory() as directory:
            definition, parameters = prepare_athena(
                context,
                source,
                example_queries()["flow"],
                suite,
                name="flow_query",
                metadata={"run_id": "compile_only"},
                sql_path=Path(directory) / "query.sql",
            )
            self.assertEqual(parameters, {})
            sql = (Path(directory) / "query.sql").read_text()
            self.assertEqual(sql, definition.data.data_asset.query)
            self.assertRegex(sql, r"^SELECT\s")
            self.assertIn('"example_account"."history"', sql)
            self.assertIn("Independently observed Account.", sql)

    def test_athena_adapter_runs_native_sql_validation_on_sqlalchemy(self):
        context = make_context()
        backend = ibis.duckdb.connect()
        expected, after = flow_inputs()
        comparison = flow_account_comparison(expected, after)
        frame = backend.execute(comparison)
        suite = context.suites.add(flow_account_suite(expected_row_count=1))
        with tempfile.TemporaryDirectory() as directory:
            connection_string = "sqlite:///" + str(Path(directory) / "comparison.db")
            engine = sa.create_engine(connection_string)
            frame.to_sql("comparison_rows", engine, index=False)
            source = context.data_sources.add_sqlite(
                name="sql_runtime", connection_string=connection_string
            )
            relation = ibis.table(comparison.schema(), name="comparison_rows")
            definition, parameters = prepare_athena(
                context, source, relation, suite, name="sql_flow"
            )
            results = run_validations(
                [definition],
                batch_parameters={definition.name: parameters},
                suite_directory=self.suite_directory,
            )
            self.assertTrue(results["sql_flow"].success)
            engine.dispose()
        backend.disconnect()

    def test_runner_rejects_ambiguous_parameters_before_running(self):
        first = Mock(name="first_definition")
        first.name = "same"
        second = Mock(name="second_definition")
        second.name = "same"
        with self.assertRaises(ValueError):
            run_validations([first, second], suite_directory=self.suite_directory)
        with self.assertRaises(ValueError):
            run_validations(
                [first],
                batch_parameters={"missing": {}},
                suite_directory=self.suite_directory,
            )
        with self.assertRaises(ValueError):
            run_validations(
                [first],
                expectation_parameters={"missing": {}},
                suite_directory=self.suite_directory,
            )
        first.run.assert_not_called()
        second.run.assert_not_called()

    def test_runner_propagates_execution_errors_and_preserves_explicit_run_id(self):
        definition = Mock()
        definition.name = "fails"
        definition.suite = gx.ExpectationSuite(name="record_before_error")
        definition.run.side_effect = RuntimeError("connection unavailable")
        later = Mock()
        later.name = "later"
        identifier = RunIdentifier(run_name="explicit")
        with self.assertRaisesRegex(RuntimeError, "connection unavailable"):
            run_validations(
                [definition, later],
                run_id=identifier,
                result_format="BASIC",
                suite_directory=self.suite_directory,
            )
        self.assertIs(definition.run.call_args.kwargs["run_id"], identifier)
        self.assertEqual(definition.run.call_args.kwargs["result_format"], "BASIC")
        later.run.assert_not_called()
        self.assertEqual(run_validations([], suite_directory=self.suite_directory), {})

    def test_runner_passes_expectation_parameters_per_definition(self):
        definition = Mock()
        definition.name = "one"
        definition.suite = gx.ExpectationSuite(name="parameterized")
        run_validations(
            [definition],
            expectation_parameters={"one": {"minimum": 5}},
            suite_directory=self.suite_directory,
        )
        self.assertEqual(definition.run.call_args.kwargs["expectation_parameters"], {"minimum": 5})

    def test_suite_snapshot_rejects_overwrite_and_preserves_builder_values(self):
        suite = flow_account_suite(expected_row_count=7)
        path = self.suite_directory / "source.suite.json"
        self.assertEqual(save_suite(suite, path), path)
        saved = json.loads(path.read_text())
        count_check = next(
            e for e in saved["expectations"] if e["type"] == "expect_table_row_count_to_equal"
        )
        self.assertEqual(count_check["kwargs"]["value"], 7)
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            save_suite(flow_account_suite(expected_row_count=1), path)
        self.assertEqual(path.read_bytes(), original)

    def test_suite_write_failure_prevents_validation_execution(self):
        definition = Mock()
        definition.name = "blocked"
        definition.suite = gx.ExpectationSuite(name="blocked")
        self.suite_directory.mkdir(parents=True)
        (self.suite_directory / "000_blocked.suite.json").write_text("existing audit")
        with self.assertRaises(FileExistsError):
            run_validations([definition], suite_directory=self.suite_directory)
        definition.run.assert_not_called()

    def test_duckdb_adapter_rejects_other_backends(self):
        backend = Mock()
        backend.name = "pyspark"
        with self.assertRaises(ValueError):
            prepare_duckdb(None, None, backend, None, None, name="wrong_backend")
        backend.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
