"""Runtime adapters and runner using native GX, DuckDB and SQLAlchemy/SQLite."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import great_expectations as gx
import great_expectations.expectations as gxe
import ibis
from great_expectations.core import RunIdentifier

from ppsc_ops_data_quality.account_to_survey_results.queries import to_sqlglot
from ppsc_ops_data_quality.account_to_survey_results.suites import (
    flow_account_suite,
)
from ppsc_ops_data_quality.runtime import run_validations, save_suite
from scripts.check_validation import prepare_validation as prepare_duckdb


def make_context():
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    return context


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.suite_directory = Path(temporary.name) / "suites"

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
            context,
            source,
            backend,
            to_sqlglot(backend.create_table("bad_rows", ibis.memtable({"value": [0]}))),
            suite,
            name="bad",
        )
        good, good_params = prepare_duckdb(
            context,
            source,
            backend,
            to_sqlglot(backend.create_table("good_rows", ibis.memtable({"value": [1]}))),
            suite,
            name="good",
        )
        results = run_validations(
            [bad, good],
            batch_parameters={"bad": bad_params, "good": good_params},
            suite_directory=self.suite_directory,
        )
        self.assertFalse(results["bad"].success)
        self.assertTrue(results["good"].success)
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


if __name__ == "__main__":
    unittest.main()
