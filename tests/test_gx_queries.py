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
from ppsc_ops_data_quality.account_to_survey_results.queries import flow_account_comparison
from ppsc_ops_data_quality.core.queries.sql import to_sqlglot
from ppsc_ops_data_quality.gx_queries import query_asset_sql, query_batch_definition


class QueryAssetTests(unittest.TestCase):
    def test_compiled_ctes_and_lineage_are_accepted_by_gx(self):
        for name, comparison in example_queries().items():
            sql = query_asset_sql(comparison, projection_lineage=PROJECTION_LINEAGE)
            asset = QueryAsset(name=name, query=sql)
            self.assertEqual(asset.query, sql)
            ast = sqlglot.parse_one(sql, read="athena")
            self.assertIsInstance(ast, exp.Select)
            self.assertIsNotNone(ast.find(exp.Subquery))
            self.assertIn("expected__", sql)
            self.assertIn("observed__", sql)
            self.assertIn("Independently observed Account.", sql)
            annotated = to_sqlglot(comparison, projection_lineage=PROJECTION_LINEAGE)
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
