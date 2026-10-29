"""SCD2 semantics and snapshot-to-expectation integration, without AWS writes."""

import unittest
from datetime import UTC, date, datetime

import ibis
import sqlglot

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    flow_account_query,
    snapshot,
    to_sqlglot,
)
from ppsc_ops_data_quality.runtime import query_asset_sql


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
        sql = query_asset_sql(to_sqlglot(snapshot(history, as_of=datetime(2026, 2, 1, tzinfo=UTC))))
        sqlglot.parse_one(sql, read="athena")
        with self.assertRaises(ValueError):
            snapshot(history, as_of=datetime(2026, 2, 1))

    def test_flow_requires_explicit_ordered_temporal_bindings(self):
        args = dict(
            survey_result_id="r1",
            eligibility=True,
            inputs={},
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
