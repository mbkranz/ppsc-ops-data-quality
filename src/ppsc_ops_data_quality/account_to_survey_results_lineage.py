"""Authoritative source lineage for Ibis-authored Account derivations.

The query module attaches PROJECTION_LINEAGE to final SQLGlot projections by exact
output alias, after completing all Ibis composition. These records never decorate
Ibis objects. Original metadata IDs and one-based workbook rows remain verbatim.
No expression-library imports are needed here.

Workbook: salesforce_schemas_combined_latest.xlsx.
Flow export: flow_survey_results_update.csv / processing-Flow-elements.
Execution-date age remains distinct from the migration anniversary-age formula.
Snapshot rollups remain distinct from per-event Flow Account assignments.
"""

FLOW_ENTITY_LINEAGE = {
    "FlowDecision.Survey_Completion_Route": {
        "source_entity": "FlowDecision.Survey_Index",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14483,
        "entity_type": "FlowDecision",
    },
    "FlowDecision.Primary_Consent_Account_Update": {
        "source_entity": "FlowDecision.Previous_Primary_Consent_Exists",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14486,
        "entity_type": "FlowDecision",
    },
    "FlowDecision.EHR_Consent_Account_Update": {
        "source_entity": "FlowDecision.Previous_EHR_Exists",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14493,
        "entity_type": "FlowDecision",
    },
    "FlowDecision.Assent_Account_Update": {
        "source_entity": "FlowDecision.Decision_4",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14501,
        "entity_type": "FlowDecision",
    },
    "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent": {
        "source_entity": "FlowRecordLookup.getEarliestPrimaryConsent",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14485,
        "entity_type": "FlowRecordLookup",
    },
    "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent": {
        "source_entity": "FlowRecordLookup.getEarliestEgetEarliestEHRConsentHRConsent",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14492,
        "entity_type": "FlowRecordLookup",
    },
    "FlowRecordLookup.First_Remote_Physical_Measurement": {
        "source_entity": "FlowRecordLookup.getFirstPhysicalMeasurement",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14518,
        "entity_type": "FlowRecordLookup",
    },
    "FlowRecordLookup.Pediatric_Permission_For_Assent": {
        "source_entity": "FlowRecordLookup.Get_Permission_1007",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14500,
        "entity_type": "FlowRecordLookup",
    },
    "FlowFormula.Age_At_Execution": {
        "source_entity": "FlowFormula.formAgeCalculation",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14573,
        "entity_type": "FlowFormula",
    },
    "FlowRecordUpdate.Primary_Consent_Without_Prior_Yes": {
        "source_entity": "FlowRecordUpdate.updateAccount1001_Positive",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14488,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Primary_Consent_With_Prior_Yes": {
        "source_entity": "FlowRecordUpdate.updateAccount1001_Negative",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14490,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.EHR_Consent_Without_Prior_Yes": {
        "source_entity": "FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14495,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.EHR_Consent_With_Prior_Yes": {
        "source_entity": "FlowRecordUpdate.updateAccount1003_NegativeSF",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14496,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Assent_No_Permission_And_No_Primary_Date": {
        "source_entity": "FlowRecordUpdate.Update_Account_1007_Positive",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14503,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date": {
        "source_entity": "FlowRecordUpdate.Update_Account_1007_Negative",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14504,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Primary_Consent_Update_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount1005",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14498,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Basics_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2001",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14506,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Overall_Health_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2003",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14508,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Lifestyle_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2005",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14510,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Personal_And_Family_History_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2006",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14512,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Healthcare_Access_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2007",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14514,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Life_Functioning_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2008",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14516,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Remote_Physical_Measurement_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2009",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14519,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Emotional_Health_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2010",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14521,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Behavioral_Health_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2011",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14523,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Environmental_Exposures_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2012",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14525,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowRecordUpdate.Social_Determinants_Completion": {
        "source_entity": "FlowRecordUpdate.updateAccount2013",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14527,
        "entity_type": "FlowRecordUpdate",
    },
    "FlowStart.Complete_Survey_Event": {
        "source_entity": "FlowStart.start",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "workbook_tab": "processing-Flow-elements",
        "workbook_row": 14482,
        "entity_type": "FlowStart",
    },
}

ACCOUNT_FIELD_LINEAGE = {
    "Account.Age_at_Time_of_Consent__pc": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": [
            "FlowRecordUpdate.updateAccount1001_Positive",
            "FlowRecordUpdate.updateAccount1001_Negative",
            "FlowRecordUpdate.Update_Account_1007_Positive",
            "FlowRecordUpdate.Update_Account_1007_Negative",
            "FlowFormula.formAgeCalculation",
        ],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount1001_Positive,\n"
        "FlowRecordUpdate.updateAccount1001_Negative, "
        "FlowRecordUpdate.Update_Account_1007_Positive,\n"
        "FlowRecordUpdate.Update_Account_1007_Negative, "
        "FlowFormula.formAgeCalculation.\n"
        "\n"
        "Flow updates rows 14488,14490,14503,14504 "
        "-> Account.Age_at_Time_of_Consent__pc.\n"
        "\n"
        "Both primary-consent branches and both "
        "assent branches assign the translated\n"
        "FlowFormula.Age_At_Execution value. Other "
        "routes retain the Account BEFORE value. "
        "This is\n"
        "execution-date age.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14488, 14490, 14503, 14504, 14573],
        "expression": "age_at_flow_execution",
        "branches": ["set_age_at_flow_execution"],
        "entity_type": "AccountField",
    },
    "Account.CABOR_Completion_Date__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": [
            "FlowRecordUpdate.updateAccount1001_Positive",
            "FlowRecordUpdate.updateAccount1001_Negative",
            "FlowRecordUpdate.Update_Account_1007_Positive",
            "FlowRecordUpdate.Update_Account_1007_Negative",
            "FlowRecordLookup.Get_Permission_1007",
        ],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount1001_Positive,\n"
        "FlowRecordUpdate.updateAccount1001_Negative, "
        "FlowRecordUpdate.Update_Account_1007_Positive,\n"
        "FlowRecordUpdate.Update_Account_1007_Negative, "
        "FlowRecordLookup.Get_Permission_1007.\n"
        "\n"
        "Rows 14488,14490,14503,14504 -> "
        "Account.CABOR_Completion_Date__c.\n"
        "\n"
        "Primary uses "
        "Record.California_Signature__c; assent uses "
        "the 1007 lookup's\n"
        "California_Signature__c, including an "
        "assigned NULL when no permission exists. An "
        "unordered\n"
        "multi-match also returns NULL, "
        "distinguished by the output flag.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14488, 14490, 14500, 14503, 14504],
        "expression": "california_signature_timestamp",
        "branches": [
            "set_california_signature_from_primary_consent",
            "set_california_signature_from_pediatric_permission",
        ],
        "entity_type": "AccountField",
    },
    "Account.Earliest_Primary_Consent_Date_for_Report__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": [
            "FlowRecordUpdate.updateAccount1001_Negative",
            "FlowRecordUpdate.Update_Account_1007_Negative",
        ],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount1001_Negative,\n"
        "FlowRecordUpdate.Update_Account_1007_Negative.\n"
        "\n"
        "Rows 14490,14504 -> "
        "Account.Earliest_Primary_Consent_Date_for_Report__c.\n"
        "\n"
        "FlowRecordUpdate.Primary_Consent_With_Prior_Yes "
        "writes the triggering "
        "completion timestamp\n"
        "when another Yes primary "
        "consent exists.\n"
        "FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date "
        "also writes the "
        "triggering\n"
        "timestamp. Positive "
        "branches leave this "
        "field unchanged. This is "
        "the authored "
        "assignment,\n"
        "not MIN(consent "
        "timestamps).",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14490, 14504],
        "expression": "earliest_primary_consent_report_timestamp",
        "branches": ["set_earliest_primary_consent_report_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Latest_Primary_Consent_Date_for_Report__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": [
            "FlowRecordUpdate.updateAccount1001_Positive",
            "FlowRecordUpdate.updateAccount1001_Negative",
            "FlowRecordUpdate.Update_Account_1007_Positive",
            "FlowRecordUpdate.Update_Account_1007_Negative",
        ],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount1001_Positive,\n"
        "FlowRecordUpdate.updateAccount1001_Negative, "
        "FlowRecordUpdate.Update_Account_1007_Positive,\n"
        "FlowRecordUpdate.Update_Account_1007_Negative.\n"
        "\n"
        "Rows "
        "14488,14490,14503,14504 -> "
        "Account.Latest_Primary_Consent_Date_for_Report__c.\n"
        "\n"
        "Both primary-consent and "
        "assent routes assign "
        "Record.Completion_Status_Timestamp__c. "
        "Lineage\n"
        "is the triggering record, "
        "not MAX of all participant "
        "completion dates.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14488, 14490, 14503, 14504],
        "expression": "latest_primary_consent_report_timestamp",
        "branches": ["set_latest_primary_consent_report_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.EHR_Consent_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount1003_NegativeSF"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount1003_NegativeSF.\n"
        "\n"
        "FlowRecordUpdate.EHR_Consent_With_Prior_Yes, "
        "row 14496 -> "
        "Account.EHR_Consent_Date_Time__c.\n"
        "\n"
        "Another Yes EHR consent exists: assign "
        "Record.Completion_Status_Timestamp__c. The "
        "no-prior\n"
        "branch writes EHR_Reconsent_Date_Time__c "
        "instead, as authored.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14496],
        "expression": "ehr_consent_timestamp",
        "branches": ["set_ehr_consent_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.EHR_Reconsent_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF.\n"
        "\n"
        "FlowRecordUpdate.EHR_Consent_Without_Prior_Yes, "
        "row 14495 ->\n"
        "Account.EHR_Reconsent_Date_Time__c.\n"
        "\n"
        "No other Yes EHR consent exists: assign "
        "Record.Completion_Status_Timestamp__c. "
        "This\n"
        "counterintuitive source mapping is "
        "preserved rather than renamed.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14495],
        "expression": "ehr_reconsent_timestamp",
        "branches": ["set_ehr_reconsent_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Update_to_Primary_Consent_Completed__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount1005"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount1005.\n"
        "\n"
        "FlowRecordUpdate.Primary_Consent_Update_Completion, "
        "row 14498: index 1005 -> "
        "triggering\n"
        "completion timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14498],
        "expression": "primary_consent_update_timestamp",
        "branches": ["set_primary_consent_update_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Basics_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2001"],
        "source_notes": "Sources: FlowRecordUpdate.updateAccount2001.\n"
        "\n"
        "FlowRecordUpdate.Basics_Completion, row 14506: "
        "indexes 2001/2002 -> triggering completion\n"
        "timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14506],
        "expression": "basics_completion_timestamp",
        "branches": ["set_basics_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Overall_Health_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2003"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount2003.\n"
        "\n"
        "FlowRecordUpdate.Overall_Health_Completion, "
        "row 14508: indexes 2003/2004 -> "
        "triggering\n"
        "completion timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14508],
        "expression": "overall_health_completion_timestamp",
        "branches": ["set_overall_health_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Lifestyle_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2005"],
        "source_notes": "Sources: FlowRecordUpdate.updateAccount2005.\n"
        "\n"
        "FlowRecordUpdate.Lifestyle_Completion, row "
        "14510: index 2005 -> triggering completion\n"
        "timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14510],
        "expression": "lifestyle_completion_timestamp",
        "branches": ["set_lifestyle_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Personal_and_Family_History_Complete__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2006"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount2006.\n"
        "\n"
        "FlowRecordUpdate.Personal_And_Family_History_Completion, "
        "row 14512: index 2006 -> "
        "triggering\n"
        "completion timestamp.\n"
        "\n"
        "This Flow assignment does "
        "not implement the "
        "migration's retired-survey "
        "PFHH derivation;\n"
        "those are different sources "
        "and must be authored "
        "separately.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14512],
        "expression": "personal_and_family_history_completion_timestamp",
        "branches": ["set_personal_and_family_history_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.HC_Access_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2007"],
        "source_notes": "Sources: FlowRecordUpdate.updateAccount2007.\n"
        "\n"
        "FlowRecordUpdate.Healthcare_Access_Completion, "
        "row 14514: index 2007 -> triggering\n"
        "completion timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14514],
        "expression": "healthcare_access_completion_timestamp",
        "branches": ["set_healthcare_access_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Life_Functioning_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2008"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount2008.\n"
        "\n"
        "FlowRecordUpdate.Life_Functioning_Completion, "
        "row 14516: index 2008 -> triggering "
        "completion\n"
        "timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14516],
        "expression": "life_functioning_completion_timestamp",
        "branches": ["set_life_functioning_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.First_Physical_Measurement_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": [
            "FlowRecordUpdate.updateAccount2009",
            "FlowRecordLookup.getFirstPhysicalMeasurement",
        ],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount2009, "
        "FlowRecordLookup.getFirstPhysicalMeasurement.\n"
        "\n"
        "FlowRecordUpdate.Remote_Physical_Measurement_Completion, "
        "row 14519 ->\n"
        "FlowRecordLookup_First_Remote_Physical_Measurement "
        "completion timestamp.\n"
        "\n"
        "First value comes from the "
        "sorted lookup; it can be "
        "NULL if the earliest "
        "matching record has\n"
        "a NULL completion timestamp. "
        "No coalescing is applied.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14518, 14519],
        "expression": "first_remote_physical_measurement_timestamp",
        "branches": ["set_first_remote_physical_measurement_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Last_Physical_Measurement_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2009"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount2009.\n"
        "\n"
        "FlowRecordUpdate.Remote_Physical_Measurement_Completion, "
        "row 14519 -> triggering "
        "completion\n"
        "timestamp, not MAX.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14519],
        "expression": "latest_processed_remote_physical_measurement_timestamp",
        "branches": ["set_latest_processed_remote_physical_measurement_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.EH_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2010"],
        "source_notes": "Sources: FlowRecordUpdate.updateAccount2010.\n"
        "\n"
        "FlowRecordUpdate.Emotional_Health_Completion, row "
        "14521: index 2010 -> triggering completion\n"
        "timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14521],
        "expression": "emotional_health_completion_timestamp",
        "branches": ["set_emotional_health_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Behavioral_Health_Completion__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2011"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount2011.\n"
        "\n"
        "FlowRecordUpdate.Behavioral_Health_Completion, "
        "row 14523: index 2011 -> triggering\n"
        "completion timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14523],
        "expression": "behavioral_health_completion_timestamp",
        "branches": ["set_behavioral_health_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Environmental_Exposures_Date_Time__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2012"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount2012.\n"
        "\n"
        "FlowRecordUpdate.Environmental_Exposures_Completion, "
        "row 14525: index 2012 -> "
        "triggering\n"
        "completion timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14525],
        "expression": "environmental_exposures_completion_timestamp",
        "branches": ["set_environmental_exposures_completion_timestamp"],
        "entity_type": "AccountField",
    },
    "Account.Social_Determinants_of_Health_Completion__c": {
        "source_flow": "Survey_Result_Survey_Completion_Updates",
        "source_entities": ["FlowRecordUpdate.updateAccount2013"],
        "source_notes": "Sources: "
        "FlowRecordUpdate.updateAccount2013.\n"
        "\n"
        "FlowRecordUpdate.Social_Determinants_Completion, "
        "row 14527: index 2013 -> "
        "triggering\n"
        "completion timestamp.",
        "workbook_tab": "processing-Flow-elements",
        "workbook_rows": [14527],
        "expression": "social_determinants_completion_timestamp",
        "branches": ["set_social_determinants_completion_timestamp"],
        "entity_type": "AccountField",
    },
}

ROLLUP_FIELD_LINEAGE = {
    "Account.EHR_Authorized__pc": {
        "source_entity": "Account.EHR_Authorized__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 442,
        "expression": "ehr_authorized_indicator",
        "branches": ["count_completed_ehr_authorization"],
        "entity_type": "AccountRollup",
    },
    "Account.Count_of_Completed_EHR_Auth__pc": {
        "source_entity": "Account.Count_of_Completed_EHR_Auth__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 465,
        "expression": "count_of_completed_ehr_auth_indicator",
        "branches": ["count_completed_ehr_authorization"],
        "entity_type": "AccountRollup",
    },
    "Account.Count_of_Completed_Primary_Consent__pc": {
        "source_entity": "Account.Count_of_Completed_Primary_Consent__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 466,
        "expression": "count_of_completed_primary_consent_indicator",
        "branches": ["count_completed_primary_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.Count_of_Completed_Reconsent__pc": {
        "source_entity": "Account.Count_of_Completed_Reconsent__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 467,
        "expression": "count_of_completed_reconsent_indicator",
        "branches": ["count_completed_primary_consent_updates"],
        "entity_type": "AccountRollup",
    },
    "Account.PPI_2_Completion_Count__pc": {
        "source_entity": "Account.PPI_2_Completion_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 468,
        "expression": "ppi_2_completion_count_indicator",
        "branches": ["count_completed_lifestyle_surveys"],
        "entity_type": "AccountRollup",
    },
    "Account.PPI_3_Completion_Count__pc": {
        "source_entity": "Account.PPI_3_Completion_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 469,
        "expression": "ppi_3_completion_count_indicator",
        "branches": ["count_completed_overall_health_surveys"],
        "entity_type": "AccountRollup",
    },
    "Account.EHR_Consent_Active__pc": {
        "source_entity": "Account.EHR_Consent_Active__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 443,
        "expression": "ehr_consent_active_indicator",
        "branches": ["count_active_ehr_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.EHR_Consent_Declined__pc": {
        "source_entity": "Account.EHR_Consent_Declined__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 540,
        "expression": "ehr_consent_declined_indicator",
        "branches": ["count_declined_ehr_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.PP1_Basics_Survey_Complete__pc": {
        "source_entity": "Account.PP1_Basics_Survey_Complete__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 541,
        "expression": "pp1_basics_survey_complete_indicator",
        "branches": ["count_completed_unrevoked_basics_surveys"],
        "entity_type": "AccountRollup",
    },
    "Account.Re_Consent_Declined__pc": {
        "source_entity": "Account.Re_Consent_Declined__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 542,
        "expression": "re_consent_declined_indicator",
        "branches": ["count_declined_primary_consent_updates"],
        "entity_type": "AccountRollup",
    },
    "Account.Re_consent_Active__pc": {
        "source_entity": "Account.Re_consent_Active__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 543,
        "expression": "re_consent_active_indicator",
        "branches": ["count_active_primary_consent_updates"],
        "entity_type": "AccountRollup",
    },
    "Account.Primary_Consent_Declined__pc": {
        "source_entity": "Account.Primary_Consent_Declined__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 555,
        "expression": "primary_consent_declined_indicator",
        "branches": ["count_declined_primary_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.EHR_Consent_Ever__pc": {
        "source_entity": "Account.EHR_Consent_Ever__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 562,
        "expression": "ehr_consent_ever_indicator",
        "branches": ["count_ever_authorized_ehr_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.Assent_Completion_Count__pc": {
        "source_entity": "Account.Assent_Completion_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 594,
        "expression": "assent_completion_count_indicator",
        "branches": ["count_completed_active_assent"],
        "entity_type": "AccountRollup",
    },
    "Account.Pediatric_Permission_Completion_Count__pc": {
        "source_entity": "Account.Pediatric_Permission_Completion_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 595,
        "expression": "pediatric_permission_completion_count_indicator",
        "branches": ["count_completed_active_pediatric_permission"],
        "entity_type": "AccountRollup",
    },
    "Account.X0_6_Peds_Permission_Count__pc": {
        "source_entity": "Account.X0_6_Peds_Permission_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 622,
        "expression": "x0_6_peds_permission_count_indicator",
        "branches": ["count_active_permission_ages_zero_to_six"],
        "entity_type": "AccountRollup",
    },
    "Account.X0_6_Peds_Permission_Declined_Count__pc": {
        "source_entity": "Account.X0_6_Peds_Permission_Declined_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 623,
        "expression": "x0_6_peds_permission_declined_count_indicator",
        "branches": ["count_declined_permission_ages_zero_to_six"],
        "entity_type": "AccountRollup",
    },
    "Account.X0_6_Peds_Permission_Revoked_Count__pc": {
        "source_entity": "Account.X0_6_Peds_Permission_Revoked_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 624,
        "expression": "x0_6_peds_permission_revoked_count_indicator",
        "branches": ["count_revoked_permission_ages_zero_to_six"],
        "entity_type": "AccountRollup",
    },
    "Account.EHR_Pediatric_Complete__pc": {
        "source_entity": "Account.EHR_Pediatric_Complete__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 626,
        "expression": "ehr_pediatric_complete_indicator",
        "branches": ["count_completed_active_pediatric_ehr_consent"],
        "entity_type": "AccountRollup",
    },
}

BRANCH_LINEAGE = {
    "set_age_at_flow_execution": {
        "output_fields": ["Account.Age_at_Time_of_Consent__pc"],
        "source_entities": [
            "FlowRecordUpdate.updateAccount1001_Positive",
            "FlowRecordUpdate.updateAccount1001_Negative",
            "FlowRecordUpdate.Update_Account_1007_Positive",
            "FlowRecordUpdate.Update_Account_1007_Negative",
            "FlowFormula.formAgeCalculation",
        ],
        "workbook_rows": [14488, 14490, 14503, 14504, 14573],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_california_signature_from_primary_consent": {
        "output_fields": ["Account.CABOR_Completion_Date__c"],
        "source_entities": [
            "FlowRecordUpdate.updateAccount1001_Positive",
            "FlowRecordUpdate.updateAccount1001_Negative",
        ],
        "workbook_rows": [14488, 14490],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_california_signature_from_pediatric_permission": {
        "output_fields": ["Account.CABOR_Completion_Date__c"],
        "source_entities": [
            "FlowRecordUpdate.Update_Account_1007_Positive",
            "FlowRecordUpdate.Update_Account_1007_Negative",
            "FlowRecordLookup.Get_Permission_1007",
        ],
        "workbook_rows": [14500, 14503, 14504],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_earliest_primary_consent_report_timestamp": {
        "output_fields": ["Account.Earliest_Primary_Consent_Date_for_Report__c"],
        "source_entities": [
            "FlowRecordUpdate.updateAccount1001_Negative",
            "FlowRecordUpdate.Update_Account_1007_Negative",
        ],
        "workbook_rows": [14490, 14504],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_latest_primary_consent_report_timestamp": {
        "output_fields": ["Account.Latest_Primary_Consent_Date_for_Report__c"],
        "source_entities": [
            "FlowRecordUpdate.updateAccount1001_Positive",
            "FlowRecordUpdate.updateAccount1001_Negative",
            "FlowRecordUpdate.Update_Account_1007_Positive",
            "FlowRecordUpdate.Update_Account_1007_Negative",
        ],
        "workbook_rows": [14488, 14490, 14503, 14504],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_ehr_consent_timestamp": {
        "output_fields": ["Account.EHR_Consent_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount1003_NegativeSF"],
        "workbook_rows": [14496],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_ehr_reconsent_timestamp": {
        "output_fields": ["Account.EHR_Reconsent_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF"],
        "workbook_rows": [14495],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_primary_consent_update_timestamp": {
        "output_fields": ["Account.Update_to_Primary_Consent_Completed__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount1005"],
        "workbook_rows": [14498],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_basics_completion_timestamp": {
        "output_fields": ["Account.Basics_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2001"],
        "workbook_rows": [14506],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_overall_health_completion_timestamp": {
        "output_fields": ["Account.Overall_Health_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2003"],
        "workbook_rows": [14508],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_lifestyle_completion_timestamp": {
        "output_fields": ["Account.Lifestyle_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2005"],
        "workbook_rows": [14510],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_personal_and_family_history_completion_timestamp": {
        "output_fields": ["Account.Personal_and_Family_History_Complete__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2006"],
        "workbook_rows": [14512],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_healthcare_access_completion_timestamp": {
        "output_fields": ["Account.HC_Access_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2007"],
        "workbook_rows": [14514],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_life_functioning_completion_timestamp": {
        "output_fields": ["Account.Life_Functioning_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2008"],
        "workbook_rows": [14516],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_first_remote_physical_measurement_timestamp": {
        "output_fields": ["Account.First_Physical_Measurement_Date_Time__c"],
        "source_entities": [
            "FlowRecordUpdate.updateAccount2009",
            "FlowRecordLookup.getFirstPhysicalMeasurement",
        ],
        "workbook_rows": [14518, 14519],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_latest_processed_remote_physical_measurement_timestamp": {
        "output_fields": ["Account.Last_Physical_Measurement_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2009"],
        "workbook_rows": [14519],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_emotional_health_completion_timestamp": {
        "output_fields": ["Account.EH_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2010"],
        "workbook_rows": [14521],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_behavioral_health_completion_timestamp": {
        "output_fields": ["Account.Behavioral_Health_Completion__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2011"],
        "workbook_rows": [14523],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_environmental_exposures_completion_timestamp": {
        "output_fields": ["Account.Environmental_Exposures_Date_Time__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2012"],
        "workbook_rows": [14525],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "set_social_determinants_completion_timestamp": {
        "output_fields": ["Account.Social_Determinants_of_Health_Completion__c"],
        "source_entities": ["FlowRecordUpdate.updateAccount2013"],
        "workbook_rows": [14527],
        "entity_type": "AccountField",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "count_completed_ehr_authorization": {
        "output_fields": [
            "Account.EHR_Authorized__pc",
            "Account.Count_of_Completed_EHR_Auth__pc",
        ],
        "source_entities": [
            "Account.EHR_Authorized__pc",
            "Account.Count_of_Completed_EHR_Auth__pc",
        ],
        "workbook_rows": [442, 465],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_primary_consent": {
        "output_fields": ["Account.Count_of_Completed_Primary_Consent__pc"],
        "source_entities": ["Account.Count_of_Completed_Primary_Consent__pc"],
        "workbook_rows": [466],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_primary_consent_updates": {
        "output_fields": ["Account.Count_of_Completed_Reconsent__pc"],
        "source_entities": ["Account.Count_of_Completed_Reconsent__pc"],
        "workbook_rows": [467],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_lifestyle_surveys": {
        "output_fields": ["Account.PPI_2_Completion_Count__pc"],
        "source_entities": ["Account.PPI_2_Completion_Count__pc"],
        "workbook_rows": [468],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_overall_health_surveys": {
        "output_fields": ["Account.PPI_3_Completion_Count__pc"],
        "source_entities": ["Account.PPI_3_Completion_Count__pc"],
        "workbook_rows": [469],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_active_ehr_consent": {
        "output_fields": ["Account.EHR_Consent_Active__pc"],
        "source_entities": ["Account.EHR_Consent_Active__pc"],
        "workbook_rows": [443],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_declined_ehr_consent": {
        "output_fields": ["Account.EHR_Consent_Declined__pc"],
        "source_entities": ["Account.EHR_Consent_Declined__pc"],
        "workbook_rows": [540],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_unrevoked_basics_surveys": {
        "output_fields": ["Account.PP1_Basics_Survey_Complete__pc"],
        "source_entities": ["Account.PP1_Basics_Survey_Complete__pc"],
        "workbook_rows": [541],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_declined_primary_consent_updates": {
        "output_fields": ["Account.Re_Consent_Declined__pc"],
        "source_entities": ["Account.Re_Consent_Declined__pc"],
        "workbook_rows": [542],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_active_primary_consent_updates": {
        "output_fields": ["Account.Re_consent_Active__pc"],
        "source_entities": ["Account.Re_consent_Active__pc"],
        "workbook_rows": [543],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_declined_primary_consent": {
        "output_fields": ["Account.Primary_Consent_Declined__pc"],
        "source_entities": ["Account.Primary_Consent_Declined__pc"],
        "workbook_rows": [555],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_ever_authorized_ehr_consent": {
        "output_fields": ["Account.EHR_Consent_Ever__pc"],
        "source_entities": ["Account.EHR_Consent_Ever__pc"],
        "workbook_rows": [562],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_active_assent": {
        "output_fields": ["Account.Assent_Completion_Count__pc"],
        "source_entities": ["Account.Assent_Completion_Count__pc"],
        "workbook_rows": [594],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_active_pediatric_permission": {
        "output_fields": ["Account.Pediatric_Permission_Completion_Count__pc"],
        "source_entities": ["Account.Pediatric_Permission_Completion_Count__pc"],
        "workbook_rows": [595],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_active_permission_ages_zero_to_six": {
        "output_fields": ["Account.X0_6_Peds_Permission_Count__pc"],
        "source_entities": ["Account.X0_6_Peds_Permission_Count__pc"],
        "workbook_rows": [622],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_declined_permission_ages_zero_to_six": {
        "output_fields": ["Account.X0_6_Peds_Permission_Declined_Count__pc"],
        "source_entities": ["Account.X0_6_Peds_Permission_Declined_Count__pc"],
        "workbook_rows": [623],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_revoked_permission_ages_zero_to_six": {
        "output_fields": ["Account.X0_6_Peds_Permission_Revoked_Count__pc"],
        "source_entities": ["Account.X0_6_Peds_Permission_Revoked_Count__pc"],
        "workbook_rows": [624],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_active_pediatric_ehr_consent": {
        "output_fields": ["Account.EHR_Pediatric_Complete__pc"],
        "source_entities": ["Account.EHR_Pediatric_Complete__pc"],
        "workbook_rows": [626],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "route_to_earliest_other_yes_primary_consent": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_earliest_other_yes_ehr_consent": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_primary_consent_update_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_pediatric_permission_for_assent": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_basics_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_overall_health_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_lifestyle_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_personal_and_family_history_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_healthcare_access_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_life_functioning_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_first_remote_physical_measurement": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_emotional_health_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_behavioral_health_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_environmental_exposures_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "route_to_social_determinants_completion": {
        "output_fields": ["FlowDecision_Survey_Completion_Route_target"],
        "source_entities": ["FlowDecision.Survey_Index", "FlowStart.start"],
        "workbook_rows": [14483, 14482],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "primary_consent_without_prior_yes": {
        "output_fields": ["FlowDecision_Primary_Consent_Account_Update_target"],
        "source_entities": ["FlowDecision.Previous_Primary_Consent_Exists"],
        "workbook_rows": [14486],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "primary_consent_with_prior_yes": {
        "output_fields": ["FlowDecision_Primary_Consent_Account_Update_target"],
        "source_entities": ["FlowDecision.Previous_Primary_Consent_Exists"],
        "workbook_rows": [14486],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "ehr_consent_without_prior_yes": {
        "output_fields": ["FlowDecision_EHR_Consent_Account_Update_target"],
        "source_entities": ["FlowDecision.Previous_EHR_Exists"],
        "workbook_rows": [14493],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "ehr_consent_with_prior_yes": {
        "output_fields": ["FlowDecision_EHR_Consent_Account_Update_target"],
        "source_entities": ["FlowDecision.Previous_EHR_Exists"],
        "workbook_rows": [14493],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "assent_no_permission_and_no_primary_date": {
        "output_fields": ["FlowDecision_Assent_Account_Update_target"],
        "source_entities": ["FlowDecision.Decision_4"],
        "workbook_rows": [14501],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
    "assent_with_permission_or_primary_date": {
        "output_fields": ["FlowDecision_Assent_Account_Update_target"],
        "source_entities": ["FlowDecision.Decision_4"],
        "workbook_rows": [14501],
        "entity_type": "FlowDecision",
        "workbook_tab": "processing-Flow-elements",
        "source_flow": "Survey_Result_Survey_Completion_Updates",
    },
}

ROLLUP_SOURCE_NOTES = (
    "\n"
    "Comma-separated metadata indexes are interpreted as IN lists. Row 555 repeats\n"
    "1005 and omits 1001; the distinct set 1005/1002 is preserved, pending confirmation\n"
    "against raw rollup metadata. The three 0-6 permission counters deliberately omit\n"
    "Complete when the source does. Primary_Consent_Active__pc is omitted because the\n"
    "exported LIKE predicate is corrupted. Sample and clinical-measurement rollups\n"
    "require other child objects. Formula fields with blank bodies cannot be derived.\n"
)

# Final SELECT alias -> metadata. Branch provenance stays inside the field
# record and never relies on compiler-generated CASE node positions.
PROJECTION_LINEAGE = {}
for _fields in (ACCOUNT_FIELD_LINEAGE, ROLLUP_FIELD_LINEAGE):
    for _target, _entry in _fields.items():
        PROJECTION_LINEAGE[_target.removeprefix("Account.")] = {
            **_entry,
            "rule_id": _entry["expression"],
            "target_field": _target,
            "description": _entry["expression"]
            .replace("_indicator", "")
            .replace("_", " ")
            .capitalize(),
            "source_entities": _entry.get("source_entities", [_entry.get("source_entity")]),
            "branches": [{"rule_id": name, **BRANCH_LINEAGE[name]} for name in _entry["branches"]],
        }

for _alias, _entity, _rule_id in (
    (
        "FlowDecision_Survey_Completion_Route_target",
        "FlowDecision.Survey_Completion_Route",
        "survey_completion_flow_decision",
    ),
    (
        "FlowDecision_Primary_Consent_Account_Update_target",
        "FlowDecision.Primary_Consent_Account_Update",
        "primary_consent_account_update_flow_decision",
    ),
    (
        "FlowDecision_EHR_Consent_Account_Update_target",
        "FlowDecision.EHR_Consent_Account_Update",
        "ehr_consent_account_update_flow_decision",
    ),
    (
        "FlowDecision_Assent_Account_Update_target",
        "FlowDecision.Assent_Account_Update",
        "assent_account_update_flow_decision",
    ),
):
    _original = FLOW_ENTITY_LINEAGE[_entity]
    _branches = [
        {"rule_id": name, **entry}
        for name, entry in BRANCH_LINEAGE.items()
        if _alias in entry["output_fields"]
    ]
    PROJECTION_LINEAGE[_alias] = {
        **_original,
        "rule_id": _rule_id,
        "description": "Translated " + _entity,
        "source_entities": list(
            dict.fromkeys(
                [_original["source_entity"]]
                + [source for branch in _branches for source in branch["source_entities"]]
            )
        ),
        "branches": _branches,
    }

for _alias, _entity, _description in (
    (
        "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
        "FlowRecordLookup.Pediatric_Permission_For_Assent",
        "Number of candidate pediatric permissions",
    ),
    (
        "CABOR_Completion_Date__c_is_deterministic",
        "FlowRecordLookup.Pediatric_Permission_For_Assent",
        "Signature lookup has at most one candidate on the assent route",
    ),
    (
        "FlowFormula_Age_At_Execution",
        "FlowFormula.Age_At_Execution",
        "Translated FlowFormula: age at execution",
    ),
):
    _original = FLOW_ENTITY_LINEAGE[_entity]
    PROJECTION_LINEAGE[_alias] = {
        **_original,
        "rule_id": _alias,
        "description": _description,
        "source_entities": [_original["source_entity"]],
    }

for _alias, _source in (
    ("Record.Id", "Survey_Result__c.Id"),
    ("Account.Id", "Account.Id"),
    ("Participant__c", "Survey_Result__c.Participant__c"),
    ("Survey_Index_Number__c", "Survey_Result__c.Survey_Index_Number__c"),
    ("PersonContactId", "Account.PersonContactId"),
):
    PROJECTION_LINEAGE[_alias] = {
        "rule_id": _alias,
        "entity_type": "SalesforceField",
        "description": "Source identity: " + _alias,
        "source_entities": [_source],
    }

# Explicit comparison output aliases keep lineage when the expected dataset is
# composed inline instead of published as an intermediate Athena view. Observed
# columns describe independent measurements, not the expected derivation branches.
for _target in (*ACCOUNT_FIELD_LINEAGE, *ROLLUP_FIELD_LINEAGE):
    _field = _target.removeprefix("Account.")
    _expected_alias = "expected__" + _field
    _observed_alias = "observed__" + _field
    PROJECTION_LINEAGE[_expected_alias] = {
        **PROJECTION_LINEAGE[_field],
        "comparison_role": "expected",
        "description": "Expected " + _target + ": " + PROJECTION_LINEAGE[_field]["description"],
    }
    PROJECTION_LINEAGE[_observed_alias] = {
        "rule_id": _observed_alias,
        "entity_type": "SalesforceField",
        "comparison_role": "observed",
        "description": "Independently observed " + _target,
        "source_entities": [_target],
    }

for _alias, _source_alias, _role in (
    ("survey_result_id", "Record.Id", "identity"),
    ("participant_contact_id", "Participant__c", "identity"),
    ("expected_account_id", "Account.Id", "expected"),
    ("observed_account_id", "Account.Id", "observed"),
    ("person_contact_id", "PersonContactId", "identity"),
    ("survey_index_number", "Survey_Index_Number__c", "evidence"),
    (
        "cabor_lookup_is_deterministic",
        "CABOR_Completion_Date__c_is_deterministic",
        "evidence",
    ),
):
    PROJECTION_LINEAGE[_alias] = {
        **PROJECTION_LINEAGE[_source_alias],
        "comparison_role": _role,
    }
