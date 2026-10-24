"""Native GX Query Asset adapter, including an actual SQLAlchemy validation."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import great_expectations as gx
import ibis
import sqlalchemy as sa
import sqlglot
from great_expectations.datasource.fluent.sql_datasource import QueryAsset
from sqlglot import exp
from test_account_to_survey_results_expectations import flow_inputs
from test_snapshot import example_queries

from ppsc_ops_data_quality.account_to_survey_results.gx import flow_account_suite
from ppsc_ops_data_quality.account_to_survey_results.lineage import PROJECTION_LINEAGE
from ppsc_ops_data_quality.account_to_survey_results.queries import (
    ROLLUP_ACCOUNT_FIELDS,
    flow_account_comparison,
    rollup_account_comparison,
)
from ppsc_ops_data_quality.core.queries.sql import to_sqlglot
from ppsc_ops_data_quality.gx_queries import query_asset_sql, query_batch_definition
from scripts.check_validation import comparisons, render_examples, synthetic_history_tables


class QueryAssetTests(unittest.TestCase):
    def test_compiled_sources_have_descriptive_aliases(self):
        expected_sources = {
            "flow": {"Account", "Contact", "Account_After", "Flow_Context"},
            "rollup": {
                "Person_Account",
                "Survey_Result__c",
                "Account_Snapshot",
            },
        }
        for name, comparison in example_queries().items():
            with self.subTest(name=name):
                query = to_sqlglot(comparison)
                aliases = {node.name for node in query.find_all(exp.TableAlias)}
                self.assertTrue(expected_sources[name] <= aliases)
                for alias in aliases:
                    self.assertNotRegex(alias, r"^t\d+$")
                for column in query.find_all(exp.Column):
                    self.assertNotRegex(column.table, r"^t\d+$")
                self.assertEqual(
                    query.sql(dialect="athena"),
                    to_sqlglot(comparison).sql(dialect="athena"),
                )

    def test_aliases_preserve_self_joins_and_literal_values(self):
        backend = ibis.duckdb.connect()
        try:
            table = backend.create_table(
                "Account", ibis.memtable({"Id": ["a", "b"], "label": ["t1", "t2"]})
            )
            other = table.view()
            expression = table.left_join(other, table.Id == other.Id).select(
                table.Id,
                table.label,
                other.label.name("t3"),
                marker=ibis.literal("t7"),
            )
            query = to_sqlglot(expression)
            actual = backend.raw_sql(query.sql(dialect="duckdb")).fetchall()
            self.assertCountEqual(actual, [("a", "t1", "t1", "t7"), ("b", "t2", "t2", "t7")])
            self.assertEqual(query.named_selects, ["Id", "label", "t3", "marker"])
            self.assertEqual(
                {node.name for node in query.find_all(exp.TableAlias)},
                {"Account", "Account_2"},
            )
        finally:
            backend.disconnect()

    def test_inlining_cte_with_the_same_name_as_its_physical_source(self):
        backend = ibis.duckdb.connect()
        try:
            table = backend.create_table("Account", ibis.memtable({"Id": ["a", "a"]}))
            expression = table.alias("Account").mutate(marker=ibis.literal("Account"))
            query = to_sqlglot(expression)
            self.assertIsNone(query.args.get("with_"))
            self.assertCountEqual(
                backend.raw_sql(query.sql(dialect="duckdb")).fetchall(),
                [("a", "Account"), ("a", "Account")],
            )
        finally:
            backend.disconnect()

    def test_rendered_comparisons_preserve_synthetic_results(self):
        backend = ibis.duckdb.connect()
        try:
            for name, comparison in comparisons(synthetic_history_tables(backend)).items():
                with self.subTest(name=name):
                    original = backend.raw_sql(backend.compile(comparison)).fetchall()
                    rendered = to_sqlglot(comparison).sql(dialect="duckdb")
                    self.assertCountEqual(backend.raw_sql(rendered).fetchall(), original)
        finally:
            backend.disconnect()

    def test_rollup_grouping_preserves_identical_observations_and_missing_parents(self):
        backend = ibis.duckdb.connect()
        try:
            account = backend.create_table(
                "Account",
                ibis.memtable(
                    {
                        "Id": ["a1", "a1", "a2", None],
                        "PersonContactId": ["c1", "c1", "c2", "c3"],
                        "IsPersonAccount": [True, True, True, True],
                    }
                ),
            )
            survey = backend.create_table(
                "Survey",
                ibis.memtable(
                    {
                        "Participant__c": ["c1", "c1", "c3"],
                        "Completion_Status__c": ["Complete"] * 3,
                        "Survey_Index_Number__c": ["1001"] * 3,
                        "Consent_Status__c": ["Yes"] * 3,
                        "Consent_Revoked__c": [False] * 3,
                    }
                ),
            )
            observed = backend.create_table(
                "Observed",
                ibis.memtable(
                    {
                        "Id": ["a1", "a1"],
                        **{field: [0, 0] for field in ROLLUP_ACCOUNT_FIELDS},
                    }
                ),
            )
            comparison = rollup_account_comparison(account, survey, observed)
            self.assertCountEqual(
                backend.raw_sql(
                    backend.compile(
                        comparison.select(
                            "expected_account_id",
                            "person_contact_id",
                            "observed_account_id",
                            "expected__Count_of_Completed_Primary_Consent__pc",
                        )
                    )
                ).fetchall(),
                [
                    ("a1", "c1", "a1", 4),
                    ("a1", "c1", "a1", 4),
                    ("a2", "c2", None, 0),
                    (None, "c3", None, 1),
                ],
            )
            self.assertCountEqual(
                backend.raw_sql(to_sqlglot(comparison).sql(dialect="duckdb")).fetchall(),
                backend.raw_sql(backend.compile(comparison)).fetchall(),
            )
        finally:
            backend.disconnect()

    def test_checked_in_sql_examples_match_builders(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_examples(output)
            for generated in output.glob("*.sql"):
                sql = generated.read_text(encoding="utf-8")
                self.assertEqual(sql, (root / "sql" / generated.name).read_text(encoding="utf-8"))
                queries = sqlglot.parse(sql, read="athena")
                self.assertEqual(len(queries), 2)
                self.assertNotIn("FlowDecision_", sql)
                self.assertNotIn("Survey_Completion_Route", sql)
                for query in queries:
                    for alias in query.find_all(exp.TableAlias):
                        self.assertNotRegex(alias.name, r"^t\d+$")
                    for column in query.find_all(exp.Column):
                        self.assertNotRegex(column.table, r"^t\d+$")

    def test_single_explicit_projection_and_resolved_conditions_are_accepted_by_gx(self):
        for name, comparison in example_queries().items():
            sql = query_asset_sql(comparison, projection_lineage=PROJECTION_LINEAGE)
            asset = QueryAsset(name=name, query=sql)
            self.assertEqual(asset.query, sql)
            self.assertLessEqual(len(sql.encode("utf-8")), 262_144)
            ast = sqlglot.parse_one(sql, read="athena")
            self.assertIsInstance(ast, exp.Select)
            self.assertIsNotNone(ast.find(exp.Subquery))
            self.assertEqual(len(sqlglot.parse(sql, read="athena")), 1)
            self.assertFalse(ast.is_star)
            self.assertIsNone(ast.args.get("with_"))
            self.assertEqual(ast.named_selects, list(comparison.columns))
            expected_projections = [
                p
                for p in ast.selects
                if p.alias_or_name.startswith("expected__")
                and not p.alias_or_name.endswith(("__assigned", "__deterministic", "__complete"))
            ]
            self.assertEqual(len(expected_projections), 19)
            for projection in expected_projections:
                if projection.find(exp.Case) is None:
                    # A window/grain preflight can keep the value CASE in its
                    # input relation. Do not fold it across a window boundary.
                    self.assertIsInstance(projection.unalias(), exp.Column)
                    self.assertIsNotNone(ast.find(exp.Case))
                if name == "rollup":
                    self.assertIsNotNone(ast.find(exp.Sum), projection.sql())
            for projection in ast.selects:
                if projection.alias_or_name.startswith("observed__"):
                    self.assertIsInstance(projection.unalias(), exp.Column)
            self.assertIn("expected__", sql)
            self.assertIn("observed__", sql)
            self.assertIn("Independently observed Account.", sql)
            annotated = to_sqlglot(comparison, projection_lineage=PROJECTION_LINEAGE)
            self.assertEqual(sql, annotated.sql(dialect="athena", pretty=False))
            self.assertEqual(annotated.meta["ppsc"]["unannotated_fields"], [])
            expected = next(
                p for p in annotated.selects if p.alias_or_name.startswith("expected__")
            )
            observed = next(
                p for p in annotated.selects if p.alias_or_name.startswith("observed__")
            )
            self.assertEqual(expected.meta["ppsc"]["comparison_role"], "expected")
            self.assertEqual(observed.meta["ppsc"]["comparison_role"], "observed")
            self.assertNotIn("branches", observed.meta["ppsc"])

    def test_utf8_query_limit_fails_before_registering_an_asset(self):
        source = Mock()
        expression = ibis.table({"Id": "string"}, name="input").mutate(
            note=ibis.literal("é" * 140_000)
        )
        with self.assertRaisesRegex(ValueError, "262144-byte"):
            query_batch_definition(source, expression, name="oversized")
        source.add_query_asset.assert_not_called()

    def test_registration_does_not_fetch_batch_or_create_views(self):
        data_source = Mock()
        query = ibis.table({"Id": "string"}, name="history")
        definition = query_batch_definition(
            data_source, query, name="run_comparison", metadata={"run_id": "run_1"}
        )
        call = data_source.add_query_asset.call_args
        self.assertEqual(call.kwargs["batch_metadata"], {"run_id": "run_1"})
        self.assertRegex(call.kwargs["query"], r"^SELECT\s")
        self.assertNotIn("CREATE VIEW", call.kwargs["query"])
        self.assertIs(
            definition,
            data_source.add_query_asset.return_value.add_batch_definition_whole_table.return_value,
        )
        definition.get_batch.assert_not_called()

    def test_native_query_batch_validates_full_builtin_suite_on_sqlalchemy(self):
        backend = ibis.duckdb.connect()
        expected, after = flow_inputs()
        comparison = flow_account_comparison(expected, after)
        frame = backend.execute(comparison)
        with tempfile.TemporaryDirectory() as directory:
            connection_string = "sqlite:///" + str(Path(directory) / "comparison.db")
            engine = sa.create_engine(connection_string)
            frame.to_sql("comparison_rows", engine, index=False)
            context = gx.get_context(mode="ephemeral")
            context.variables.progress_bars = {"globally": False}
            data_source = context.data_sources.add_sqlite(
                name="sqlite_query_test", connection_string=connection_string
            )
            # The adapter is dialect-specific to Athena. This SELECT-only shape is
            # also executable in SQLite, exercising the real GX QueryAsset path.
            relation = ibis.table(comparison.schema(), name="comparison_rows")
            definition = query_batch_definition(
                data_source,
                relation,
                name="flow_comparison",
                metadata={"run_id": "test"},
            )
            batch = definition.get_batch()
            result = batch.validate(flow_account_suite(expected_row_count=1))
            self.assertTrue(result.success)
            with engine.begin() as connection:
                connection.execute(
                    sa.text('UPDATE comparison_rows SET "observed__Basics_Date_Time__c" = NULL')
                )
            result = definition.get_batch().validate(flow_account_suite(expected_row_count=1))
            self.assertFalse(result.success)
            # Run-specific snapshot parameters belong to the query builder.
            with self.assertRaises(Exception) as caught:
                definition.get_batch(batch_parameters={"as_of": "2026-10-21"})
            self.assertIn("as_of", str(caught.exception))
            engine.dispose()
        backend.disconnect()


if __name__ == "__main__":
    unittest.main()
