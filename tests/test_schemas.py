"""Source metadata types, interchange, actual expression coverage and overrides."""

import unittest
from datetime import date, datetime
from decimal import Decimal

import ibis
import pandas as pd
import pyarrow as pa
import sqlglot
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results import schemas as derived
from ppsc_ops_data_quality.account_to_survey_results.gx import (
    flow_account_suite,
    rollup_account_suite,
)
from ppsc_ops_data_quality.account_to_survey_results.metadata import metadata_inputs
from ppsc_ops_data_quality.account_to_survey_results.queries import (
    flow_account_query,
    rollup_account_query,
)
from ppsc_ops_data_quality.core.queries import history_tables
from ppsc_ops_data_quality.core.queries.snapshot import snapshot
from ppsc_ops_data_quality.core.schemas import (
    ACCOUNT_HISTORY_VALIDATION_INPUT,
    ACCOUNT_VALIDATION_INPUT,
    CONTACT_HISTORY_VALIDATION_INPUT,
    CONTACT_VALIDATION_INPUT,
    SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
    SURVEY_RESULT_VALIDATION_INPUT,
)
from ppsc_ops_data_quality.gx_queries import query_asset_sql
from ppsc_ops_data_quality.views import create_view_sql

SOURCE_SCHEMAS = (
    ACCOUNT_VALIDATION_INPUT,
    ACCOUNT_HISTORY_VALIDATION_INPUT,
    CONTACT_VALIDATION_INPUT,
    CONTACT_HISTORY_VALIDATION_INPUT,
    SURVEY_RESULT_VALIDATION_INPUT,
    SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
)


class SchemaTests(unittest.TestCase):
    def test_explicit_types_follow_field_definitions_and_keep_raw_nulls(self):
        # Workbook datamodel-Fields row 407: Number(3,0), not a floating-point age.
        self.assertEqual(
            ACCOUNT_VALIDATION_INPUT["Age_at_Time_of_Consent__pc"],
            ibis.dtype("decimal(3,0)"),
        )
        # Rows 442+ COUNT fields are modeled as integers, not booleans.
        self.assertEqual(ACCOUNT_VALIDATION_INPUT["EHR_Authorized__pc"], ibis.dtype("int64"))
        # Survey index is Text(255), despite looking numeric (row 1775).
        self.assertTrue(SURVEY_RESULT_VALIDATION_INPUT["Survey_Index_Number__c"].is_string())
        self.assertTrue(CONTACT_VALIDATION_INPUT["Birthdate"].is_date())
        for schema in SOURCE_SCHEMAS:
            self.assertTrue(all(dtype.nullable for dtype in schema.types))

    def test_source_schemas_interoperate_with_arrow_and_athena_column_definitions(self):
        for schema in SOURCE_SCHEMAS:
            arrow_schema = schema.to_pyarrow()
            self.assertEqual(arrow_schema.names, list(schema.names))
            converted = ibis.Schema.from_pyarrow(arrow_schema)
            self.assertEqual(converted.names, schema.names)
            self.assertEqual(converted.to_pyarrow(), arrow_schema)
            columns = schema.to_sqlglot_column_defs(dialect="athena")
            converted_sql = ibis.Schema.from_sqlglot(
                exp.Schema(expressions=columns), dialect="athena"
            )
            self.assertEqual(converted_sql.names, schema.names)
        self.assertEqual(
            ACCOUNT_VALIDATION_INPUT.to_pyarrow().field("Age_at_Time_of_Consent__pc").type,
            pa.decimal128(3, 0),
        )

    def test_snapshot_profiles_preserve_all_declared_fields(self):
        history = history_tables(inputs=metadata_inputs())
        for relation in history.values():
            for point in [None, datetime(2026, 10, 21, 12)]:
                self.assertEqual(snapshot(relation, as_of=point).schema(), relation.schema())
        self.assertIn("loaded_at", history["Account"].columns)

    def test_declared_sources_build_complete_comparisons_and_optional_views(self):
        history = history_tables(inputs=metadata_inputs())
        flow = flow_account_query(
            history,
            survey_result_id="r1",
            account_before_at=datetime(2026, 10, 21, 11),
            execution_at=datetime(2026, 10, 21, 12),
            account_after_at=datetime(2026, 10, 21, 13),
            flow_run_date=date(2026, 10, 21),
        )
        rollups = rollup_account_query(history, as_of=datetime(2026, 10, 21, 12))
        self.assertEqual(flow.schema(), derived.FLOW_ACCOUNT_COMPARISON)
        self.assertEqual(rollups.schema(), derived.ROLLUP_ACCOUNT_COMPARISON)
        for query, suite in [
            (flow, flow_account_suite()),
            (rollups, rollup_account_suite()),
        ]:
            for expectation in suite.expectations:
                for attribute in ["column", "column_A", "column_B"]:
                    column = getattr(expectation, attribute, None)
                    if column:
                        self.assertIn(column, query.columns)
                if hasattr(expectation, "column_set"):
                    self.assertTrue(set(expectation.column_set).issubset(query.columns))
            sqlglot.parse_one(query_asset_sql(query), read="athena")
            sqlglot.parse_one(create_view_sql(query, name="comparison"), read="athena")

    def test_inadequate_date_history_is_retained_in_explicit_query_inputs(self):
        # A prepared relation may expose date-grained history; runtime refuses to
        # certify intra-day Flow equivalence from that weaker evidence.
        account_schema = ibis.schema(
            {
                **ACCOUNT_HISTORY_VALIDATION_INPUT.fields,
                "valid_from": "date",
                "valid_to": "date",
                "ingestion_partition": "string",
            }
        )
        account = ibis.table(account_schema, name="reviewed_date_delivery")
        self.assertEqual(snapshot(account, as_of=date(2026, 10, 21)).schema(), account_schema)
        self.assertIn("ingestion_partition", account.columns)

    def test_decimal_source_values_and_missing_identifiers_survive_execution(self):
        rows = [{name: None for name in ACCOUNT_VALIDATION_INPUT}]
        rows[0]["Age_at_Time_of_Consent__pc"] = Decimal("26")
        table = ibis.memtable(rows, schema=ACCOUNT_VALIDATION_INPUT)
        backend = ibis.duckdb.connect()
        result = backend.execute(table)
        self.assertEqual(result.iloc[0]["Age_at_Time_of_Consent__pc"], Decimal("26"))
        self.assertTrue(pd.isna(result.iloc[0]["Id"]))
        backend.disconnect()


if __name__ == "__main__":
    unittest.main()
