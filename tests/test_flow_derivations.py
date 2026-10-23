import datetime as dt
import unittest
from pathlib import Path

import ibis
import sqlglot

from ppsc_ops_data_quality.account_to_survey_results import lineage
from ppsc_ops_data_quality.account_to_survey_results import queries as m
from ppsc_ops_data_quality.core.queries.sql import to_sqlglot

OLD = dt.datetime(2001, 1, 1)
NEW = dt.datetime(2024, 1, 1)
SIGN = dt.datetime(2023, 12, 31)
SCHEMA = {
    "Id": "string",
    "Participant__c": "string",
    "Survey_Index_Number__c": "string",
    "Completion_Status__c": "string",
    "Consent_Status__c": "string",
    "Completion_Status_Timestamp__c": "timestamp",
    "Consent_Status_Timestamp__c": "timestamp",
    "California_Signature__c": "timestamp",
}


def fixtures(
    index="1001",
    status="Complete",
    consent="Yes",
    prior=None,
    earliest=OLD,
    signature=SIGN,
    extra=(),
):
    record = {
        "Id": "r1",
        "Participant__c": "c1",
        "Survey_Index_Number__c": index,
        "Completion_Status__c": status,
        "Consent_Status__c": consent,
        "Completion_Status_Timestamp__c": NEW,
        "Consent_Status_Timestamp__c": NEW,
        "California_Signature__c": signature,
    }
    Trigger = ibis.memtable([record], schema=SCHEMA)
    allrows = [record] + list(extra)
    if prior:
        allrows.append(
            {
                "Id": "prior",
                "Participant__c": "c1",
                "Survey_Index_Number__c": prior,
                "Completion_Status__c": "In-Progress",
                "Consent_Status__c": "Yes",
                "Consent_Status_Timestamp__c": OLD,
                "Completion_Status_Timestamp__c": OLD,
                "California_Signature__c": SIGN,
            }
        )
    All = ibis.memtable([{k: r.get(k) for k in SCHEMA} for r in allrows], schema=SCHEMA)
    schema = {
        "Id": "string",
        **{
            f: "float64" if f == "Age_at_Time_of_Consent__pc" else "timestamp"
            for f in m.ACCOUNT_FIELDS_ASSIGNED_BY_FLOW
        },
    }
    baseline = {
        "Id": "a1",
        **{
            f: 22 if f == "Age_at_Time_of_Consent__pc" else OLD
            for f in m.ACCOUNT_FIELDS_ASSIGNED_BY_FLOW
        },
    }
    baseline["Earliest_Primary_Consent_Date_for_Report__c"] = earliest
    Account = ibis.memtable([baseline], schema=schema)
    Contact = ibis.memtable(
        [{"Id": "c1", "AccountId": "a1", "Birthdate": dt.date(2000, 1, 1)}],
        schema={"Id": "string", "AccountId": "string", "Birthdate": "date"},
    )
    return (Trigger, All, Account, Contact)


def build(*args, **kwargs):
    Trigger, All, Account, Contact = fixtures(*args, **kwargs)
    Record = m.join_account(Trigger, Contact, Account)
    Record = m.add_flow_context(Record, All, flow_run_date=ibis.date("2026-10-21"))
    return m.expected_account_values(Record)


class ExpectedValues(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = ibis.duckdb.connect()

    def row(self, *args, **kwargs):
        return self.con.execute(build(*args, **kwargs)).iloc[0]

    def test_every_simple_update(self):
        for index, field in [
            ("1005", "Update_to_Primary_Consent_Completed__c"),
            ("2001", "Basics_Date_Time__c"),
            ("2002", "Basics_Date_Time__c"),
            ("2003", "Overall_Health_Date_Time__c"),
            ("2004", "Overall_Health_Date_Time__c"),
            ("2005", "Lifestyle_Date_Time__c"),
            ("2006", "Personal_and_Family_History_Complete__c"),
            ("2007", "HC_Access_Date_Time__c"),
            ("2008", "Life_Functioning_Date_Time__c"),
            ("2010", "EH_Date_Time__c"),
            ("2011", "Behavioral_Health_Completion__c"),
            ("2012", "Environmental_Exposures_Date_Time__c"),
            ("2013", "Social_Determinants_of_Health_Completion__c"),
        ]:
            with self.subTest(index=index):
                row = self.row(index)
                self.assertEqual(row[field], NEW)
                for unchanged in set(m.ACCOUNT_FIELDS_ASSIGNED_BY_FLOW) - {
                    field,
                    "Age_at_Time_of_Consent__pc",
                }:
                    self.assertEqual(row[unchanged], OLD)

    def test_primary_branches_and_age(self):
        for index in ["1001", "1002"]:
            row = self.row(index)
            self.assertEqual(row.Earliest_Primary_Consent_Date_for_Report__c, OLD)
            self.assertEqual(row.Latest_Primary_Consent_Date_for_Report__c, NEW)
            self.assertEqual(row.Age_at_Time_of_Consent__pc, 26)
            row = self.row(index, prior="1001")
            self.assertEqual(row.Earliest_Primary_Consent_Date_for_Report__c, NEW)

    def test_ehr_branches_preserve_source_behavior(self):
        for index in ["1003", "1004"]:
            row = self.row(index)
            self.assertEqual(row.EHR_Reconsent_Date_Time__c, NEW)
            self.assertEqual(row.EHR_Consent_Date_Time__c, OLD)
            row = self.row(index, prior="1003")
            self.assertEqual(row.EHR_Consent_Date_Time__c, NEW)
            self.assertEqual(row.EHR_Reconsent_Date_Time__c, OLD)

    def test_assigned_null_not_coalesced(self):
        import pandas as pd

        row = self.row(signature=None)
        self.assertTrue(pd.isna(row.CABOR_Completion_Date__c))
        row = self.row("1008", earliest=None)
        self.assertTrue(pd.isna(row.Earliest_Primary_Consent_Date_for_Report__c))
        self.assertTrue(pd.isna(row.CABOR_Completion_Date__c))
        self.assertTrue(row.CABOR_Completion_Date__c_is_deterministic)

    def test_assent_permission_and_ambiguity(self):
        import pandas as pd

        row = self.row("1008", prior="1007", earliest=None)
        self.assertEqual(row.CABOR_Completion_Date__c, SIGN)
        self.assertEqual(row.Earliest_Primary_Consent_Date_for_Report__c, NEW)
        row = self.row(
            "1008",
            prior="1007",
            earliest=None,
            extra=[
                {
                    "Id": "p2",
                    "Participant__c": "c1",
                    "Survey_Index_Number__c": "1007",
                    "Consent_Status__c": "Yes",
                    "California_Signature__c": NEW,
                }
            ],
        )
        self.assertEqual(row["FlowRecordLookup.Pediatric_Permission_For_Assent.match_count"], 2)
        self.assertFalse(row.CABOR_Completion_Date__c_is_deterministic)
        self.assertTrue(pd.isna(row.CABOR_Completion_Date__c))

    def test_physical_lookup(self):
        row = self.row("2009", prior="2009")
        self.assertEqual(row.First_Physical_Measurement_Date_Time__c, OLD)
        self.assertEqual(row.Last_Physical_Measurement_Date_Time__c, NEW)

    def test_default_and_noncomplete_keep_before(self):
        for index, status, consent in [
            ("9999", "Complete", "Yes"),
            ("2001", "In-Progress", "Yes"),
            ("1001", "Complete", "No"),
            ("1008", "Complete", "No"),
        ]:
            row = self.row(index, status=status, consent=consent)
            for field in m.ACCOUNT_FIELDS_ASSIGNED_BY_FLOW:
                self.assertEqual(row[field], 22 if field == "Age_at_Time_of_Consent__pc" else OLD)

    def test_missing_parent_retained(self):
        Trigger, All, Account, Contact = fixtures("2001")
        Contact = Contact.filter(Contact.Id == "absent")
        Record = m.join_account(Trigger, Contact, Account)
        Record = m.add_flow_context(Record, All, flow_run_date=ibis.date("2026-10-21"))
        rows = self.con.execute(m.expected_account_values(Record))
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows["Account.Id"].isna().all())

    def test_rollups_are_separate_expected_case_aggregates(self):
        Account = ibis.memtable(
            {
                "Id": ["a1", "a2", "business"],
                "PersonContactId": ["c1", "c2", None],
                "IsPersonAccount": [True, True, False],
            }
        )
        Survey = ibis.memtable(
            {
                "Participant__c": ["c1", "c1", "c1", "other"],
                "Completion_Status__c": ["Complete", "Complete", "In-Progress", "Complete"],
                "Survey_Index_Number__c": ["1001", "1001", "1002", "1001"],
                "Consent_Status__c": ["Yes", "Yes", "Yes", "Yes"],
                "Consent_Revoked__c": [False, False, False, False],
            }
        )
        expected = m.expected_survey_rollups(Account, Survey)
        rows = self.con.execute(expected).set_index("Account.Id")
        self.assertEqual(set(rows.index), {"a1", "a2"})
        self.assertEqual(rows.loc["a1", "Count_of_Completed_Primary_Consent__pc"], 2)
        self.assertEqual(rows.loc["a2", "Count_of_Completed_Primary_Consent__pc"], 0)
        self.assertEqual(rows.loc["a1", "X0_6_Peds_Permission_Count__pc"], 1)
        sql = str(ibis.to_sql(expected, dialect="athena"))
        self.assertEqual(len(sqlglot.parse(sql, read="athena")), 1)
        self.assertIn("CASE", sql)
        self.assertIn("SUM(", sql)

    def test_intermediate_decision_targets_are_not_projected(self):
        row = self.row("2001")
        self.assertFalse(
            any(column.startswith("FlowDecision_") for column in row.index),
            "resolved routing conditions belong in final expected expressions",
        )

    def context(self, index="1001", **kwargs):
        Trigger, All, Account, Contact = fixtures(index, **kwargs)
        return m.add_flow_context(
            m.join_account(Trigger, Contact, Account), All, flow_run_date=ibis.date("2026-10-21")
        )

    def test_plain_ibis_values_can_be_selected_independently(self):
        import ibis.expr.types as ir

        R = self.context("2001")
        fields = m.derived_account_expressions(R)
        self.assertEqual(len(fields), 19)
        self.assertTrue(all(isinstance(f, ir.Value) for f in fields))
        by_name = {f.get_name(): f for f in fields}
        basics = by_name["Basics_Date_Time__c"]
        self.assertEqual(self.con.execute(R.select(basics)).iloc[0].Basics_Date_Time__c, NEW)
        selected = m.expected_account_values(R, fields=[basics])
        self.assertEqual(self.con.execute(selected).iloc[0].Basics_Date_Time__c, NEW)
        with self.assertRaises(ValueError):
            m.expected_account_values(R, fields=[basics, basics])

    def test_annotations_match_final_aliases_and_original_sources(self):
        query = to_sqlglot(
            build("1001", prior="1002"), projection_lineage=lineage.PROJECTION_LINEAGE
        )
        by_name = {p.alias_or_name: p for p in query.selects}
        self.assertEqual(query.meta["ppsc"]["unannotated_fields"], [])
        for name in m.ACCOUNT_FIELDS_ASSIGNED_BY_FLOW:
            self.assertEqual(by_name[name].meta["ppsc"]["target_field"], "Account." + name)
        p = by_name["Basics_Date_Time__c"].meta["ppsc"]
        self.assertEqual(p["source_entities"], ["FlowRecordUpdate.updateAccount2001"])
        self.assertEqual(p["branches"][0]["rule_id"], "set_basics_completion_timestamp")
        self.assertEqual(p["workbook_rows"], [14506])
        self.assertFalse(any(name.startswith("FlowDecision_") for name in by_name))

    def test_ast_copy_and_dump_load_preserve_metadata(self):
        import json

        from sqlglot import exp

        query = to_sqlglot(
            build("1008", prior="1007"), projection_lineage=lineage.PROJECTION_LINEAGE
        )
        for restored in [query.copy(), exp.Expression.load(json.loads(json.dumps(query.dump())))]:
            self.assertEqual(restored.meta["ppsc"], query.meta["ppsc"])
            self.assertEqual(
                [p.meta["ppsc"] for p in restored.selects], [p.meta["ppsc"] for p in query.selects]
            )
            self.assertEqual(restored.sql(dialect="athena"), query.sql(dialect="athena"))
        sql = query.sql(dialect="athena", pretty=True)
        self.assertIn("source: FlowRecordUpdate.updateAccount2001", sql)
        reparsed = sqlglot.parse_one(sql, read="athena")
        self.assertFalse(any(n.meta.get("ppsc") for n in reparsed.walk()))

    def test_recompilation_reapplies_independent_metadata(self):
        from ibis.backends.sql.compilers.athena import compiler

        from ppsc_ops_data_quality.account_to_survey_results import lineage

        expression = build("1001")
        first = to_sqlglot(expression, projection_lineage=lineage.PROJECTION_LINEAGE)
        plain = compiler.to_sqlglot(expression)
        self.assertTrue(all("ppsc" not in p.meta for p in plain.selects))
        first.selects[-1].meta["ppsc"]["description"] = "mutated copy"
        second = to_sqlglot(expression, projection_lineage=lineage.PROJECTION_LINEAGE)
        self.assertNotEqual(second.selects[-1].meta["ppsc"]["description"], "mutated copy")
        self.assertNotEqual(
            lineage.PROJECTION_LINEAGE[second.selects[-1].alias_or_name]["description"],
            "mutated copy",
        )

    def test_all_authored_update_sources_and_branch_ids_retained(self):
        import json

        from ppsc_ops_data_quality.account_to_survey_results import lineage

        query = to_sqlglot(build("1008"), projection_lineage=lineage.PROJECTION_LINEAGE)
        manifest = json.loads(
            (Path(__file__).parent / "fixtures/survey_completion_flow_updates.json").read_text()
        )
        expected = set(manifest["record_update_ids"])
        actual = {
            s for s in query.meta["ppsc"]["source_entities"] if s.startswith("FlowRecordUpdate.")
        }
        self.assertEqual(actual, expected)
        ids = {b["rule_id"] for p in query.selects for b in p.meta["ppsc"].get("branches", [])}
        rolls = ibis.table(
            {
                "Completion_Status__c": "string",
                "Consent_Status__c": "string",
                "Consent_Revoked__c": "boolean",
                "Survey_Index_Number__c": "string",
            },
            name="Record",
        )
        for indicator in m.survey_rollup_indicators(rolls):
            ids.update(
                b["rule_id"] for b in lineage.PROJECTION_LINEAGE[indicator.get_name()]["branches"]
            )
        intermediate_decision_ids = {
            branch["rule_id"]
            for name, metadata in lineage.PROJECTION_LINEAGE.items()
            if name.startswith("FlowDecision_")
            for branch in metadata.get("branches", [])
        }
        self.assertEqual(ids, set(lineage.BRANCH_LINEAGE) - intermediate_decision_ids)

    def test_annotated_athena_ast_matches_ibis_execution(self):
        import pandas as pd

        for index, kwargs in [
            ("1001", {"prior": "1002"}),
            ("1008", {"prior": "1007", "earliest": None}),
            ("2009", {"prior": "2009"}),
        ]:
            with self.subTest(index=index):
                expression = build(index, **kwargs)
                expected = self.con.execute(expression)
                query = to_sqlglot(expression, projection_lineage=lineage.PROJECTION_LINEAGE)
                parsed = sqlglot.parse_one(query.sql(dialect="athena"), read="athena")
                rows = self.con.raw_sql(parsed.sql(dialect="duckdb")).fetchall()
                actual = pd.DataFrame(rows, columns=expected.columns)
                # pandas 3 can represent SQL NULL strings as NaN rather than None.
                # Compare null positions independently, then every non-null value.
                pd.testing.assert_frame_equal(actual.isna(), expected.isna())
                for column in expected.columns:
                    present = expected[column].notna()
                    pd.testing.assert_series_equal(
                        actual.loc[present, column].reset_index(drop=True),
                        expected.loc[present, column].reset_index(drop=True),
                        check_dtype=False,
                    )

    def test_unknown_outputs_and_null_predicates(self):
        R = self.context("1001", status=None)
        row = self.con.execute(m.expected_account_values(R)).iloc[0]
        self.assertEqual(row.Age_at_Time_of_Consent__pc, 22)
        custom = R.select(custom_output=R.Id)
        query = to_sqlglot(custom, projection_lineage=lineage.PROJECTION_LINEAGE)
        self.assertEqual(query.meta["ppsc"]["unannotated_fields"], ["custom_output"])
        self.assertNotIn("ppsc", query.selects[0].meta)


if __name__ == "__main__":
    unittest.main(verbosity=2)
