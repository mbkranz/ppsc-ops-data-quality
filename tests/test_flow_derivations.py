import datetime as dt
import unittest

import ibis
import sqlglot

from ppsc_ops_data_quality.account_to_survey_results import queries as m

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


def build(backend, *args, **kwargs):
    _, surveys, account, contact = fixtures(*args, **kwargs)
    history = {}
    for name, table in [("Account", account), ("Contact", contact), ("Survey_Result__c", surveys)]:
        table = table.mutate(
            valid_from=ibis.timestamp("1999-01-01"),
            valid_to=ibis.null().cast("timestamp"),
            is_current=True,
        )
        history[name] = backend.create_table(
            name + "_history_" + __import__("uuid").uuid4().hex, table
        )
    return m.flow_account_query(
        history,
        survey_result_id="r1",
        account_before_at=dt.datetime(2023, 12, 30),
        execution_at=dt.datetime(2024, 1, 1),
        account_after_at=dt.datetime(2024, 1, 2),
        flow_run_date=dt.date(2026, 10, 21),
        eligibility=kwargs.get("status", "Complete") == "Complete",
        inputs=m.metadata_inputs(),
    )


class ExpectedValues(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = ibis.duckdb.connect()

    def row(self, *args, **kwargs):
        row = (
            self.con.con.execute(
                build(self.con, *args, **kwargs).sql(dialect="duckdb", comments=False)
            )
            .fetchdf()
            .iloc[0]
        )
        return row.rename(
            {"expected." + field: field for field in m.FLOW_FIELDS}
            | {"cabor_lookup_is_deterministic": "CABOR_Completion_Date__c_is_deterministic"}
        )

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
            self.assertEqual(row.Earliest_Primary_Consent_Date_for_Report__c, NEW)
            self.assertEqual(row.Latest_Primary_Consent_Date_for_Report__c, NEW)
            self.assertEqual(row.Age_at_Time_of_Consent__pc, 26)
            row = self.row(index, prior="1001")
            self.assertEqual(row.Earliest_Primary_Consent_Date_for_Report__c, OLD)

    def test_ehr_branches_preserve_source_behavior(self):
        for index in ["1003", "1004"]:
            row = self.row(index)
            self.assertEqual(row.EHR_Reconsent_Date_Time__c, OLD)
            self.assertEqual(row.EHR_Consent_Date_Time__c, NEW)
            row = self.row(index, prior="1003")
            self.assertEqual(row.EHR_Consent_Date_Time__c, OLD)
            self.assertEqual(row.EHR_Reconsent_Date_Time__c, NEW)

    def test_assigned_null_not_coalesced(self):
        import pandas as pd

        row = self.row(signature=None)
        self.assertTrue(pd.isna(row.CABOR_Completion_Date__c))
        row = self.row("1008", earliest=None)
        self.assertEqual(row.Earliest_Primary_Consent_Date_for_Report__c, NEW)
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
        rows = self.con.execute(expected).set_index("Id")
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
