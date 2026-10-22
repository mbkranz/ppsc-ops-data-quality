"""SCD2 semantics and snapshot-to-expectation integration, without AWS writes."""

import unittest
from datetime import UTC, date, datetime
from unittest.mock import Mock

import ibis
import pyarrow as pa
import sqlglot
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    flow_account_query,
    rollup_account_query,
)
from ppsc_ops_data_quality.core.queries.snapshot import snapshot
from ppsc_ops_data_quality.gx_queries import query_asset_sql
from ppsc_ops_data_quality.runtime.data_access import bind_history_tables
from ppsc_ops_data_quality.views import create_view, create_view_sql


def object_history_schemas():
    """Use the shared source profiles instead of duplicating fixture dtypes."""
    from ppsc_ops_data_quality.core.schemas import (
        ACCOUNT_HISTORY_VALIDATION_INPUT,
        CONTACT_HISTORY_VALIDATION_INPUT,
        SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
    )

    return {
        "Account": ACCOUNT_HISTORY_VALIDATION_INPUT,
        "Contact": CONTACT_HISTORY_VALIDATION_INPUT,
        "Survey_Result__c": SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
    }


def example_queries():
    history = {
        name: ibis.table(schema, name="history", database=database)
        for (name, schema), database in zip(
            object_history_schemas().items(),
            ["example_account", "example_contact", "example_survey_result"],
            strict=True,
        )
    }
    return {
        "flow": flow_account_query(
            history,
            survey_result_id="EXAMPLE_VERIFIED_SURVEY_EVENT",
            account_before_at=datetime(2026, 10, 21, 11, 59, 59),
            execution_at=datetime(2026, 10, 21, 12),
            account_after_at=datetime(2026, 10, 21, 12, 5),
            flow_run_date=date(2026, 10, 21),
        ),
        "rollup": rollup_account_query(history, as_of=datetime(2026, 10, 21, 12)),
    }


class SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = ibis.duckdb.connect()

    def history(self):
        return ibis.memtable(
            [
                {
                    "Id": "a",
                    "valid_from": date(2026, 1, 1),
                    "valid_to": date(2026, 2, 1),
                    "is_current": False,
                },
                {
                    "Id": "a",
                    "valid_from": date(2026, 2, 1),
                    "valid_to": None,
                    "is_current": True,
                },
                {
                    "Id": "duplicate",
                    "valid_from": date(2026, 1, 1),
                    "valid_to": None,
                    "is_current": True,
                },
                {
                    "Id": "duplicate",
                    "valid_from": date(2026, 1, 1),
                    "valid_to": None,
                    "is_current": True,
                },
                {
                    "Id": "unknown_start",
                    "valid_from": None,
                    "valid_to": None,
                    "is_current": None,
                },
                {
                    "Id": "future",
                    "valid_from": date(2027, 1, 1),
                    "valid_to": None,
                    "is_current": True,
                },
            ],
            schema={
                "Id": "string",
                "valid_from": "date",
                "valid_to": "date",
                "is_current": "boolean",
            },
        )

    def test_current_uses_flag_and_retains_duplicates(self):
        result = self.con.execute(snapshot(self.history()))
        self.assertCountEqual(result.Id, ["a", "duplicate", "duplicate", "future"])

    def test_half_open_boundary_and_unknown_start(self):
        query = snapshot(self.history(), as_of=date(2026, 2, 1))
        result = self.con.execute(query)
        self.assertCountEqual(result.Id, ["a", "duplicate", "duplicate"])
        self.assertEqual(result[result.Id == "a"].iloc[0].valid_from.date(), date(2026, 2, 1))
        self.assertEqual(query.schema(), self.history().schema())

    def test_timestamp_precision_and_midnight_date(self):
        history = ibis.memtable(
            [
                {
                    "Id": "a",
                    "valid_from": datetime(2026, 2, 1, 12),
                    "valid_to": datetime(2026, 2, 1, 13),
                },
                {"Id": "a", "valid_from": datetime(2026, 2, 1, 13), "valid_to": None},
            ],
            schema={"Id": "string", "valid_from": "timestamp", "valid_to": "timestamp"},
        )
        at_boundary = self.con.execute(snapshot(history, as_of=datetime(2026, 2, 1, 13)))
        self.assertEqual(len(at_boundary), 1)
        self.assertEqual(at_boundary.iloc[0].valid_from.hour, 13)
        at_midnight = self.con.execute(snapshot(history, as_of=date(2026, 2, 1)))
        self.assertEqual(len(at_midnight), 0)

    def test_explicit_column_mapping(self):
        history = self.history().rename(start="valid_from", end="valid_to", current="is_current")
        query = snapshot(
            history,
            valid_from="start",
            valid_to="end",
            as_of=date(2026, 2, 1),
        )
        self.assertEqual(len(self.con.execute(query)), 3)
        self.assertEqual(
            len(self.con.execute(snapshot(history, is_current="current"))),
            4,
        )

    def test_invalid_temporal_types_fail_explicitly(self):
        with self.assertRaises(TypeError):
            snapshot(self.history(), as_of=datetime(2026, 2, 1))
        with self.assertRaises(TypeError):
            snapshot(self.history(), as_of="2026-02-01")
        with self.assertRaises(ValueError):
            snapshot(self.history().drop("is_current"))
        with self.assertRaises(ValueError):
            snapshot(
                self.history().mutate(valid_to=ibis.timestamp("2026-01-01")),
                as_of=date(2026, 2, 1),
            )
        history = ibis.table({"valid_from": "timestamp", "valid_to": "timestamp"}, name="history")
        with self.assertRaises(ValueError):
            snapshot(history, as_of=datetime(2026, 2, 1, tzinfo=UTC))

    def test_zoned_timestamp_literal_compiles(self):
        history = ibis.table(
            {"valid_from": "timestamp('UTC')", "valid_to": "timestamp('UTC')"},
            name="history",
        )
        sql = query_asset_sql(snapshot(history, as_of=datetime(2026, 2, 1, tzinfo=UTC)))
        sqlglot.parse_one(sql, read="athena")
        with self.assertRaises(ValueError):
            snapshot(history, as_of=datetime(2026, 2, 1))

    def test_optional_view_definition_is_independent(self):
        history = ibis.table(self.history().schema(), name="history", database="account_source")
        query = snapshot(history)
        ddl = sqlglot.parse_one(
            create_view_sql(query, name="account_state", database="quality"),
            read="athena",
        )
        self.assertIsInstance(ddl, exp.Create)
        self.assertEqual(ddl.this.name, "account_state")
        self.assertEqual(ddl.this.db, "quality")
        self.assertIn('"account_source"."history"', create_view_sql(query, name="account_state"))
        with self.assertRaises(ValueError):
            create_view_sql(query, name='state"invalid')

    def test_queries_read_history_without_catalog_views(self):
        for name, comparison in example_queries().items():
            sql = query_asset_sql(comparison)
            ast = sqlglot.parse_one(sql, read="athena")
            ctes = {cte.alias_or_name for cte in ast.find_all(exp.CTE)}
            sources = {
                (table.db, table.name)
                for table in ast.find_all(exp.Table)
                if table.name not in ctes
            }
            expected_sources = {
                ("example_account", "history"),
                ("example_survey_result", "history"),
            }
            if name == "flow":
                expected_sources.add(("example_contact", "history"))
                self.assertIn("EXAMPLE_VERIFIED_SURVEY_EVENT", sql)
                for stamp in ["11:59:59", "12:00:00", "12:05:00"]:
                    self.assertIn(stamp, sql)
            self.assertEqual(sources, expected_sources)
            self.assertRegex(sql, r"^SELECT\s")
            self.assertFalse(sql.endswith(";"))

    def test_comparisons_execute_directly_over_history_sources(self):
        con = ibis.duckdb.connect()
        schemas = object_history_schemas()
        before_time = datetime(2026, 10, 21, 11, 59, 59)
        execution_time = datetime(2026, 10, 21, 12)
        after_time = datetime(2026, 10, 21, 12, 5)
        start = datetime(2026, 1, 1)
        account = {key: None for key in schemas["Account"]}
        account.update(
            Id="a1",
            PersonContactId="c1",
            IsPersonAccount=True,
            valid_from=start,
            valid_to=after_time,
            is_current=False,
        )
        account_after = dict(
            account,
            valid_from=after_time,
            valid_to=None,
            is_current=True,
            Basics_Date_Time__c=execution_time,
        )
        contact = {
            "Id": "c1",
            "AccountId": "a1",
            "Birthdate": date(2000, 1, 1),
            "valid_from": start,
            "valid_to": None,
            "is_current": True,
        }
        survey = {key: None for key in schemas["Survey_Result__c"]}
        survey.update(
            Id="r1",
            Participant__c="c1",
            Survey_Index_Number__c="2001",
            Completion_Status__c="Complete",
            Consent_Status__c="Yes",
            Consent_Revoked__c=False,
            Completion_Status_Timestamp__c=execution_time,
            valid_from=execution_time,
            valid_to=None,
            is_current=True,
        )
        history = {}
        for name, rows in [
            ("Account", [account, account_after]),
            ("Contact", [contact]),
            ("Survey_Result__c", [survey]),
        ]:
            relation = con.create_table(
                name + "_history",
                ibis.memtable(
                    pa.Table.from_pylist(rows, schema=schemas[name].to_pyarrow()),
                    schema=schemas[name],
                ),
            )
            history[name] = relation
        flow = con.execute(
            flow_account_query(
                history,
                survey_result_id="r1",
                account_before_at=before_time,
                execution_at=execution_time,
                account_after_at=after_time,
                flow_run_date=date(2026, 10, 21),
            )
        )
        self.assertEqual(len(flow), 1)
        self.assertEqual(flow.iloc[0]["expected__Basics_Date_Time__c"], execution_time)
        self.assertEqual(flow.iloc[0]["observed__Basics_Date_Time__c"], execution_time)
        rollups = con.execute(rollup_account_query(history, as_of=execution_time))
        self.assertEqual(rollups.iloc[0]["expected__PP1_Basics_Survey_Complete__pc"], 1)
        con.disconnect()

    def test_binds_real_history_tables(self):
        backend = Mock()
        bind_history_tables(
            backend,
            account_database="a",
            contact_database="c",
            survey_result_database="s",
        )
        self.assertEqual([call.args for call in backend.table.call_args_list], [("history",)] * 3)
        self.assertEqual(
            [call.kwargs["database"] for call in backend.table.call_args_list],
            ["a", "c", "s"],
        )

    def test_optional_publishing_executes_only_on_explicit_call(self):
        connection = Mock()
        query = self.history()
        table = create_view(connection, query, name="published_comparison", database="quality")
        connection.cursor.return_value.execute.assert_called_once_with(
            create_view_sql(query, name="published_comparison", database="quality")
        )
        connection.cursor.return_value.close.assert_called_once()
        self.assertEqual(table.schema(), query.schema())
        connection.cursor.return_value.execute.side_effect = RuntimeError("Athena failure")
        with self.assertRaises(RuntimeError):
            create_view(connection, query, name="published_comparison")
        self.assertEqual(connection.cursor.return_value.close.call_count, 2)

    def test_flow_requires_explicit_ordered_temporal_bindings(self):
        args = dict(
            survey_result_id="r1",
            account_before_at=datetime(2026, 10, 21, 11),
            execution_at=datetime(2026, 10, 21, 12),
            account_after_at=datetime(2026, 10, 21, 13),
            flow_run_date=date(2026, 10, 21),
        )
        for replacements, error in [
            ({"account_before_at": None}, TypeError),
            ({"account_before_at": args["execution_at"]}, ValueError),
            ({"account_after_at": args["account_before_at"]}, ValueError),
            ({"execution_at": date(2026, 10, 21)}, ValueError),
            ({"survey_result_id": ""}, ValueError),
        ]:
            with self.subTest(replacements=replacements), self.assertRaises(error):
                flow_account_query({}, **{**args, **replacements})


if __name__ == "__main__":
    unittest.main()
