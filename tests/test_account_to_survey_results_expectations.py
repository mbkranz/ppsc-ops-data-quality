import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import great_expectations as gx
import great_expectations.expectations as gxe
import ibis
import pandas as pd
import sqlalchemy as sa

from ppsc_ops_data_quality.account_to_survey_results import gx as checks
from ppsc_ops_data_quality.account_to_survey_results import queries
from ppsc_ops_data_quality.account_to_survey_results import queries as derivations

OLD = dt.datetime(2001, 1, 1)
NEW = dt.datetime(2025, 1, 1)


def flow_inputs(*, completion_timestamp=NEW):
    survey = ibis.memtable(
        [
            {
                "Id": "s1",
                "Participant__c": "c1",
                "Survey_Index_Number__c": "2001",
                "Completion_Status__c": "Complete",
                "Consent_Status__c": "Yes",
                "Completion_Status_Timestamp__c": completion_timestamp,
                "Consent_Status_Timestamp__c": NEW,
                "California_Signature__c": None,
            }
        ],
        schema={
            "Id": "string",
            "Participant__c": "string",
            "Survey_Index_Number__c": "string",
            "Completion_Status__c": "string",
            "Consent_Status__c": "string",
            "Completion_Status_Timestamp__c": "timestamp",
            "Consent_Status_Timestamp__c": "timestamp",
            "California_Signature__c": "timestamp",
        },
    )
    account_schema = {
        "Id": "string",
        **{
            f: "float64" if f == "Age_at_Time_of_Consent__pc" else "timestamp"
            for f in checks.ACCOUNT_FIELDS_ASSIGNED_BY_FLOW
        },
    }
    baseline = {
        "Id": "a1",
        **{
            f: 22.0 if f == "Age_at_Time_of_Consent__pc" else OLD
            for f in checks.ACCOUNT_FIELDS_ASSIGNED_BY_FLOW
        },
    }
    before = ibis.memtable([baseline], schema=account_schema)
    # Independently declared observed result for a Basics event.
    after = ibis.memtable(
        [{**baseline, "Basics_Date_Time__c": completion_timestamp, "survey_result_id": "s1"}],
        schema={**account_schema, "survey_result_id": "string"},
    )
    contact = ibis.memtable(
        [{"Id": "c1", "AccountId": "a1", "Birthdate": dt.date(2000, 1, 1)}],
        schema={"Id": "string", "AccountId": "string", "Birthdate": "date"},
    )
    record = derivations.add_flow_context(
        derivations.join_account(survey, contact, before),
        survey,
        flow_run_date=ibis.date("2026-10-21"),
    )
    return derivations.expected_account_values(record), after


class BuiltInExpectations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = gx.get_context(mode="ephemeral")
        cls.context.variables.progress_bars = {"globally": False}
        ds = cls.context.data_sources.add_pandas(name="local_comparisons")
        cls.batch_definition = ds.add_dataframe_asset(
            name="comparison"
        ).add_batch_definition_whole_dataframe("whole")
        cls.ibis_backend = ibis.duckdb.connect()
        expected, after = flow_inputs()
        cls.flow_frame = cls.ibis_backend.execute(queries.flow_account_comparison(expected, after))

    @classmethod
    def tearDownClass(cls):
        cls.ibis_backend.disconnect()

    def validate(self, frame, suite):
        batch = self.batch_definition.get_batch(batch_parameters={"dataframe": frame})
        result = batch.validate(suite, result_format="BASIC")
        for expectation_result in result.results:
            self.assertFalse(
                expectation_result.exception_info.get("raised_exception", False),
                expectation_result.exception_info,
            )
        return result

    @staticmethod
    def failed_checks(result):
        return {r.expectation_config.meta["check_id"] for r in result.results if not r.success}

    def test_valid_flow_passes_with_builtin_classes_only(self):
        suite = checks.flow_account_suite(expected_row_count=1)
        self.assertEqual(len(suite.expectations), 28)
        self.assertTrue(
            all(
                type(e).__module__.startswith("great_expectations.expectations.core")
                for e in suite.expectations
            )
        )
        self.assertTrue(self.validate(self.flow_frame, suite).success)

    def test_wrong_value_fails_its_named_pair(self):
        frame = self.flow_frame.copy()
        frame.loc[0, "observed__Basics_Date_Time__c"] = OLD
        failed = self.failed_checks(self.validate(frame, checks.flow_account_suite()))
        self.assertEqual(failed, {"observed_Basics_Date_Time__c_equals_expected"})

    def test_launch_boundary_preserves_rows_and_scopes_flow_checks(self):
        for timestamp, eligible in [
            (dt.datetime(2024, 12, 15, 23, 59, 59), False),
            (dt.datetime(2024, 12, 16), True),
            (dt.datetime(2024, 12, 16, 23, 59, 59), True),
            (NEW, True),
            (None, None),
        ]:
            with self.subTest(timestamp=timestamp):
                expected, after = flow_inputs(completion_timestamp=timestamp)
                frame = self.ibis_backend.execute(queries.flow_account_comparison(expected, after))
                self.assertEqual(len(frame), 1)  # No input filtering, including NULL timestamps.
                scope = frame.loc[0, "survey_completion_occurred_on_or_after_launch"]
                if eligible is None:
                    self.assertTrue(pd.isna(scope))
                else:
                    self.assertEqual(scope, eligible)
                frame["observed__Basics_Date_Time__c"] = OLD
                frame["observed_account_id"] = None
                frame["cabor_lookup_is_deterministic"] = False
                result = self.validate(
                    frame, checks.flow_account_suite(expected_row_count=int(bool(eligible)))
                )
                if eligible:
                    self.assertEqual(
                        self.failed_checks(result),
                        {
                            "observed_Basics_Date_Time__c_equals_expected",
                            "flow_observed_account_id_is_present",
                            "permission_lookup_is_deterministic",
                        },
                    )
                else:
                    self.assertTrue(result.success)

    def test_every_flow_row_expectation_has_launch_scope_after_serialization(self):
        suite_json = checks.flow_account_suite(expected_row_count=1).to_json_dict()
        restored = gx.ExpectationSuite(**json.loads(json.dumps(suite_json)))
        serialized = restored.to_json_dict()["expectations"]
        for expectation in serialized:
            if expectation["type"] == "expect_table_columns_to_match_set":
                continue
            condition = expectation["kwargs"]["row_condition"]
            self.assertIn("survey_completion_occurred_on_or_after_launch", json.dumps(condition))
        cabor = next(
            e
            for e in serialized
            if e["meta"]["check_id"] == "observed_CABOR_Completion_Date__c_equals_expected"
        )
        self.assertIn("cabor_lookup_is_deterministic", json.dumps(cabor["kwargs"]["row_condition"]))

    def test_both_null_allowed_and_one_sided_null_fails(self):
        for expected, observed, success in [
            (None, None, True),
            (None, 22.0, False),
            (22.0, None, False),
        ]:
            with self.subTest(expected=expected, observed=observed):
                frame = self.flow_frame.copy()
                frame["expected__Age_at_Time_of_Consent__pc"] = expected
                frame["observed__Age_at_Time_of_Consent__pc"] = observed
                self.assertEqual(self.validate(frame, checks.flow_account_suite()).success, success)

    def test_missing_parent_and_observed_account_are_failures(self):
        for column in [
            "participant_contact_id",
            "expected_account_id",
            "observed_account_id",
        ]:
            with self.subTest(column=column):
                frame = self.flow_frame.copy()
                frame[column] = None
                result = self.validate(frame, checks.flow_account_suite())
                self.assertIn(f"flow_{column}_is_present", self.failed_checks(result))

    def test_duplicate_event_is_failure_and_repeated_account_is_valid(self):
        frame = pd.concat([self.flow_frame, self.flow_frame], ignore_index=True)
        result = self.validate(frame, checks.flow_account_suite())
        self.assertIn("one_comparison_row_per_survey_event", self.failed_checks(result))
        frame.loc[1, "survey_result_id"] = "s2"
        self.assertTrue(self.validate(frame, checks.flow_account_suite()).success)

    def test_ambiguous_lookup_fails_resolution_not_an_invented_value(self):
        frame = self.flow_frame.copy()
        frame["cabor_lookup_is_deterministic"] = False
        frame["expected__CABOR_Completion_Date__c"] = pd.NaT
        result = self.validate(frame, checks.flow_account_suite())
        self.assertEqual(self.failed_checks(result), {"permission_lookup_is_deterministic"})
        frame["cabor_lookup_is_deterministic"] = None
        result = self.validate(frame, checks.flow_account_suite())
        self.assertIn(
            "permission_lookup_resolution_evidence_is_present",
            self.failed_checks(result),
        )

    def test_event_identity_join_retains_wrong_or_missing_observations(self):
        expected, after = flow_inputs()
        after = after.mutate(survey_result_id=ibis.literal("another_event"))
        frame = self.ibis_backend.execute(queries.flow_account_comparison(expected, after))
        self.assertEqual(len(frame), 1)
        self.assertTrue(frame.observed_account_id.isna().all())
        result = self.validate(frame, checks.flow_account_suite())
        self.assertIn("flow_observed_account_id_is_present", self.failed_checks(result))

    def test_duplicate_observed_rows_are_not_deduplicated(self):
        expected, after = flow_inputs()
        frame = self.ibis_backend.execute(
            queries.flow_account_comparison(expected, after.union(after))
        )
        self.assertEqual(len(frame), 2)
        self.assertIn(
            "one_comparison_row_per_survey_event",
            self.failed_checks(self.validate(frame, checks.flow_account_suite())),
        )

    def test_rollup_comparison_and_zero_children(self):
        account = ibis.memtable(
            {
                "Id": ["a1", "a2"],
                "PersonContactId": ["c1", "c2"],
                "IsPersonAccount": [True, True],
            }
        )
        survey = ibis.memtable(
            {
                "Participant__c": ["c1"],
                "Completion_Status__c": ["Complete"],
                "Consent_Status__c": ["Yes"],
                "Survey_Index_Number__c": ["1001"],
                "Consent_Revoked__c": [False],
            }
        )
        expected = derivations.expected_survey_rollups(account, survey)
        observed = ibis.memtable(
            [
                {
                    "Id": "a1",
                    **{
                        f: 1 if f == "Count_of_Completed_Primary_Consent__pc" else 0
                        for f in checks.ROLLUP_ACCOUNT_FIELDS
                    },
                },
                {"Id": "a2", **{f: 0 for f in checks.ROLLUP_ACCOUNT_FIELDS}},
            ],
        )
        frame = self.ibis_backend.execute(queries.rollup_account_comparison(expected, observed))
        self.assertTrue(
            self.validate(frame, checks.rollup_account_suite(expected_row_count=2)).success
        )
        frame.loc[
            frame.expected_account_id == "a2",
            "observed__Count_of_Completed_Primary_Consent__pc",
        ] = 1
        failed = self.failed_checks(self.validate(frame, checks.rollup_account_suite()))
        self.assertEqual(
            failed,
            {"observed_Count_of_Completed_Primary_Consent__pc_equals_expected_rollup"},
        )

    def test_suites_round_trip_json_and_carry_original_lineage(self):
        for suite in [checks.flow_account_suite(), checks.rollup_account_suite()]:
            restored = gx.ExpectationSuite(**json.loads(json.dumps(suite.to_json_dict())))
            self.assertEqual(len(restored.expectations), len(suite.expectations))
        pair = next(
            e
            for e in checks.flow_account_suite().expectations
            if e.meta["check_id"] == "observed_Basics_Date_Time__c_equals_expected"
        )
        self.assertEqual(
            pair.meta["ppsc"]["source_entities"], ["FlowRecordUpdate.updateAccount2001"]
        )
        self.assertEqual(pair.ignore_row_if, "both_values_are_missing")

    def test_independent_expected_row_count(self):
        result = self.validate(self.flow_frame, checks.flow_account_suite(expected_row_count=2))
        self.assertEqual(self.failed_checks(result), {"flow_comparison_row_count_matches_source"})

    def test_empty_batch_requires_an_explicit_nonempty_contract_to_fail(self):
        empty = self.flow_frame.iloc[0:0].copy()
        self.assertTrue(self.validate(empty, checks.flow_account_suite()).success)
        result = self.validate(empty, checks.flow_account_suite(expected_row_count=1))
        self.assertEqual(self.failed_checks(result), {"flow_comparison_row_count_matches_source"})

    def test_sqlalchemy_pair_null_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            url = "sqlite:///" + str(Path(tmp) / "nulls.sqlite")
            engine = sa.create_engine(url)
            pd.DataFrame({"a": [None, None, 1, 1], "b": [None, 1, None, 1]}).to_sql(
                "pairs", engine, index=False
            )
            engine.dispose()
            ds = self.context.data_sources.add_sql(
                name="sql_nulls", connection_string=url, create_temp_table=False
            )
            batch = (
                ds.add_table_asset(name="pairs", table_name="pairs")
                .add_batch_definition_whole_table("whole")
                .get_batch()
            )
            result = batch.validate(
                gxe.ExpectColumnPairValuesToBeEqual(
                    column_A="a", column_B="b", ignore_row_if="both_values_are_missing"
                )
            )
            self.assertFalse(result.exception_info["raised_exception"])
            self.assertEqual(result.result["missing_count"], 1)
            self.assertEqual(result.result["unexpected_count"], 2)

    def test_full_flow_suite_on_sqlalchemy(self):
        with tempfile.TemporaryDirectory() as tmp:
            url = "sqlite:///" + str(Path(tmp) / "flow.sqlite")
            engine = sa.create_engine(url)
            expected, after = flow_inputs(completion_timestamp=dt.datetime(2024, 12, 15))
            prelaunch = self.ibis_backend.execute(queries.flow_account_comparison(expected, after))
            prelaunch["observed_account_id"] = None
            prelaunch["observed__Basics_Date_Time__c"] = OLD
            prelaunch["cabor_lookup_is_deterministic"] = False
            pd.concat([self.flow_frame, prelaunch], ignore_index=True).to_sql(
                "comparison", engine, index=False
            )
            engine.dispose()
            ds = self.context.data_sources.add_sql(
                name="sql_flow", connection_string=url, create_temp_table=False
            )
            batch = (
                ds.add_table_asset(name="comparison", table_name="comparison")
                .add_batch_definition_whole_table("whole")
                .get_batch()
            )
            result = batch.validate(checks.flow_account_suite(expected_row_count=1))
            for item in result.results:
                self.assertFalse(
                    item.exception_info.get("raised_exception", False),
                    item.exception_info,
                )
            self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main(verbosity=2)
