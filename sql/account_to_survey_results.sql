-- ILLUSTRATIVE bindings/event/times; source profiles are defined in account_to_survey_results/definitions/.
-- Direct SELECTs over history. Verify physical catalog types before execution.
-- Execution: 2026-10-21 12:00; BEFORE: 11:59:59; settled AFTER: 12:05.

-- flow
SELECT
  "Comparison_Rows"."Record.Id", /* Source identity: Record.Id; source: Survey_Result__c.Id */
  "Comparison_Rows"."Account.Id", /* Source identity: Account.Id; source: Account.Id */
  "Comparison_Rows"."Participant__c", /* Source identity: Participant__c; source: Survey_Result__c.Participant__c */
  "Comparison_Rows"."Survey_Index_Number__c", /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */
  "Comparison_Rows"."Completion_Status_Timestamp__c", /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
  "Comparison_Rows"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count", /* Number of matching native permission candidates; source: FlowRecordLookup.Get_Permission_1007 */
  "Comparison_Rows"."Age_at_Time_of_Consent__pc", /* Native Flow assignments to Account.Age_at_Time_of_Consent__pc; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowFormula.formAgeCalculation, FlowRecordLookup.getEarliestPrimaryConsent, FlowRecordLookup.Get_Permission_1007 */
  "Comparison_Rows"."CABOR_Completion_Date__c", /* Native Flow assignments to Account.CABOR_Completion_Date__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowRecordLookup.getEarliestPrimaryConsent, FlowRecordLookup.Get_Permission_1007 */
  "Comparison_Rows"."Earliest_Primary_Consent_Date_for_Report__c", /* Native Flow assignments to Account.Earliest_Primary_Consent_Date_for_Report__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Negative, FlowRecordLookup.getEarliestPrimaryConsent, FlowRecordLookup.Get_Permission_1007 */
  "Comparison_Rows"."Latest_Primary_Consent_Date_for_Report__c", /* Native Flow assignments to Account.Latest_Primary_Consent_Date_for_Report__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowRecordLookup.getEarliestPrimaryConsent, FlowRecordLookup.Get_Permission_1007 */
  "Comparison_Rows"."EHR_Consent_Date_Time__c", /* Native Flow assignments to Account.EHR_Consent_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1003_NegativeSF, FlowRecordLookup.getEarliestEgetEarliestEHRConsentHRConsent */
  "Comparison_Rows"."EHR_Reconsent_Date_Time__c", /* Native Flow assignments to Account.EHR_Reconsent_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF, FlowRecordLookup.getEarliestEgetEarliestEHRConsentHRConsent */
  "Comparison_Rows"."Update_to_Primary_Consent_Completed__c", /* Native Flow assignments to Account.Update_to_Primary_Consent_Completed__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1005 */
  "Comparison_Rows"."Basics_Date_Time__c", /* Native Flow assignments to Account.Basics_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2001 */
  "Comparison_Rows"."Overall_Health_Date_Time__c", /* Native Flow assignments to Account.Overall_Health_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2003 */
  "Comparison_Rows"."Lifestyle_Date_Time__c", /* Native Flow assignments to Account.Lifestyle_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2005 */
  "Comparison_Rows"."Personal_and_Family_History_Complete__c", /* Native Flow assignments to Account.Personal_and_Family_History_Complete__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2006 */
  "Comparison_Rows"."HC_Access_Date_Time__c", /* Native Flow assignments to Account.HC_Access_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2007 */
  "Comparison_Rows"."Life_Functioning_Date_Time__c", /* Native Flow assignments to Account.Life_Functioning_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2008 */
  "Comparison_Rows"."First_Physical_Measurement_Date_Time__c", /* Native Flow assignments to Account.First_Physical_Measurement_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2009, FlowRecordLookup.getFirstPhysicalMeasurement */
  "Comparison_Rows"."Last_Physical_Measurement_Date_Time__c", /* Native Flow assignments to Account.Last_Physical_Measurement_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2009 */
  "Comparison_Rows"."EH_Date_Time__c", /* Native Flow assignments to Account.EH_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2010 */
  "Comparison_Rows"."Behavioral_Health_Completion__c", /* Native Flow assignments to Account.Behavioral_Health_Completion__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2011 */
  "Comparison_Rows"."Environmental_Exposures_Date_Time__c", /* Native Flow assignments to Account.Environmental_Exposures_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2012 */
  "Comparison_Rows"."Social_Determinants_of_Health_Completion__c", /* Native Flow assignments to Account.Social_Determinants_of_Health_Completion__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2013 */
  "Comparison_Rows"."CABOR_Completion_Date__c_is_deterministic" /* The selected native assignment has deterministic lookup evidence; source: FlowRecordLookup.Get_Permission_1007 */
FROM (
  WITH "Survey_Results_At_Execution" AS (
    SELECT
      "survey_results_history"."california_signature__c" AS "California_Signature__c",
      "survey_results_history"."completion_status__c" AS "Completion_Status__c",
      "survey_results_history"."completion_status_timestamp__c" AS "Completion_Status_Timestamp__c",
      "survey_results_history"."consent_revoked__c" AS "Consent_Revoked__c",
      "survey_results_history"."consent_status__c" AS "Consent_Status__c",
      "survey_results_history"."consent_status_timestamp__c" AS "Consent_Status_Timestamp__c",
      "survey_results_history"."id" AS "Id",
      "survey_results_history"."is_current",
      "survey_results_history"."loaded_at",
      "survey_results_history"."participant__c" AS "Participant__c",
      "survey_results_history"."survey_index_number__c" AS "Survey_Index_Number__c",
      "survey_results_history"."valid_from",
      "survey_results_history"."valid_to"
    FROM "fixture_catalog"."fixture_lake"."survey_results_history" AS "survey_results_history"
    WHERE
      "survey_results_history"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      AND (
        (
          "survey_results_history"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
        )
        OR (
          "survey_results_history"."valid_to" IS NULL
        )
      )
  ), "Contact_At_Execution" AS (
    SELECT
      "contact_history"."accountid" AS "AccountId",
      "contact_history"."birthdate" AS "Birthdate",
      "contact_history"."id" AS "Id",
      "contact_history"."is_current",
      "contact_history"."loaded_at",
      "contact_history"."valid_from",
      "contact_history"."valid_to"
    FROM "fixture_catalog"."fixture_lake"."contact_history" AS "contact_history"
    WHERE
      "contact_history"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      AND (
        (
          "contact_history"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
        )
        OR (
          "contact_history"."valid_to" IS NULL
        )
      )
  ), "Account_Before" AS (
    SELECT
      "account_history"."age_at_time_of_consent__pc" AS "Age_at_Time_of_Consent__pc",
      "account_history"."assent_completion_count__pc" AS "Assent_Completion_Count__pc",
      "account_history"."basics_date_time__c" AS "Basics_Date_Time__c",
      "account_history"."behavioral_health_completion__c" AS "Behavioral_Health_Completion__c",
      "account_history"."cabor_completion_date__c" AS "CABOR_Completion_Date__c",
      "account_history"."count_of_completed_ehr_auth__pc" AS "Count_of_Completed_EHR_Auth__pc",
      "account_history"."count_of_completed_primary_consent__pc" AS "Count_of_Completed_Primary_Consent__pc",
      "account_history"."count_of_completed_reconsent__pc" AS "Count_of_Completed_Reconsent__pc",
      "account_history"."earliest_primary_consent_date_for_report__c" AS "Earliest_Primary_Consent_Date_for_Report__c",
      "account_history"."eh_date_time__c" AS "EH_Date_Time__c",
      "account_history"."ehr_authorized__pc" AS "EHR_Authorized__pc",
      "account_history"."ehr_consent_active__pc" AS "EHR_Consent_Active__pc",
      "account_history"."ehr_consent_date_time__c" AS "EHR_Consent_Date_Time__c",
      "account_history"."ehr_consent_declined__pc" AS "EHR_Consent_Declined__pc",
      "account_history"."ehr_consent_ever__pc" AS "EHR_Consent_Ever__pc",
      "account_history"."ehr_pediatric_complete__pc" AS "EHR_Pediatric_Complete__pc",
      "account_history"."ehr_reconsent_date_time__c" AS "EHR_Reconsent_Date_Time__c",
      "account_history"."environmental_exposures_date_time__c" AS "Environmental_Exposures_Date_Time__c",
      "account_history"."first_physical_measurement_date_time__c" AS "First_Physical_Measurement_Date_Time__c",
      "account_history"."hc_access_date_time__c" AS "HC_Access_Date_Time__c",
      "account_history"."id" AS "Id",
      "account_history"."is_current",
      "account_history"."ispersonaccount" AS "IsPersonAccount",
      "account_history"."last_physical_measurement_date_time__c" AS "Last_Physical_Measurement_Date_Time__c",
      "account_history"."latest_primary_consent_date_for_report__c" AS "Latest_Primary_Consent_Date_for_Report__c",
      "account_history"."life_functioning_date_time__c" AS "Life_Functioning_Date_Time__c",
      "account_history"."lifestyle_date_time__c" AS "Lifestyle_Date_Time__c",
      "account_history"."loaded_at",
      "account_history"."overall_health_date_time__c" AS "Overall_Health_Date_Time__c",
      "account_history"."pediatric_permission_completion_count__pc" AS "Pediatric_Permission_Completion_Count__pc",
      "account_history"."personal_and_family_history_complete__c" AS "Personal_and_Family_History_Complete__c",
      "account_history"."personcontactid" AS "PersonContactId",
      "account_history"."pp1_basics_survey_complete__pc" AS "PP1_Basics_Survey_Complete__pc",
      "account_history"."ppi_2_completion_count__pc" AS "PPI_2_Completion_Count__pc",
      "account_history"."ppi_3_completion_count__pc" AS "PPI_3_Completion_Count__pc",
      "account_history"."primary_consent_declined__pc" AS "Primary_Consent_Declined__pc",
      "account_history"."re_consent_active__pc" AS "Re_consent_Active__pc",
      "account_history"."re_consent_declined__pc" AS "Re_Consent_Declined__pc",
      "account_history"."social_determinants_of_health_completion__c" AS "Social_Determinants_of_Health_Completion__c",
      "account_history"."update_to_primary_consent_completed__c" AS "Update_to_Primary_Consent_Completed__c",
      "account_history"."valid_from",
      "account_history"."valid_to",
      "account_history"."x0_6_peds_permission_count__pc" AS "X0_6_Peds_Permission_Count__pc",
      "account_history"."x0_6_peds_permission_declined_count__pc" AS "X0_6_Peds_Permission_Declined_Count__pc",
      "account_history"."x0_6_peds_permission_revoked_count__pc" AS "X0_6_Peds_Permission_Revoked_Count__pc"
    FROM "fixture_catalog"."fixture_lake"."account_history" AS "account_history"
    WHERE
      "account_history"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
      AND (
        (
          "account_history"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
        )
        OR (
          "account_history"."valid_to" IS NULL
        )
      )
  ), "getFirstPhysicalMeasurement" AS (
    SELECT
      *
    FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution"
  ), "Get_Permission_1007" AS (
    SELECT
      *
    FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution_2"
  ), "getEarliestEgetEarliestEHRConsentHRConsent" AS (
    SELECT
      *
    FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution_3"
  ), "getEarliestPrimaryConsent" AS (
    SELECT
      *
    FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution_4"
  ), "Contact" AS (
    SELECT
      *
    FROM "Contact_At_Execution" AS "Contact_At_Execution"
  ), "Account" AS (
    SELECT
      *
    FROM "Account_Before" AS "Account_Before"
  ), "Trigger_Survey_Result" AS (
    SELECT
      *
    FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution_5"
    WHERE
      "Survey_Results_At_Execution_5"."Id" = 'EXAMPLE_VERIFIED_SURVEY_EVENT'
  ), "Survey_Result__c" AS (
    SELECT
      *
    FROM "Trigger_Survey_Result" AS "Trigger_Survey_Result"
  ), "Flow_Context" AS (
    SELECT
      "Survey_Result__c_21"."Id",
      "Survey_Result__c_21"."Participant__c",
      "Survey_Result__c_21"."Survey_Index_Number__c",
      "Survey_Result__c_21"."Completion_Status__c",
      "Survey_Result__c_21"."Consent_Status__c",
      "Survey_Result__c_21"."Completion_Status_Timestamp__c",
      "Survey_Result__c_21"."California_Signature__c",
      "Survey_Result__c_21"."Participant__r.AccountId",
      "Survey_Result__c_21"."Participant__r.Birthdate",
      "Survey_Result__c_21"."Participant__r.Account.Id",
      "Survey_Result__c_21"."Participant__r.Account.Age_at_Time_of_Consent__pc",
      "Survey_Result__c_21"."Participant__r.Account.CABOR_Completion_Date__c",
      "Survey_Result__c_21"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
      "Survey_Result__c_21"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
      "Survey_Result__c_21"."Participant__r.Account.EHR_Consent_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
      "Survey_Result__c_21"."Participant__r.Account.Basics_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.Overall_Health_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.Lifestyle_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.Personal_and_Family_History_Complete__c",
      "Survey_Result__c_21"."Participant__r.Account.HC_Access_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.Life_Functioning_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.EH_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.Behavioral_Health_Completion__c",
      "Survey_Result__c_21"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
      "Survey_Result__c_21"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
      "Survey_Result__c_21"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
      "Survey_Result__c_21"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
      "Survey_Result__c_21"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
      "Survey_Result__c_21"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
      "Survey_Result__c_21"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
      "Survey_Result__c_21"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
      "Survey_Result__c_21"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
      "Survey_Result__c_21"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
      "Survey_Result__c_21"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
      "Survey_Result__c_21"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
      "Survey_Result__c_21"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
      "Survey_Result__c_21"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
      "Survey_Result__c_21"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
      "Survey_Result__c_21"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
      "Survey_Result__c_21"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
      "Survey_Result__c_21"."FlowRecordLookup.First_Remote_Physical_Measurement.match_count",
      "Survey_Result__c_21"."__known.FlowRecordLookup.First_Remote_Physical_Measurement.Id",
      "Survey_Result__c_21"."FlowFormula_Age_At_Execution"
    FROM (
      SELECT
        "Survey_Result__c_20"."Id",
        "Survey_Result__c_20"."Participant__c",
        "Survey_Result__c_20"."Survey_Index_Number__c",
        "Survey_Result__c_20"."Completion_Status__c",
        "Survey_Result__c_20"."Consent_Status__c",
        "Survey_Result__c_20"."Completion_Status_Timestamp__c",
        "Survey_Result__c_20"."California_Signature__c",
        "Survey_Result__c_20"."Participant__r.AccountId",
        "Survey_Result__c_20"."Participant__r.Birthdate",
        "Survey_Result__c_20"."Participant__r.Account.Id",
        "Survey_Result__c_20"."Participant__r.Account.Age_at_Time_of_Consent__pc",
        "Survey_Result__c_20"."Participant__r.Account.CABOR_Completion_Date__c",
        "Survey_Result__c_20"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
        "Survey_Result__c_20"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
        "Survey_Result__c_20"."Participant__r.Account.EHR_Consent_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
        "Survey_Result__c_20"."Participant__r.Account.Basics_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.Overall_Health_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.Lifestyle_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.Personal_and_Family_History_Complete__c",
        "Survey_Result__c_20"."Participant__r.Account.HC_Access_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.Life_Functioning_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.EH_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.Behavioral_Health_Completion__c",
        "Survey_Result__c_20"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
        "Survey_Result__c_20"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
        "Survey_Result__c_20"."__ppsc_flow_row",
        "Survey_Result__c_20"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
        "Survey_Result__c_20"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
        "Survey_Result__c_20"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
        "Survey_Result__c_20"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
        "Survey_Result__c_20"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
        "Survey_Result__c_20"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
        "Survey_Result__c_20"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
        "Survey_Result__c_20"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
        "Survey_Result__c_20"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
        "Survey_Result__c_20"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
        "Survey_Result__c_20"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
        "Survey_Result__c_20"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
        "Survey_Result__c_20"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
        "Survey_Result__c_20"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
        "Survey_Result__c_20"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
        "Survey_Result__c_20"."FlowRecordLookup.First_Remote_Physical_Measurement.match_count",
        "Survey_Result__c_20"."__known.FlowRecordLookup.First_Remote_Physical_Measurement.Id",
        CAST(FLOOR(
          DATE_DIFF(
            'DAY',
            DATE_TRUNC('DAY', "Survey_Result__c_20"."Participant__r.Birthdate"),
            DATE_TRUNC('DAY', FROM_ISO8601_DATE('2026-10-21'))
          ) / CAST(365.25 AS DOUBLE)
        ) AS BIGINT) AS "FlowFormula_Age_At_Execution"
      FROM (
        SELECT
          "Survey_Result__c_19"."Id",
          "Survey_Result__c_19"."Participant__c",
          "Survey_Result__c_19"."Survey_Index_Number__c",
          "Survey_Result__c_19"."Completion_Status__c",
          "Survey_Result__c_19"."Consent_Status__c",
          "Survey_Result__c_19"."Completion_Status_Timestamp__c",
          "Survey_Result__c_19"."California_Signature__c",
          "Survey_Result__c_19"."Participant__r.AccountId",
          "Survey_Result__c_19"."Participant__r.Birthdate",
          "Survey_Result__c_19"."Participant__r.Account.Id",
          "Survey_Result__c_19"."Participant__r.Account.Age_at_Time_of_Consent__pc",
          "Survey_Result__c_19"."Participant__r.Account.CABOR_Completion_Date__c",
          "Survey_Result__c_19"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
          "Survey_Result__c_19"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
          "Survey_Result__c_19"."Participant__r.Account.EHR_Consent_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
          "Survey_Result__c_19"."Participant__r.Account.Basics_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.Overall_Health_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.Lifestyle_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.Personal_and_Family_History_Complete__c",
          "Survey_Result__c_19"."Participant__r.Account.HC_Access_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.Life_Functioning_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.EH_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.Behavioral_Health_Completion__c",
          "Survey_Result__c_19"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
          "Survey_Result__c_19"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
          "Survey_Result__c_19"."__ppsc_flow_row",
          "Survey_Result__c_19"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
          "Survey_Result__c_19"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
          "Survey_Result__c_19"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
          "Survey_Result__c_19"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
          "Survey_Result__c_19"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
          "Survey_Result__c_19"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
          "Survey_Result__c_19"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
          "Survey_Result__c_19"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
          "Survey_Result__c_19"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
          "Survey_Result__c_19"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
          "Survey_Result__c_19"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
          "Survey_Result__c_19"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
          "Survey_Result__c_19"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
          "Survey_Result__c_19"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
          "Survey_Result__c_19"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
          "Survey_Result__c_19"."FlowRecordLookup.First_Remote_Physical_Measurement.match_count",
          "Survey_Result__c_19"."__known.FlowRecordLookup.First_Remote_Physical_Measurement.Id"
        FROM (
          SELECT
            *
          FROM (
            SELECT
              "Survey_Result__c_17"."Id",
              "Survey_Result__c_17"."Participant__c",
              "Survey_Result__c_17"."Survey_Index_Number__c",
              "Survey_Result__c_17"."Completion_Status__c",
              "Survey_Result__c_17"."Consent_Status__c",
              "Survey_Result__c_17"."Completion_Status_Timestamp__c",
              "Survey_Result__c_17"."California_Signature__c",
              "Survey_Result__c_17"."Participant__r.AccountId",
              "Survey_Result__c_17"."Participant__r.Birthdate",
              "Survey_Result__c_17"."Participant__r.Account.Id",
              "Survey_Result__c_17"."Participant__r.Account.Age_at_Time_of_Consent__pc",
              "Survey_Result__c_17"."Participant__r.Account.CABOR_Completion_Date__c",
              "Survey_Result__c_17"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
              "Survey_Result__c_17"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
              "Survey_Result__c_17"."Participant__r.Account.EHR_Consent_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
              "Survey_Result__c_17"."Participant__r.Account.Basics_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.Overall_Health_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.Lifestyle_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.Personal_and_Family_History_Complete__c",
              "Survey_Result__c_17"."Participant__r.Account.HC_Access_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.Life_Functioning_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.EH_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.Behavioral_Health_Completion__c",
              "Survey_Result__c_17"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
              "Survey_Result__c_17"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
              "Survey_Result__c_17"."__ppsc_flow_row",
              "Survey_Result__c_17"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
              "Survey_Result__c_17"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
              "Survey_Result__c_17"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
              "Survey_Result__c_17"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
              "Survey_Result__c_17"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
              "Survey_Result__c_17"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
              "Survey_Result__c_17"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
              "Survey_Result__c_17"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
              "Survey_Result__c_17"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
              "Survey_Result__c_17"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
              "Survey_Result__c_17"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
              "Survey_Result__c_17"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
              "Survey_Result__c_17"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
              "Survey_Result__c_17"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
              "Survey_Result__c_17"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
              "Survey_Result__c_17"."__ppsc_match",
              "Survey_Result__c_17"."__ppsc_lookup_known",
              COALESCE(
                SUM("Survey_Result__c_17"."__ppsc_match") OVER (
                  PARTITION BY "Survey_Result__c_17"."__ppsc_flow_row"
                  ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ),
                0
              ) AS "FlowRecordLookup.First_Remote_Physical_Measurement.match_count",
              ROW_NUMBER() OVER (
                PARTITION BY "Survey_Result__c_17"."__ppsc_flow_row"
                ORDER BY "Survey_Result__c_17"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c" ASC NULLS FIRST
              ) - 1 AS "__ppsc_rank",
              TRUE
              AND (
                COALESCE(
                  SUM("Survey_Result__c_17"."__ppsc_match") OVER (
                    PARTITION BY "Survey_Result__c_17"."__ppsc_flow_row", "Survey_Result__c_17"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                  ),
                  0
                ) <= 1
              ) AS "__known.FlowRecordLookup.First_Remote_Physical_Measurement.Id"
            FROM (
              SELECT
                "Survey_Result__c_16"."Id",
                "Survey_Result__c_16"."Participant__c",
                "Survey_Result__c_16"."Survey_Index_Number__c",
                "Survey_Result__c_16"."Completion_Status__c",
                "Survey_Result__c_16"."Consent_Status__c",
                "Survey_Result__c_16"."Completion_Status_Timestamp__c",
                "Survey_Result__c_16"."California_Signature__c",
                "Survey_Result__c_16"."Participant__r.AccountId",
                "Survey_Result__c_16"."Participant__r.Birthdate",
                "Survey_Result__c_16"."Participant__r.Account.Id",
                "Survey_Result__c_16"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                "Survey_Result__c_16"."Participant__r.Account.CABOR_Completion_Date__c",
                "Survey_Result__c_16"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                "Survey_Result__c_16"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                "Survey_Result__c_16"."Participant__r.Account.EHR_Consent_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                "Survey_Result__c_16"."Participant__r.Account.Basics_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.Overall_Health_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.Lifestyle_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                "Survey_Result__c_16"."Participant__r.Account.HC_Access_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.Life_Functioning_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.EH_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.Behavioral_Health_Completion__c",
                "Survey_Result__c_16"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                "Survey_Result__c_16"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                "Survey_Result__c_16"."__ppsc_flow_row",
                "Survey_Result__c_16"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                "Survey_Result__c_16"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                "Survey_Result__c_16"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                "Survey_Result__c_16"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                "Survey_Result__c_16"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                "Survey_Result__c_16"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                "Survey_Result__c_16"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
                "Survey_Result__c_16"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                "Survey_Result__c_16"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
                "Survey_Result__c_16"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
                "Survey_Result__c_16"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
                "Survey_Result__c_16"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
                "Survey_Result__c_16"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
                "getFirstPhysicalMeasurement_2"."Completion_Status_Timestamp__c" AS "FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
                "getFirstPhysicalMeasurement_2"."Id" AS "FlowRecordLookup.First_Remote_Physical_Measurement.Id",
                "getFirstPhysicalMeasurement_2"."__ppsc_match",
                TRUE AS "__ppsc_lookup_known"
              FROM (
                SELECT
                  "Survey_Result__c_15"."Id",
                  "Survey_Result__c_15"."Participant__c",
                  "Survey_Result__c_15"."Survey_Index_Number__c",
                  "Survey_Result__c_15"."Completion_Status__c",
                  "Survey_Result__c_15"."Consent_Status__c",
                  "Survey_Result__c_15"."Completion_Status_Timestamp__c",
                  "Survey_Result__c_15"."California_Signature__c",
                  "Survey_Result__c_15"."Participant__r.AccountId",
                  "Survey_Result__c_15"."Participant__r.Birthdate",
                  "Survey_Result__c_15"."Participant__r.Account.Id",
                  "Survey_Result__c_15"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                  "Survey_Result__c_15"."Participant__r.Account.CABOR_Completion_Date__c",
                  "Survey_Result__c_15"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                  "Survey_Result__c_15"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                  "Survey_Result__c_15"."Participant__r.Account.EHR_Consent_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                  "Survey_Result__c_15"."Participant__r.Account.Basics_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.Overall_Health_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.Lifestyle_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                  "Survey_Result__c_15"."Participant__r.Account.HC_Access_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.Life_Functioning_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.EH_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.Behavioral_Health_Completion__c",
                  "Survey_Result__c_15"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                  "Survey_Result__c_15"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                  "Survey_Result__c_15"."__ppsc_flow_row",
                  "Survey_Result__c_15"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                  "Survey_Result__c_15"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                  "Survey_Result__c_15"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                  "Survey_Result__c_15"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                  "Survey_Result__c_15"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                  "Survey_Result__c_15"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                  "Survey_Result__c_15"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
                  "Survey_Result__c_15"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                  "Survey_Result__c_15"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
                  "Survey_Result__c_15"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
                  "Survey_Result__c_15"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
                  "Survey_Result__c_15"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
                  "Survey_Result__c_15"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.Id"
                FROM (
                  SELECT
                    *
                  FROM (
                    SELECT
                      "Survey_Result__c_13"."Id",
                      "Survey_Result__c_13"."Participant__c",
                      "Survey_Result__c_13"."Survey_Index_Number__c",
                      "Survey_Result__c_13"."Completion_Status__c",
                      "Survey_Result__c_13"."Consent_Status__c",
                      "Survey_Result__c_13"."Completion_Status_Timestamp__c",
                      "Survey_Result__c_13"."California_Signature__c",
                      "Survey_Result__c_13"."Participant__r.AccountId",
                      "Survey_Result__c_13"."Participant__r.Birthdate",
                      "Survey_Result__c_13"."Participant__r.Account.Id",
                      "Survey_Result__c_13"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                      "Survey_Result__c_13"."Participant__r.Account.CABOR_Completion_Date__c",
                      "Survey_Result__c_13"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                      "Survey_Result__c_13"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                      "Survey_Result__c_13"."Participant__r.Account.EHR_Consent_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                      "Survey_Result__c_13"."Participant__r.Account.Basics_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.Overall_Health_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.Lifestyle_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                      "Survey_Result__c_13"."Participant__r.Account.HC_Access_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.Life_Functioning_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.EH_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.Behavioral_Health_Completion__c",
                      "Survey_Result__c_13"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                      "Survey_Result__c_13"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                      "Survey_Result__c_13"."__ppsc_flow_row",
                      "Survey_Result__c_13"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                      "Survey_Result__c_13"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                      "Survey_Result__c_13"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                      "Survey_Result__c_13"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                      "Survey_Result__c_13"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                      "Survey_Result__c_13"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                      "Survey_Result__c_13"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
                      "Survey_Result__c_13"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                      IF(
                        TRUE
                        AND (
                          COALESCE(
                            SUM("Survey_Result__c_13"."__ppsc_match") OVER (
                              PARTITION BY "Survey_Result__c_13"."__ppsc_flow_row"
                              ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                            ),
                            0
                          ) <= 1
                        ),
                        "Survey_Result__c_13"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
                        CAST(NULL AS TIMESTAMP)
                      ) AS "FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
                      "Survey_Result__c_13"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
                      "Survey_Result__c_13"."__ppsc_match",
                      "Survey_Result__c_13"."__ppsc_lookup_known",
                      COALESCE(
                        SUM("Survey_Result__c_13"."__ppsc_match") OVER (
                          PARTITION BY "Survey_Result__c_13"."__ppsc_flow_row"
                          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                        ),
                        0
                      ) AS "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
                      ROW_NUMBER() OVER (PARTITION BY "Survey_Result__c_13"."__ppsc_flow_row") - 1 AS "__ppsc_rank",
                      TRUE
                      AND (
                        COALESCE(
                          SUM("Survey_Result__c_13"."__ppsc_match") OVER (
                            PARTITION BY "Survey_Result__c_13"."__ppsc_flow_row"
                            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                          ),
                          0
                        ) <= 1
                      ) AS "__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
                      TRUE
                      AND (
                        COALESCE(
                          SUM("Survey_Result__c_13"."__ppsc_match") OVER (
                            PARTITION BY "Survey_Result__c_13"."__ppsc_flow_row"
                            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                          ),
                          0
                        ) <= 1
                      ) AS "__known.FlowRecordLookup.Pediatric_Permission_For_Assent.Id"
                    FROM (
                      SELECT
                        "Survey_Result__c_12"."Id",
                        "Survey_Result__c_12"."Participant__c",
                        "Survey_Result__c_12"."Survey_Index_Number__c",
                        "Survey_Result__c_12"."Completion_Status__c",
                        "Survey_Result__c_12"."Consent_Status__c",
                        "Survey_Result__c_12"."Completion_Status_Timestamp__c",
                        "Survey_Result__c_12"."California_Signature__c",
                        "Survey_Result__c_12"."Participant__r.AccountId",
                        "Survey_Result__c_12"."Participant__r.Birthdate",
                        "Survey_Result__c_12"."Participant__r.Account.Id",
                        "Survey_Result__c_12"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                        "Survey_Result__c_12"."Participant__r.Account.CABOR_Completion_Date__c",
                        "Survey_Result__c_12"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                        "Survey_Result__c_12"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                        "Survey_Result__c_12"."Participant__r.Account.EHR_Consent_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                        "Survey_Result__c_12"."Participant__r.Account.Basics_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.Overall_Health_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.Lifestyle_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                        "Survey_Result__c_12"."Participant__r.Account.HC_Access_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.Life_Functioning_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.EH_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.Behavioral_Health_Completion__c",
                        "Survey_Result__c_12"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                        "Survey_Result__c_12"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                        "Survey_Result__c_12"."__ppsc_flow_row",
                        "Survey_Result__c_12"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                        "Survey_Result__c_12"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                        "Survey_Result__c_12"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                        "Survey_Result__c_12"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                        "Survey_Result__c_12"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                        "Survey_Result__c_12"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                        "Survey_Result__c_12"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
                        "Survey_Result__c_12"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                        "Get_Permission_1007_2"."California_Signature__c" AS "FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
                        "Get_Permission_1007_2"."Id" AS "FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
                        "Get_Permission_1007_2"."__ppsc_match",
                        TRUE AS "__ppsc_lookup_known"
                      FROM (
                        SELECT
                          "Survey_Result__c_11"."Id",
                          "Survey_Result__c_11"."Participant__c",
                          "Survey_Result__c_11"."Survey_Index_Number__c",
                          "Survey_Result__c_11"."Completion_Status__c",
                          "Survey_Result__c_11"."Consent_Status__c",
                          "Survey_Result__c_11"."Completion_Status_Timestamp__c",
                          "Survey_Result__c_11"."California_Signature__c",
                          "Survey_Result__c_11"."Participant__r.AccountId",
                          "Survey_Result__c_11"."Participant__r.Birthdate",
                          "Survey_Result__c_11"."Participant__r.Account.Id",
                          "Survey_Result__c_11"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                          "Survey_Result__c_11"."Participant__r.Account.CABOR_Completion_Date__c",
                          "Survey_Result__c_11"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                          "Survey_Result__c_11"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                          "Survey_Result__c_11"."Participant__r.Account.EHR_Consent_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                          "Survey_Result__c_11"."Participant__r.Account.Basics_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.Overall_Health_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.Lifestyle_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                          "Survey_Result__c_11"."Participant__r.Account.HC_Access_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.Life_Functioning_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.EH_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.Behavioral_Health_Completion__c",
                          "Survey_Result__c_11"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                          "Survey_Result__c_11"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                          "Survey_Result__c_11"."__ppsc_flow_row",
                          "Survey_Result__c_11"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                          "Survey_Result__c_11"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                          "Survey_Result__c_11"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                          "Survey_Result__c_11"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                          "Survey_Result__c_11"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                          "Survey_Result__c_11"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                          "Survey_Result__c_11"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
                          "Survey_Result__c_11"."__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id"
                        FROM (
                          SELECT
                            *
                          FROM (
                            SELECT
                              "Survey_Result__c_9"."Id",
                              "Survey_Result__c_9"."Participant__c",
                              "Survey_Result__c_9"."Survey_Index_Number__c",
                              "Survey_Result__c_9"."Completion_Status__c",
                              "Survey_Result__c_9"."Consent_Status__c",
                              "Survey_Result__c_9"."Completion_Status_Timestamp__c",
                              "Survey_Result__c_9"."California_Signature__c",
                              "Survey_Result__c_9"."Participant__r.AccountId",
                              "Survey_Result__c_9"."Participant__r.Birthdate",
                              "Survey_Result__c_9"."Participant__r.Account.Id",
                              "Survey_Result__c_9"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                              "Survey_Result__c_9"."Participant__r.Account.CABOR_Completion_Date__c",
                              "Survey_Result__c_9"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                              "Survey_Result__c_9"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                              "Survey_Result__c_9"."Participant__r.Account.EHR_Consent_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                              "Survey_Result__c_9"."Participant__r.Account.Basics_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.Overall_Health_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.Lifestyle_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                              "Survey_Result__c_9"."Participant__r.Account.HC_Access_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.Life_Functioning_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.EH_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.Behavioral_Health_Completion__c",
                              "Survey_Result__c_9"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                              "Survey_Result__c_9"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                              "Survey_Result__c_9"."__ppsc_flow_row",
                              "Survey_Result__c_9"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                              "Survey_Result__c_9"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                              "Survey_Result__c_9"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                              "Survey_Result__c_9"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                              "Survey_Result__c_9"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                              "Survey_Result__c_9"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                              "Survey_Result__c_9"."__ppsc_match",
                              "Survey_Result__c_9"."__ppsc_lookup_known",
                              COALESCE(
                                SUM("Survey_Result__c_9"."__ppsc_match") OVER (
                                  PARTITION BY "Survey_Result__c_9"."__ppsc_flow_row"
                                  ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                                ),
                                0
                              ) AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.match_count",
                              ROW_NUMBER() OVER (
                                PARTITION BY "Survey_Result__c_9"."__ppsc_flow_row"
                                ORDER BY "Survey_Result__c_9"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
                              ) - 1 AS "__ppsc_rank",
                              TRUE
                              AND (
                                COALESCE(
                                  SUM("Survey_Result__c_9"."__ppsc_match") OVER (
                                    PARTITION BY "Survey_Result__c_9"."__ppsc_flow_row", "Survey_Result__c_9"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c"
                                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                                  ),
                                  0
                                ) <= 1
                              ) AS "__known.FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id"
                            FROM (
                              SELECT
                                "Survey_Result__c_8"."Id",
                                "Survey_Result__c_8"."Participant__c",
                                "Survey_Result__c_8"."Survey_Index_Number__c",
                                "Survey_Result__c_8"."Completion_Status__c",
                                "Survey_Result__c_8"."Consent_Status__c",
                                "Survey_Result__c_8"."Completion_Status_Timestamp__c",
                                "Survey_Result__c_8"."California_Signature__c",
                                "Survey_Result__c_8"."Participant__r.AccountId",
                                "Survey_Result__c_8"."Participant__r.Birthdate",
                                "Survey_Result__c_8"."Participant__r.Account.Id",
                                "Survey_Result__c_8"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                "Survey_Result__c_8"."Participant__r.Account.CABOR_Completion_Date__c",
                                "Survey_Result__c_8"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                "Survey_Result__c_8"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                "Survey_Result__c_8"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                "Survey_Result__c_8"."Participant__r.Account.Basics_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.Overall_Health_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.Lifestyle_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                "Survey_Result__c_8"."Participant__r.Account.HC_Access_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.EH_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.Behavioral_Health_Completion__c",
                                "Survey_Result__c_8"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                "Survey_Result__c_8"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                "Survey_Result__c_8"."__ppsc_flow_row",
                                "Survey_Result__c_8"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                                "Survey_Result__c_8"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                                "Survey_Result__c_8"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                                "Survey_Result__c_8"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                                "getEarliestEgetEarliestEHRConsentHRConsent_2"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent_2"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                                "getEarliestEgetEarliestEHRConsentHRConsent_2"."__ppsc_match",
                                TRUE AS "__ppsc_lookup_known"
                              FROM (
                                SELECT
                                  "Survey_Result__c_7"."Id",
                                  "Survey_Result__c_7"."Participant__c",
                                  "Survey_Result__c_7"."Survey_Index_Number__c",
                                  "Survey_Result__c_7"."Completion_Status__c",
                                  "Survey_Result__c_7"."Consent_Status__c",
                                  "Survey_Result__c_7"."Completion_Status_Timestamp__c",
                                  "Survey_Result__c_7"."California_Signature__c",
                                  "Survey_Result__c_7"."Participant__r.AccountId",
                                  "Survey_Result__c_7"."Participant__r.Birthdate",
                                  "Survey_Result__c_7"."Participant__r.Account.Id",
                                  "Survey_Result__c_7"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                  "Survey_Result__c_7"."Participant__r.Account.CABOR_Completion_Date__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                  "Survey_Result__c_7"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Basics_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Overall_Health_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Lifestyle_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                  "Survey_Result__c_7"."Participant__r.Account.HC_Access_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.EH_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Behavioral_Health_Completion__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                  "Survey_Result__c_7"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                  "Survey_Result__c_7"."__ppsc_flow_row",
                                  "Survey_Result__c_7"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                                  "Survey_Result__c_7"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                                  "Survey_Result__c_7"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                                  "Survey_Result__c_7"."__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id"
                                FROM (
                                  SELECT
                                    *
                                  FROM (
                                    SELECT
                                      "Survey_Result__c_5"."Id",
                                      "Survey_Result__c_5"."Participant__c",
                                      "Survey_Result__c_5"."Survey_Index_Number__c",
                                      "Survey_Result__c_5"."Completion_Status__c",
                                      "Survey_Result__c_5"."Consent_Status__c",
                                      "Survey_Result__c_5"."Completion_Status_Timestamp__c",
                                      "Survey_Result__c_5"."California_Signature__c",
                                      "Survey_Result__c_5"."Participant__r.AccountId",
                                      "Survey_Result__c_5"."Participant__r.Birthdate",
                                      "Survey_Result__c_5"."Participant__r.Account.Id",
                                      "Survey_Result__c_5"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                      "Survey_Result__c_5"."Participant__r.Account.CABOR_Completion_Date__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                      "Survey_Result__c_5"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Basics_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Overall_Health_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Lifestyle_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                      "Survey_Result__c_5"."Participant__r.Account.HC_Access_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.EH_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Behavioral_Health_Completion__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                      "Survey_Result__c_5"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                      "Survey_Result__c_5"."__ppsc_flow_row",
                                      "Survey_Result__c_5"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                                      "Survey_Result__c_5"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                                      "Survey_Result__c_5"."__ppsc_match",
                                      "Survey_Result__c_5"."__ppsc_lookup_known",
                                      COALESCE(
                                        SUM("Survey_Result__c_5"."__ppsc_match") OVER (
                                          PARTITION BY "Survey_Result__c_5"."__ppsc_flow_row"
                                          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                                        ),
                                        0
                                      ) AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.match_count",
                                      ROW_NUMBER() OVER (
                                        PARTITION BY "Survey_Result__c_5"."__ppsc_flow_row"
                                        ORDER BY "Survey_Result__c_5"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
                                      ) - 1 AS "__ppsc_rank",
                                      TRUE
                                      AND (
                                        COALESCE(
                                          SUM("Survey_Result__c_5"."__ppsc_match") OVER (
                                            PARTITION BY "Survey_Result__c_5"."__ppsc_flow_row", "Survey_Result__c_5"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c"
                                            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                                          ),
                                          0
                                        ) <= 1
                                      ) AS "__known.FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id"
                                    FROM (
                                      SELECT
                                        "Survey_Result__c_4"."Id",
                                        "Survey_Result__c_4"."Participant__c",
                                        "Survey_Result__c_4"."Survey_Index_Number__c",
                                        "Survey_Result__c_4"."Completion_Status__c",
                                        "Survey_Result__c_4"."Consent_Status__c",
                                        "Survey_Result__c_4"."Completion_Status_Timestamp__c",
                                        "Survey_Result__c_4"."California_Signature__c",
                                        "Survey_Result__c_4"."Participant__r.AccountId",
                                        "Survey_Result__c_4"."Participant__r.Birthdate",
                                        "Survey_Result__c_4"."Participant__r.Account.Id",
                                        "Survey_Result__c_4"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                        "Survey_Result__c_4"."Participant__r.Account.CABOR_Completion_Date__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                        "Survey_Result__c_4"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Basics_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Overall_Health_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Lifestyle_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                        "Survey_Result__c_4"."Participant__r.Account.HC_Access_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.EH_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Behavioral_Health_Completion__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                        "Survey_Result__c_4"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                        "Survey_Result__c_4"."__ppsc_flow_row",
                                        "getEarliestPrimaryConsent_2"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                                        "getEarliestPrimaryConsent_2"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                                        "getEarliestPrimaryConsent_2"."__ppsc_match",
                                        TRUE AS "__ppsc_lookup_known"
                                      FROM (
                                        SELECT
                                          "Survey_Result__c_3"."Id",
                                          "Survey_Result__c_3"."Participant__c",
                                          "Survey_Result__c_3"."Survey_Index_Number__c",
                                          "Survey_Result__c_3"."Completion_Status__c",
                                          "Survey_Result__c_3"."Consent_Status__c",
                                          "Survey_Result__c_3"."Completion_Status_Timestamp__c",
                                          "Survey_Result__c_3"."California_Signature__c",
                                          "Survey_Result__c_3"."Participant__r.AccountId",
                                          "Survey_Result__c_3"."Participant__r.Birthdate",
                                          "Survey_Result__c_3"."Participant__r.Account.Id",
                                          "Survey_Result__c_3"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                          "Survey_Result__c_3"."Participant__r.Account.CABOR_Completion_Date__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                          "Survey_Result__c_3"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Basics_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Overall_Health_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Lifestyle_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                          "Survey_Result__c_3"."Participant__r.Account.HC_Access_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.EH_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Behavioral_Health_Completion__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                          "Survey_Result__c_3"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                          ROW_NUMBER() OVER () - 1 AS "__ppsc_flow_row"
                                        FROM (
                                          SELECT
                                            "Survey_Result__c_2"."Id",
                                            "Survey_Result__c_2"."Participant__c",
                                            "Survey_Result__c_2"."Survey_Index_Number__c",
                                            "Survey_Result__c_2"."Completion_Status__c",
                                            "Survey_Result__c_2"."Consent_Status__c",
                                            "Survey_Result__c_2"."Completion_Status_Timestamp__c",
                                            "Survey_Result__c_2"."California_Signature__c",
                                            "Contact"."AccountId" AS "Participant__r.AccountId",
                                            "Contact"."Birthdate" AS "Participant__r.Birthdate",
                                            "Account"."Id" AS "Participant__r.Account.Id",
                                            "Account"."Age_at_Time_of_Consent__pc" AS "Participant__r.Account.Age_at_Time_of_Consent__pc",
                                            "Account"."CABOR_Completion_Date__c" AS "Participant__r.Account.CABOR_Completion_Date__c",
                                            "Account"."Earliest_Primary_Consent_Date_for_Report__c" AS "Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                            "Account"."Latest_Primary_Consent_Date_for_Report__c" AS "Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                            "Account"."EHR_Consent_Date_Time__c" AS "Participant__r.Account.EHR_Consent_Date_Time__c",
                                            "Account"."EHR_Reconsent_Date_Time__c" AS "Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                            "Account"."Update_to_Primary_Consent_Completed__c" AS "Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                            "Account"."Basics_Date_Time__c" AS "Participant__r.Account.Basics_Date_Time__c",
                                            "Account"."Overall_Health_Date_Time__c" AS "Participant__r.Account.Overall_Health_Date_Time__c",
                                            "Account"."Lifestyle_Date_Time__c" AS "Participant__r.Account.Lifestyle_Date_Time__c",
                                            "Account"."Personal_and_Family_History_Complete__c" AS "Participant__r.Account.Personal_and_Family_History_Complete__c",
                                            "Account"."HC_Access_Date_Time__c" AS "Participant__r.Account.HC_Access_Date_Time__c",
                                            "Account"."Life_Functioning_Date_Time__c" AS "Participant__r.Account.Life_Functioning_Date_Time__c",
                                            "Account"."First_Physical_Measurement_Date_Time__c" AS "Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                            "Account"."Last_Physical_Measurement_Date_Time__c" AS "Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                            "Account"."EH_Date_Time__c" AS "Participant__r.Account.EH_Date_Time__c",
                                            "Account"."Behavioral_Health_Completion__c" AS "Participant__r.Account.Behavioral_Health_Completion__c",
                                            "Account"."Environmental_Exposures_Date_Time__c" AS "Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                            "Account"."Social_Determinants_of_Health_Completion__c" AS "Participant__r.Account.Social_Determinants_of_Health_Completion__c"
                                          FROM (
                                            SELECT
                                              "Survey_Result__c"."Id",
                                              "Survey_Result__c"."Participant__c",
                                              "Survey_Result__c"."Survey_Index_Number__c",
                                              "Survey_Result__c"."Completion_Status__c",
                                              "Survey_Result__c"."Consent_Status__c",
                                              "Survey_Result__c"."Completion_Status_Timestamp__c",
                                              "Survey_Result__c"."California_Signature__c"
                                            FROM "Survey_Result__c" AS "Survey_Result__c"
                                          ) AS "Survey_Result__c_2"
                                          LEFT OUTER JOIN "Contact" AS "Contact"
                                            ON "Survey_Result__c_2"."Participant__c" = "Contact"."Id"
                                          LEFT OUTER JOIN "Account" AS "Account"
                                            ON "Contact"."AccountId" = "Account"."Id"
                                        ) AS "Survey_Result__c_3"
                                      ) AS "Survey_Result__c_4"
                                      LEFT OUTER JOIN (
                                        SELECT
                                          "getEarliestPrimaryConsent"."California_Signature__c",
                                          "getEarliestPrimaryConsent"."Completion_Status__c",
                                          "getEarliestPrimaryConsent"."Completion_Status_Timestamp__c",
                                          "getEarliestPrimaryConsent"."Consent_Revoked__c",
                                          "getEarliestPrimaryConsent"."Consent_Status__c",
                                          "getEarliestPrimaryConsent"."Consent_Status_Timestamp__c",
                                          "getEarliestPrimaryConsent"."Id",
                                          "getEarliestPrimaryConsent"."is_current",
                                          "getEarliestPrimaryConsent"."loaded_at",
                                          "getEarliestPrimaryConsent"."Participant__c",
                                          "getEarliestPrimaryConsent"."Survey_Index_Number__c",
                                          "getEarliestPrimaryConsent"."valid_from",
                                          "getEarliestPrimaryConsent"."valid_to",
                                          1 AS "__ppsc_match"
                                        FROM "getEarliestPrimaryConsent" AS "getEarliestPrimaryConsent"
                                      ) AS "getEarliestPrimaryConsent_2"
                                        ON (
                                          COALESCE("getEarliestPrimaryConsent_2"."Survey_Index_Number__c" = '1001', FALSE)
                                          OR COALESCE("getEarliestPrimaryConsent_2"."Survey_Index_Number__c" = '1002', FALSE)
                                        )
                                        AND COALESCE(
                                          "getEarliestPrimaryConsent_2"."Participant__c" = "Survey_Result__c_4"."Participant__c",
                                          FALSE
                                        )
                                        AND COALESCE("getEarliestPrimaryConsent_2"."Consent_Status__c" = 'Yes', FALSE)
                                        AND COALESCE("getEarliestPrimaryConsent_2"."Id" <> "Survey_Result__c_4"."Id", FALSE)
                                        AND COALESCE("Survey_Result__c_4"."Completion_Status__c" = 'Complete', FALSE)
                                        AND NOT (
                                          FALSE
                                        )
                                        AND (
                                          COALESCE("Survey_Result__c_4"."Survey_Index_Number__c" = '1001', FALSE)
                                          OR COALESCE("Survey_Result__c_4"."Survey_Index_Number__c" = '1002', FALSE)
                                        )
                                        AND COALESCE("Survey_Result__c_4"."Consent_Status__c" = 'Yes', FALSE)
                                    ) AS "Survey_Result__c_5"
                                  ) AS "Survey_Result__c_6"
                                  WHERE
                                    "Survey_Result__c_6"."__ppsc_rank" = 0
                                ) AS "Survey_Result__c_7"
                              ) AS "Survey_Result__c_8"
                              LEFT OUTER JOIN (
                                SELECT
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."California_Signature__c",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."Completion_Status__c",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."Completion_Status_Timestamp__c",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."Consent_Revoked__c",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."Consent_Status__c",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."Consent_Status_Timestamp__c",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."Id",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."is_current",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."loaded_at",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."Participant__c",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."Survey_Index_Number__c",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."valid_from",
                                  "getEarliestEgetEarliestEHRConsentHRConsent"."valid_to",
                                  1 AS "__ppsc_match"
                                FROM "getEarliestEgetEarliestEHRConsentHRConsent" AS "getEarliestEgetEarliestEHRConsentHRConsent"
                              ) AS "getEarliestEgetEarliestEHRConsentHRConsent_2"
                                ON (
                                  COALESCE(
                                    "getEarliestEgetEarliestEHRConsentHRConsent_2"."Survey_Index_Number__c" = '1003',
                                    FALSE
                                  )
                                  OR COALESCE(
                                    "getEarliestEgetEarliestEHRConsentHRConsent_2"."Survey_Index_Number__c" = '1004',
                                    FALSE
                                  )
                                )
                                AND COALESCE(
                                  "getEarliestEgetEarliestEHRConsentHRConsent_2"."Participant__c" = "Survey_Result__c_8"."Participant__c",
                                  FALSE
                                )
                                AND COALESCE("getEarliestEgetEarliestEHRConsentHRConsent_2"."Consent_Status__c" = 'Yes', FALSE)
                                AND COALESCE(
                                  "getEarliestEgetEarliestEHRConsentHRConsent_2"."Id" <> "Survey_Result__c_8"."Id",
                                  FALSE
                                )
                                AND COALESCE("Survey_Result__c_8"."Completion_Status__c" = 'Complete', FALSE)
                                AND NOT (
                                  FALSE
                                  OR (
                                    (
                                      COALESCE("Survey_Result__c_8"."Survey_Index_Number__c" = '1001', FALSE)
                                      OR COALESCE("Survey_Result__c_8"."Survey_Index_Number__c" = '1002', FALSE)
                                    )
                                    AND COALESCE("Survey_Result__c_8"."Consent_Status__c" = 'Yes', FALSE)
                                  )
                                )
                                AND (
                                  COALESCE("Survey_Result__c_8"."Survey_Index_Number__c" = '1003', FALSE)
                                  OR COALESCE("Survey_Result__c_8"."Survey_Index_Number__c" = '1004', FALSE)
                                )
                                AND COALESCE("Survey_Result__c_8"."Consent_Status__c" = 'Yes', FALSE)
                            ) AS "Survey_Result__c_9"
                          ) AS "Survey_Result__c_10"
                          WHERE
                            "Survey_Result__c_10"."__ppsc_rank" = 0
                        ) AS "Survey_Result__c_11"
                      ) AS "Survey_Result__c_12"
                      LEFT OUTER JOIN (
                        SELECT
                          "Get_Permission_1007"."California_Signature__c",
                          "Get_Permission_1007"."Completion_Status__c",
                          "Get_Permission_1007"."Completion_Status_Timestamp__c",
                          "Get_Permission_1007"."Consent_Revoked__c",
                          "Get_Permission_1007"."Consent_Status__c",
                          "Get_Permission_1007"."Consent_Status_Timestamp__c",
                          "Get_Permission_1007"."Id",
                          "Get_Permission_1007"."is_current",
                          "Get_Permission_1007"."loaded_at",
                          "Get_Permission_1007"."Participant__c",
                          "Get_Permission_1007"."Survey_Index_Number__c",
                          "Get_Permission_1007"."valid_from",
                          "Get_Permission_1007"."valid_to",
                          1 AS "__ppsc_match"
                        FROM "Get_Permission_1007" AS "Get_Permission_1007"
                      ) AS "Get_Permission_1007_2"
                        ON COALESCE("Get_Permission_1007_2"."Survey_Index_Number__c" = '1007', FALSE)
                        AND COALESCE("Get_Permission_1007_2"."Consent_Status__c" = 'Yes', FALSE)
                        AND COALESCE(
                          "Get_Permission_1007_2"."Participant__c" = "Survey_Result__c_12"."Participant__c",
                          FALSE
                        )
                        AND COALESCE("Get_Permission_1007_2"."Id" <> "Survey_Result__c_12"."Id", FALSE)
                        AND COALESCE("Survey_Result__c_12"."Completion_Status__c" = 'Complete', FALSE)
                        AND NOT (
                          FALSE
                          OR (
                            (
                              COALESCE("Survey_Result__c_12"."Survey_Index_Number__c" = '1001', FALSE)
                              OR COALESCE("Survey_Result__c_12"."Survey_Index_Number__c" = '1002', FALSE)
                            )
                            AND COALESCE("Survey_Result__c_12"."Consent_Status__c" = 'Yes', FALSE)
                          )
                          OR (
                            (
                              COALESCE("Survey_Result__c_12"."Survey_Index_Number__c" = '1003', FALSE)
                              OR COALESCE("Survey_Result__c_12"."Survey_Index_Number__c" = '1004', FALSE)
                            )
                            AND COALESCE("Survey_Result__c_12"."Consent_Status__c" = 'Yes', FALSE)
                          )
                          OR COALESCE("Survey_Result__c_12"."Survey_Index_Number__c" = '1005', FALSE)
                        )
                        AND COALESCE("Survey_Result__c_12"."Survey_Index_Number__c" = '1008', FALSE)
                        AND (
                          COALESCE("Survey_Result__c_12"."Consent_Status__c" = 'Yes', FALSE)
                          OR COALESCE("Survey_Result__c_12"."Consent_Status__c" = 'N/A', FALSE)
                        )
                    ) AS "Survey_Result__c_13"
                  ) AS "Survey_Result__c_14"
                  WHERE
                    "Survey_Result__c_14"."__ppsc_rank" = 0
                ) AS "Survey_Result__c_15"
              ) AS "Survey_Result__c_16"
              LEFT OUTER JOIN (
                SELECT
                  "getFirstPhysicalMeasurement"."California_Signature__c",
                  "getFirstPhysicalMeasurement"."Completion_Status__c",
                  "getFirstPhysicalMeasurement"."Completion_Status_Timestamp__c",
                  "getFirstPhysicalMeasurement"."Consent_Revoked__c",
                  "getFirstPhysicalMeasurement"."Consent_Status__c",
                  "getFirstPhysicalMeasurement"."Consent_Status_Timestamp__c",
                  "getFirstPhysicalMeasurement"."Id",
                  "getFirstPhysicalMeasurement"."is_current",
                  "getFirstPhysicalMeasurement"."loaded_at",
                  "getFirstPhysicalMeasurement"."Participant__c",
                  "getFirstPhysicalMeasurement"."Survey_Index_Number__c",
                  "getFirstPhysicalMeasurement"."valid_from",
                  "getFirstPhysicalMeasurement"."valid_to",
                  1 AS "__ppsc_match"
                FROM "getFirstPhysicalMeasurement" AS "getFirstPhysicalMeasurement"
              ) AS "getFirstPhysicalMeasurement_2"
                ON COALESCE("getFirstPhysicalMeasurement_2"."Survey_Index_Number__c" = '2009', FALSE)
                AND COALESCE(
                  "getFirstPhysicalMeasurement_2"."Participant__c" = "Survey_Result__c_16"."Participant__c",
                  FALSE
                )
                AND COALESCE("Survey_Result__c_16"."Completion_Status__c" = 'Complete', FALSE)
                AND NOT (
                  FALSE
                  OR (
                    (
                      COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '1001', FALSE)
                      OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '1002', FALSE)
                    )
                    AND COALESCE("Survey_Result__c_16"."Consent_Status__c" = 'Yes', FALSE)
                  )
                  OR (
                    (
                      COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '1003', FALSE)
                      OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '1004', FALSE)
                    )
                    AND COALESCE("Survey_Result__c_16"."Consent_Status__c" = 'Yes', FALSE)
                  )
                  OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '1005', FALSE)
                  OR (
                    COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '1008', FALSE)
                    AND (
                      COALESCE("Survey_Result__c_16"."Consent_Status__c" = 'Yes', FALSE)
                      OR COALESCE("Survey_Result__c_16"."Consent_Status__c" = 'N/A', FALSE)
                    )
                  )
                  OR (
                    COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2001', FALSE)
                    OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2002', FALSE)
                  )
                  OR (
                    COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2003', FALSE)
                    OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2004', FALSE)
                  )
                  OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2005', FALSE)
                  OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2006', FALSE)
                  OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2007', FALSE)
                  OR COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2008', FALSE)
                )
                AND COALESCE("Survey_Result__c_16"."Survey_Index_Number__c" = '2009', FALSE)
            ) AS "Survey_Result__c_17"
          ) AS "Survey_Result__c_18"
          WHERE
            "Survey_Result__c_18"."__ppsc_rank" = 0
        ) AS "Survey_Result__c_19"
      ) AS "Survey_Result__c_20"
    ) AS "Survey_Result__c_21"
  )
  SELECT
    "Flow_Context"."Id" AS "Record.Id",
    "Flow_Context"."Participant__r.Account.Id" AS "Account.Id",
    "Flow_Context"."Participant__c",
    "Flow_Context"."Survey_Index_Number__c",
    "Flow_Context"."Completion_Status_Timestamp__c",
    "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
      )
      AND (
        "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
      )
      THEN CAST("Flow_Context"."FlowFormula_Age_At_Execution" AS DECIMAL(3, 0))
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
        OR (
          "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
        )
      )
      THEN CAST("Flow_Context"."FlowFormula_Age_At_Execution" AS DECIMAL(3, 0))
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
        AND (
          COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
        )
      )
      AND NOT (
        FALSE
      )
      AND (
        (
          "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
        )
        AND (
          "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
        )
      )
      THEN CAST("Flow_Context"."FlowFormula_Age_At_Execution" AS DECIMAL(3, 0))
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
        AND (
          COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
        )
      )
      AND NOT (
        FALSE
        OR (
          (
            "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
          )
          AND (
            "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
          )
        )
      )
      THEN CAST("Flow_Context"."FlowFormula_Age_At_Execution" AS DECIMAL(3, 0))
      ELSE "Flow_Context"."Participant__r.Account.Age_at_Time_of_Consent__pc"
    END AS "Age_at_Time_of_Consent__pc",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
      )
      AND (
        "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
      )
      THEN "Flow_Context"."California_Signature__c"
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
        OR (
          "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
        )
      )
      THEN "Flow_Context"."California_Signature__c"
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
        AND (
          COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
        )
      )
      AND NOT (
        FALSE
      )
      AND (
        (
          "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
        )
        AND (
          "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
        )
      )
      THEN "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
        AND (
          COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
        )
      )
      AND NOT (
        FALSE
        OR (
          (
            "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
          )
          AND (
            "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
          )
        )
      )
      THEN "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
      ELSE "Flow_Context"."Participant__r.Account.CABOR_Completion_Date__c"
    END AS "CABOR_Completion_Date__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
        OR (
          "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
        )
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
        AND (
          COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
        )
      )
      AND NOT (
        FALSE
        OR (
          (
            "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
          )
          AND (
            "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
          )
        )
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c"
    END AS "Earliest_Primary_Consent_Date_for_Report__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
      )
      AND (
        "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
        OR (
          "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
        )
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
        AND (
          COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
        )
      )
      AND NOT (
        FALSE
      )
      AND (
        (
          "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
        )
        AND (
          "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
        )
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
        AND (
          COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
        )
      )
      AND NOT (
        FALSE
        OR (
          (
            "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
          )
          AND (
            "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
          )
        )
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c"
    END AS "Latest_Primary_Consent_Date_for_Report__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
        OR (
          "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NOT NULL
        )
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.EHR_Consent_Date_Time__c"
    END AS "EHR_Consent_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
      )
      AND (
        (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
        )
        AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
      )
      AND NOT (
        FALSE
      )
      AND (
        "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NOT NULL
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.EHR_Reconsent_Date_Time__c"
    END AS "EHR_Reconsent_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Update_to_Primary_Consent_Completed__c"
    END AS "Update_to_Primary_Consent_Completed__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Basics_Date_Time__c"
    END AS "Basics_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
      )
      AND (
        COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
      )
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Overall_Health_Date_Time__c"
    END AS "Overall_Health_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Lifestyle_Date_Time__c"
    END AS "Lifestyle_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Personal_and_Family_History_Complete__c"
    END AS "Personal_and_Family_History_Complete__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2007', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.HC_Access_Date_Time__c"
    END AS "HC_Access_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2007', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2008', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Life_Functioning_Date_Time__c"
    END AS "Life_Functioning_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2007', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2008', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2009', FALSE)
      THEN "Flow_Context"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.First_Physical_Measurement_Date_Time__c"
    END AS "First_Physical_Measurement_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2007', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2008', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2009', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c"
    END AS "Last_Physical_Measurement_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2007', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2008', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2009', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2010', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.EH_Date_Time__c"
    END AS "EH_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2007', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2008', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2009', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2010', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2011', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Behavioral_Health_Completion__c"
    END AS "Behavioral_Health_Completion__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2007', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2008', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2009', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2010', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2011', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2012', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Environmental_Exposures_Date_Time__c"
    END AS "Environmental_Exposures_Date_Time__c",
    CASE
      WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
      AND NOT (
        FALSE
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2001', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2002', FALSE)
        )
        OR (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '2003', FALSE)
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2004', FALSE)
        )
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2005', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2006', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2007', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2008', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2009', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2010', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2011', FALSE)
        OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '2012', FALSE)
      )
      AND COALESCE("Flow_Context"."Survey_Index_Number__c" = '2013', FALSE)
      THEN "Flow_Context"."Completion_Status_Timestamp__c"
      ELSE "Flow_Context"."Participant__r.Account.Social_Determinants_of_Health_Completion__c"
    END AS "Social_Determinants_of_Health_Completion__c",
    COALESCE(
      TRUE
      AND CASE
        WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
        AND NOT (
          FALSE
        )
        AND (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        AND NOT (
          FALSE
        )
        AND (
          "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
        )
        THEN TRUE
        WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
        AND NOT (
          FALSE
        )
        AND (
          (
            COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
            OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
          )
          AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
        )
        AND NOT (
          FALSE
          OR (
            "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
          )
        )
        THEN TRUE
        WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
        AND NOT (
          FALSE
          OR (
            (
              COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
              OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
            )
            AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          )
          OR (
            (
              COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
              OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
            )
            AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          )
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        )
        AND (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        AND NOT (
          FALSE
        )
        AND (
          (
            "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
          )
          AND (
            "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
          )
        )
        THEN "Flow_Context"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
        WHEN COALESCE("Flow_Context"."Completion_Status__c" = 'Complete', FALSE)
        AND NOT (
          FALSE
          OR (
            (
              COALESCE("Flow_Context"."Survey_Index_Number__c" = '1001', FALSE)
              OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1002', FALSE)
            )
            AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          )
          OR (
            (
              COALESCE("Flow_Context"."Survey_Index_Number__c" = '1003', FALSE)
              OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1004', FALSE)
            )
            AND COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
          )
          OR COALESCE("Flow_Context"."Survey_Index_Number__c" = '1005', FALSE)
        )
        AND (
          COALESCE("Flow_Context"."Survey_Index_Number__c" = '1008', FALSE)
          AND (
            COALESCE("Flow_Context"."Consent_Status__c" = 'Yes', FALSE)
            OR COALESCE("Flow_Context"."Consent_Status__c" = 'N/A', FALSE)
          )
        )
        AND NOT (
          FALSE
          OR (
            (
              "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NOT NULL
            )
            AND (
              "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NOT NULL
            )
          )
        )
        THEN "Flow_Context"."__known.FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
        ELSE TRUE
      END,
      FALSE
    ) AS "CABOR_Completion_Date__c_is_deterministic"
  FROM "Flow_Context" AS "Flow_Context"
) AS Comparison_Rows;

-- rollups
SELECT
  "Comparison_Rows"."Account.Id", /* Source identity: Account.Id; source: Account.Id */
  "Comparison_Rows"."PersonContactId", /* Source identity: PersonContactId; source: Account.PersonContactId */
  "Comparison_Rows"."EHR_Authorized__pc", /* Ehr authorized; source: Account.EHR_Authorized__pc */
  "Comparison_Rows"."Count_of_Completed_EHR_Auth__pc", /* Count of completed ehr auth; source: Account.Count_of_Completed_EHR_Auth__pc */
  "Comparison_Rows"."Count_of_Completed_Primary_Consent__pc", /* Count of completed primary consent; source: Account.Count_of_Completed_Primary_Consent__pc */
  "Comparison_Rows"."Count_of_Completed_Reconsent__pc", /* Count of completed reconsent; source: Account.Count_of_Completed_Reconsent__pc */
  "Comparison_Rows"."PPI_2_Completion_Count__pc", /* Ppi 2 completion count; source: Account.PPI_2_Completion_Count__pc */
  "Comparison_Rows"."PPI_3_Completion_Count__pc", /* Ppi 3 completion count; source: Account.PPI_3_Completion_Count__pc */
  "Comparison_Rows"."EHR_Consent_Active__pc", /* Ehr consent active; source: Account.EHR_Consent_Active__pc */
  "Comparison_Rows"."EHR_Consent_Declined__pc", /* Ehr consent declined; source: Account.EHR_Consent_Declined__pc */
  "Comparison_Rows"."PP1_Basics_Survey_Complete__pc", /* Pp1 basics survey complete; source: Account.PP1_Basics_Survey_Complete__pc */
  "Comparison_Rows"."Re_Consent_Declined__pc", /* Re consent declined; source: Account.Re_Consent_Declined__pc */
  "Comparison_Rows"."Re_consent_Active__pc", /* Re consent active; source: Account.Re_consent_Active__pc */
  "Comparison_Rows"."Primary_Consent_Declined__pc", /* Primary consent declined; source: Account.Primary_Consent_Declined__pc */
  "Comparison_Rows"."EHR_Consent_Ever__pc", /* Ehr consent ever; source: Account.EHR_Consent_Ever__pc */
  "Comparison_Rows"."Assent_Completion_Count__pc", /* Assent completion count; source: Account.Assent_Completion_Count__pc */
  "Comparison_Rows"."Pediatric_Permission_Completion_Count__pc", /* Pediatric permission completion count; source: Account.Pediatric_Permission_Completion_Count__pc */
  "Comparison_Rows"."X0_6_Peds_Permission_Count__pc", /* X0 6 peds permission count; source: Account.X0_6_Peds_Permission_Count__pc */
  "Comparison_Rows"."X0_6_Peds_Permission_Declined_Count__pc", /* X0 6 peds permission declined count; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
  "Comparison_Rows"."X0_6_Peds_Permission_Revoked_Count__pc", /* X0 6 peds permission revoked count; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
  "Comparison_Rows"."EHR_Pediatric_Complete__pc" /* Ehr pediatric complete; source: Account.EHR_Pediatric_Complete__pc */
FROM (
  WITH "Account_At_Snapshot" AS (
    SELECT
      "account_history"."age_at_time_of_consent__pc" AS "Age_at_Time_of_Consent__pc",
      "account_history"."assent_completion_count__pc" AS "Assent_Completion_Count__pc",
      "account_history"."basics_date_time__c" AS "Basics_Date_Time__c",
      "account_history"."behavioral_health_completion__c" AS "Behavioral_Health_Completion__c",
      "account_history"."cabor_completion_date__c" AS "CABOR_Completion_Date__c",
      "account_history"."count_of_completed_ehr_auth__pc" AS "Count_of_Completed_EHR_Auth__pc",
      "account_history"."count_of_completed_primary_consent__pc" AS "Count_of_Completed_Primary_Consent__pc",
      "account_history"."count_of_completed_reconsent__pc" AS "Count_of_Completed_Reconsent__pc",
      "account_history"."earliest_primary_consent_date_for_report__c" AS "Earliest_Primary_Consent_Date_for_Report__c",
      "account_history"."eh_date_time__c" AS "EH_Date_Time__c",
      "account_history"."ehr_authorized__pc" AS "EHR_Authorized__pc",
      "account_history"."ehr_consent_active__pc" AS "EHR_Consent_Active__pc",
      "account_history"."ehr_consent_date_time__c" AS "EHR_Consent_Date_Time__c",
      "account_history"."ehr_consent_declined__pc" AS "EHR_Consent_Declined__pc",
      "account_history"."ehr_consent_ever__pc" AS "EHR_Consent_Ever__pc",
      "account_history"."ehr_pediatric_complete__pc" AS "EHR_Pediatric_Complete__pc",
      "account_history"."ehr_reconsent_date_time__c" AS "EHR_Reconsent_Date_Time__c",
      "account_history"."environmental_exposures_date_time__c" AS "Environmental_Exposures_Date_Time__c",
      "account_history"."first_physical_measurement_date_time__c" AS "First_Physical_Measurement_Date_Time__c",
      "account_history"."hc_access_date_time__c" AS "HC_Access_Date_Time__c",
      "account_history"."id" AS "Id",
      "account_history"."is_current",
      "account_history"."ispersonaccount" AS "IsPersonAccount",
      "account_history"."last_physical_measurement_date_time__c" AS "Last_Physical_Measurement_Date_Time__c",
      "account_history"."latest_primary_consent_date_for_report__c" AS "Latest_Primary_Consent_Date_for_Report__c",
      "account_history"."life_functioning_date_time__c" AS "Life_Functioning_Date_Time__c",
      "account_history"."lifestyle_date_time__c" AS "Lifestyle_Date_Time__c",
      "account_history"."loaded_at",
      "account_history"."overall_health_date_time__c" AS "Overall_Health_Date_Time__c",
      "account_history"."pediatric_permission_completion_count__pc" AS "Pediatric_Permission_Completion_Count__pc",
      "account_history"."personal_and_family_history_complete__c" AS "Personal_and_Family_History_Complete__c",
      "account_history"."personcontactid" AS "PersonContactId",
      "account_history"."pp1_basics_survey_complete__pc" AS "PP1_Basics_Survey_Complete__pc",
      "account_history"."ppi_2_completion_count__pc" AS "PPI_2_Completion_Count__pc",
      "account_history"."ppi_3_completion_count__pc" AS "PPI_3_Completion_Count__pc",
      "account_history"."primary_consent_declined__pc" AS "Primary_Consent_Declined__pc",
      "account_history"."re_consent_active__pc" AS "Re_consent_Active__pc",
      "account_history"."re_consent_declined__pc" AS "Re_Consent_Declined__pc",
      "account_history"."social_determinants_of_health_completion__c" AS "Social_Determinants_of_Health_Completion__c",
      "account_history"."update_to_primary_consent_completed__c" AS "Update_to_Primary_Consent_Completed__c",
      "account_history"."valid_from",
      "account_history"."valid_to",
      "account_history"."x0_6_peds_permission_count__pc" AS "X0_6_Peds_Permission_Count__pc",
      "account_history"."x0_6_peds_permission_declined_count__pc" AS "X0_6_Peds_Permission_Declined_Count__pc",
      "account_history"."x0_6_peds_permission_revoked_count__pc" AS "X0_6_Peds_Permission_Revoked_Count__pc"
    FROM "fixture_catalog"."fixture_lake"."account_history" AS "account_history"
    WHERE
      "account_history"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      AND (
        (
          "account_history"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
        )
        OR (
          "account_history"."valid_to" IS NULL
        )
      )
  ), "Survey_Results_At_Execution" AS (
    SELECT
      "survey_results_history"."california_signature__c" AS "California_Signature__c",
      "survey_results_history"."completion_status__c" AS "Completion_Status__c",
      "survey_results_history"."completion_status_timestamp__c" AS "Completion_Status_Timestamp__c",
      "survey_results_history"."consent_revoked__c" AS "Consent_Revoked__c",
      "survey_results_history"."consent_status__c" AS "Consent_Status__c",
      "survey_results_history"."consent_status_timestamp__c" AS "Consent_Status_Timestamp__c",
      "survey_results_history"."id" AS "Id",
      "survey_results_history"."is_current",
      "survey_results_history"."loaded_at",
      "survey_results_history"."participant__c" AS "Participant__c",
      "survey_results_history"."survey_index_number__c" AS "Survey_Index_Number__c",
      "survey_results_history"."valid_from",
      "survey_results_history"."valid_to"
    FROM "fixture_catalog"."fixture_lake"."survey_results_history" AS "survey_results_history"
    WHERE
      "survey_results_history"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      AND (
        (
          "survey_results_history"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
        )
        OR (
          "survey_results_history"."valid_to" IS NULL
        )
      )
  ), "Person_Account" AS (
    SELECT
      "Account_At_Snapshot"."Id",
      "Account_At_Snapshot"."PersonContactId"
    FROM "Account_At_Snapshot" AS "Account_At_Snapshot"
    WHERE
      "Account_At_Snapshot"."IsPersonAccount"
  ), "Survey_Result__c" AS (
    SELECT
      "Survey_Results_At_Execution"."Participant__c",
      "Survey_Results_At_Execution"."Completion_Status__c",
      "Survey_Results_At_Execution"."Survey_Index_Number__c",
      "Survey_Results_At_Execution"."Consent_Status__c",
      "Survey_Results_At_Execution"."Consent_Revoked__c"
    FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution"
  )
  SELECT
    "Person_Account_3"."Account.Id",
    "Person_Account_3"."PersonContactId",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1003'
        )
        THEN 1
        ELSE 0
      END
    ) AS "EHR_Authorized__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1003'
        )
        THEN 1
        ELSE 0
      END
    ) AS "Count_of_Completed_EHR_Auth__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1001'
        )
        THEN 1
        ELSE 0
      END
    ) AS "Count_of_Completed_Primary_Consent__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1005'
        )
        THEN 1
        ELSE 0
      END
    ) AS "Count_of_Completed_Reconsent__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '2005'
        )
        THEN 1
        ELSE 0
      END
    ) AS "PPI_2_Completion_Count__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '2003'
        )
        THEN 1
        ELSE 0
      END
    ) AS "PPI_3_Completion_Count__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'Yes'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND "Person_Account_3"."Survey_Index_Number__c" IN ('1003', '1004')
        THEN 1
        ELSE 0
      END
    ) AS "EHR_Consent_Active__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'No'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND "Person_Account_3"."Survey_Index_Number__c" IN ('1003', '1004')
        THEN 1
        ELSE 0
      END
    ) AS "EHR_Consent_Declined__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND "Person_Account_3"."Survey_Index_Number__c" IN ('2001', '2002')
        THEN 1
        ELSE 0
      END
    ) AS "PP1_Basics_Survey_Complete__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'No'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1005'
        )
        THEN 1
        ELSE 0
      END
    ) AS "Re_Consent_Declined__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'Yes'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1005'
        )
        THEN 1
        ELSE 0
      END
    ) AS "Re_consent_Active__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'No'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND "Person_Account_3"."Survey_Index_Number__c" IN ('1005', '1002')
        THEN 1
        ELSE 0
      END
    ) AS "Primary_Consent_Declined__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'Yes'
        )
        AND "Person_Account_3"."Survey_Index_Number__c" IN ('1003', '1004')
        THEN 1
        ELSE 0
      END
    ) AS "EHR_Consent_Ever__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'Yes'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1008'
        )
        THEN 1
        ELSE 0
      END
    ) AS "Assent_Completion_Count__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'Yes'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1007'
        )
        THEN 1
        ELSE 0
      END
    ) AS "Pediatric_Permission_Completion_Count__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Consent_Status__c" = 'Yes'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1002'
        )
        THEN 1
        ELSE 0
      END
    ) AS "X0_6_Peds_Permission_Count__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Consent_Status__c" = 'No'
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1002'
        )
        THEN 1
        ELSE 0
      END
    ) AS "X0_6_Peds_Permission_Declined_Count__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Consent_Revoked__c" = TRUE
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1002'
        )
        THEN 1
        ELSE 0
      END
    ) AS "X0_6_Peds_Permission_Revoked_Count__pc",
    SUM(
      CASE
        WHEN (
          "Person_Account_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Person_Account_3"."Consent_Status__c" = 'Yes'
        )
        AND (
          "Person_Account_3"."Consent_Revoked__c" = FALSE
        )
        AND (
          "Person_Account_3"."Survey_Index_Number__c" = '1004'
        )
        THEN 1
        ELSE 0
      END
    ) AS "EHR_Pediatric_Complete__pc"
  FROM (
    SELECT
      "Person_Account_2"."Id" AS "Account.Id",
      "Person_Account_2"."PersonContactId",
      "Person_Account_2"."_source_parent_key_is_unique",
      "Survey_Result__c"."Completion_Status__c",
      "Survey_Result__c"."Survey_Index_Number__c",
      "Survey_Result__c"."Consent_Status__c",
      "Survey_Result__c"."Consent_Revoked__c"
    FROM (
      SELECT
        "Person_Account"."Id",
        "Person_Account"."PersonContactId",
        COUNT("Person_Account"."Id") OVER (
          PARTITION BY "Person_Account"."Id"
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) = 1 AS "_source_parent_key_is_unique"
      FROM "Person_Account" AS "Person_Account"
    ) AS "Person_Account_2"
    LEFT OUTER JOIN "Survey_Result__c" AS "Survey_Result__c"
      ON "Person_Account_2"."PersonContactId" = "Survey_Result__c"."Participant__c"
  ) AS "Person_Account_3"
  GROUP BY
    1,
    2
) AS Comparison_Rows;
