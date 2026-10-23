-- ILLUSTRATIVE bindings/event/times; source profiles are defined in core/schemas/.
-- Direct SELECTs over history. Verify physical catalog types before execution.
-- Execution: 2026-10-21 12:00; BEFORE: 11:59:59; settled AFTER: 12:05.

-- flow
WITH "Survey_Results_At_Execution" AS (
  SELECT
    *
  FROM "example_survey_result"."history" AS "history"
  WHERE
    "history"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
    AND (
      (
        "history"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      )
      OR (
        "history"."valid_to" IS NULL
      )
    )
), "Contact_At_Execution" AS (
  SELECT
    *
  FROM "example_contact"."history" AS "history_2"
  WHERE
    "history_2"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
    AND (
      (
        "history_2"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      )
      OR (
        "history_2"."valid_to" IS NULL
      )
    )
), "Account_Before" AS (
  SELECT
    *
  FROM "example_account"."history" AS "history_3"
  WHERE
    "history_3"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
    AND (
      (
        "history_3"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
      )
      OR (
        "history_3"."valid_to" IS NULL
      )
    )
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
  FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution"
  WHERE
    "Survey_Results_At_Execution"."Id" = 'EXAMPLE_VERIFIED_SURVEY_EVENT'
), "FlowRecordLookup_First_Remote_Physical_Measurement" AS (
  SELECT
    "Survey_Results_At_Execution_2"."Id",
    "Survey_Results_At_Execution_2"."Participant__c",
    "Survey_Results_At_Execution_2"."Completion_Status_Timestamp__c"
  FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution_2"
  WHERE
    "Survey_Results_At_Execution_2"."Survey_Index_Number__c" = '2009'
), "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent" AS (
  SELECT
    "Survey_Results_At_Execution_3"."Id",
    "Survey_Results_At_Execution_3"."Participant__c",
    "Survey_Results_At_Execution_3"."Consent_Status_Timestamp__c"
  FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution_3"
  WHERE
    "Survey_Results_At_Execution_3"."Survey_Index_Number__c" IN ('1003', '1004')
    AND "Survey_Results_At_Execution_3"."Consent_Status__c" = 'Yes'
), "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent" AS (
  SELECT
    "Survey_Results_At_Execution_4"."Id",
    "Survey_Results_At_Execution_4"."Participant__c",
    "Survey_Results_At_Execution_4"."Consent_Status_Timestamp__c"
  FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution_4"
  WHERE
    "Survey_Results_At_Execution_4"."Survey_Index_Number__c" IN ('1001', '1002')
    AND "Survey_Results_At_Execution_4"."Consent_Status__c" = 'Yes'
), "Survey_Result__c" AS (
  SELECT
    *
  FROM "Trigger_Survey_Result" AS "Trigger_Survey_Result"
), "Pediatric_Permission" AS (
  SELECT
    "Survey_Results_At_Execution_6"."Participant__c",
    MIN("Survey_Results_At_Execution_6"."Id") AS "Id",
    COUNT(*) AS "match_count",
    CASE
      WHEN COUNT(*) = 1
      THEN MIN("Survey_Results_At_Execution_6"."California_Signature__c")
      ELSE CAST(NULL AS TIMESTAMP)
    END AS "California_Signature__c"
  FROM (
    SELECT
      *
    FROM "Survey_Results_At_Execution" AS "Survey_Results_At_Execution_5"
    WHERE
      "Survey_Results_At_Execution_5"."Survey_Index_Number__c" = '1007'
      AND "Survey_Results_At_Execution_5"."Consent_Status__c" = 'Yes'
  ) AS "Survey_Results_At_Execution_6"
  GROUP BY
    1
), "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked" AS (
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
    "Survey_Result__c_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
    "Survey_Result__c_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
    ROW_NUMBER() OVER (
      PARTITION BY "Survey_Result__c_3"."Id"
      ORDER BY "Survey_Result__c_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
    ) - 1 AS "_lookup_rank"
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
      "Account"."Social_Determinants_of_Health_Completion__c" AS "Participant__r.Account.Social_Determinants_of_Health_Completion__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c"
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
    LEFT OUTER JOIN "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent" AS "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"
      ON "Survey_Result__c_2"."Participant__c" = "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"."Participant__c"
      AND "Survey_Result__c_2"."Id" <> "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"."Id"
  ) AS "Survey_Result__c_3"
), "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked" AS (
  SELECT
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Id",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Survey_Index_Number__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Completion_Status__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Consent_Status__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Completion_Status_Timestamp__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."California_Signature__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.AccountId",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Birthdate",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Id",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Age_at_Time_of_Consent__pc",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.CABOR_Completion_Date__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.EHR_Consent_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Basics_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Overall_Health_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Lifestyle_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Personal_and_Family_History_Complete__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.HC_Access_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Life_Functioning_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.EH_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Behavioral_Health_Completion__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
    "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
    ROW_NUMBER() OVER (
      PARTITION BY "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."Id"
      ORDER BY "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
    ) - 1 AS "_lookup_rank"
  FROM (
    SELECT
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Id",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Survey_Index_Number__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Completion_Status__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Consent_Status__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Completion_Status_Timestamp__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."California_Signature__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.AccountId",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Birthdate",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Id",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Age_at_Time_of_Consent__pc",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.CABOR_Completion_Date__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.EHR_Consent_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Basics_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Overall_Health_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Lifestyle_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Personal_and_Family_History_Complete__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.HC_Access_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Life_Functioning_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.EH_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Behavioral_Health_Completion__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c"
    FROM (
      SELECT
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Id",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Survey_Index_Number__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Completion_Status__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Consent_Status__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Completion_Status_Timestamp__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."California_Signature__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.AccountId",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Birthdate",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Id",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Age_at_Time_of_Consent__pc",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.CABOR_Completion_Date__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.EHR_Consent_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Basics_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Overall_Health_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Lifestyle_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Personal_and_Family_History_Complete__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.HC_Access_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Life_Functioning_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.EH_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Behavioral_Health_Completion__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c"
      FROM (
        SELECT
          *
        FROM "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked" AS "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked"
        WHERE
          "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked"."_lookup_rank" = 0
      ) AS "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"
    ) AS "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"
    LEFT OUTER JOIN "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent" AS "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent"
      ON "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Participant__c" = "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent"."Participant__c"
      AND "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."Id" <> "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent"."Id"
  ) AS "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"
), "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked" AS (
  SELECT
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Id",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Survey_Index_Number__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Completion_Status__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Consent_Status__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Completion_Status_Timestamp__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."California_Signature__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.AccountId",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Birthdate",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Id",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Age_at_Time_of_Consent__pc",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.CABOR_Completion_Date__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.EHR_Consent_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Basics_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Overall_Health_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Lifestyle_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Personal_and_Family_History_Complete__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.HC_Access_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Life_Functioning_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.EH_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Behavioral_Health_Completion__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
    "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
    ROW_NUMBER() OVER (
      PARTITION BY "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."Id"
      ORDER BY "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c" ASC NULLS FIRST
    ) - 1 AS "_lookup_rank"
  FROM (
    SELECT
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Id",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Survey_Index_Number__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Completion_Status__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Consent_Status__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Completion_Status_Timestamp__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."California_Signature__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.AccountId",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Birthdate",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Id",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Age_at_Time_of_Consent__pc",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.CABOR_Completion_Date__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.EHR_Consent_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Basics_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Overall_Health_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Lifestyle_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Personal_and_Family_History_Complete__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.HC_Access_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Life_Functioning_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.EH_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Behavioral_Health_Completion__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement"."Id" AS "FlowRecordLookup.First_Remote_Physical_Measurement.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement"."Completion_Status_Timestamp__c" AS "FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
    FROM (
      SELECT
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Id",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Survey_Index_Number__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Completion_Status__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Consent_Status__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Completion_Status_Timestamp__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."California_Signature__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.AccountId",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Birthdate",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Id",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Age_at_Time_of_Consent__pc",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.CABOR_Completion_Date__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.EHR_Consent_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Basics_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Overall_Health_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Lifestyle_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Personal_and_Family_History_Complete__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.HC_Access_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Life_Functioning_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.EH_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Behavioral_Health_Completion__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c"
      FROM (
        SELECT
          *
        FROM "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked" AS "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked"
        WHERE
          "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked"."_lookup_rank" = 0
      ) AS "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"
    ) AS "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"
    LEFT OUTER JOIN "FlowRecordLookup_First_Remote_Physical_Measurement" AS "FlowRecordLookup_First_Remote_Physical_Measurement"
      ON "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."Participant__c" = "FlowRecordLookup_First_Remote_Physical_Measurement"."Participant__c"
  ) AS "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"
), "Flow_Context" AS (
  SELECT
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Id",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Survey_Index_Number__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Completion_Status__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Consent_Status__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Completion_Status_Timestamp__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."California_Signature__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.AccountId",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Birthdate",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Id",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Age_at_Time_of_Consent__pc",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.CABOR_Completion_Date__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.EHR_Consent_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Basics_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Overall_Health_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Lifestyle_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Personal_and_Family_History_Complete__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.HC_Access_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Life_Functioning_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.EH_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Behavioral_Health_Completion__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
    "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
    CAST(FLOOR(
      DATE_DIFF(
        'DAY',
        DATE_TRUNC(
          'DAY',
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Birthdate"
        ),
        DATE_TRUNC('DAY', FROM_ISO8601_DATE('2026-10-21'))
      ) / CAST(365.25 AS DOUBLE)
    ) AS BIGINT) AS "FlowFormula_Age_At_Execution"
  FROM (
    SELECT
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Survey_Index_Number__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Completion_Status__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Consent_Status__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Completion_Status_Timestamp__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."California_Signature__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.AccountId",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Birthdate",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Age_at_Time_of_Consent__pc",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.CABOR_Completion_Date__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.EHR_Consent_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Basics_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Overall_Health_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Lifestyle_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Personal_and_Family_History_Complete__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.HC_Access_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Life_Functioning_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.EH_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Behavioral_Health_Completion__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
      "Pediatric_Permission"."Id" AS "FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
      COALESCE("Pediatric_Permission"."match_count", 0) AS "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
      "Pediatric_Permission"."California_Signature__c" AS "FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
    FROM (
      SELECT
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Id",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Survey_Index_Number__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Completion_Status__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Consent_Status__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Completion_Status_Timestamp__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."California_Signature__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.AccountId",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Birthdate",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Id",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Age_at_Time_of_Consent__pc",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.CABOR_Completion_Date__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.EHR_Consent_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Basics_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Overall_Health_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Lifestyle_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Personal_and_Family_History_Complete__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.HC_Access_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Life_Functioning_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.EH_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Behavioral_Health_Completion__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
      FROM (
        SELECT
          *
        FROM "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked" AS "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked"
        WHERE
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked"."_lookup_rank" = 0
      ) AS "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"
    ) AS "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"
    LEFT OUTER JOIN "Pediatric_Permission" AS "Pediatric_Permission"
      ON "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Participant__c" = "Pediatric_Permission"."Participant__c"
      AND "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Completion_Status__c" = 'Complete'
      AND "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Survey_Index_Number__c" = '1008'
      AND "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."Consent_Status__c" IN ('Yes', 'N/A')
  ) AS "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"
)
SELECT
  "Flow_Context"."Id" AS "Record.Id", /* Source identity: Record.Id; source: Survey_Result__c.Id */
  "Flow_Context"."Participant__r.Account.Id" AS "Account.Id", /* Source identity: Account.Id; source: Account.Id */
  "Flow_Context"."Participant__c", /* Source identity: Participant__c; source: Survey_Result__c.Participant__c */
  "Flow_Context"."Survey_Index_Number__c", /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */
  "Flow_Context"."Completion_Status_Timestamp__c", /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
  "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count", /* Number of candidate pediatric permissions; source: FlowRecordLookup.Get_Permission_1007 */
  CASE
    WHEN (
      (
        "Flow_Context"."Completion_Status__c" = 'Complete'
      )
      AND "Flow_Context"."Survey_Index_Number__c" IN ('1001', '1002')
      AND (
        "Flow_Context"."Consent_Status__c" = 'Yes'
      )
    )
    OR (
      (
        "Flow_Context"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '1008'
      )
      AND "Flow_Context"."Consent_Status__c" IN ('Yes', 'N/A')
    )
    THEN "Flow_Context"."FlowFormula_Age_At_Execution"
    ELSE "Flow_Context"."Participant__r.Account.Age_at_Time_of_Consent__pc"
  END AS "Age_at_Time_of_Consent__pc", /* Age at flow execution; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowFormula.formAgeCalculation */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND "Flow_Context"."Survey_Index_Number__c" IN ('1001', '1002')
    AND (
      "Flow_Context"."Consent_Status__c" = 'Yes'
    )
    THEN "Flow_Context"."California_Signature__c"
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '1008'
    )
    AND "Flow_Context"."Consent_Status__c" IN ('Yes', 'N/A')
    THEN "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
    ELSE "Flow_Context"."Participant__r.Account.CABOR_Completion_Date__c"
  END AS "CABOR_Completion_Date__c", /* California signature timestamp; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowRecordLookup.Get_Permission_1007 */
  CASE
    WHEN (
      (
        "Flow_Context"."Completion_Status__c" = 'Complete'
      )
      AND "Flow_Context"."Survey_Index_Number__c" IN ('1001', '1002')
      AND (
        "Flow_Context"."Consent_Status__c" = 'Yes'
      )
      AND (
        "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NOT NULL
      )
    )
    OR (
      (
        "Flow_Context"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '1008'
      )
      AND "Flow_Context"."Consent_Status__c" IN ('Yes', 'N/A')
      AND NOT (
        (
          "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NULL
        )
        AND (
          "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NULL
        )
      )
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c"
  END AS "Earliest_Primary_Consent_Date_for_Report__c", /* Earliest primary consent report timestamp; source: FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Negative */
  CASE
    WHEN (
      (
        "Flow_Context"."Completion_Status__c" = 'Complete'
      )
      AND "Flow_Context"."Survey_Index_Number__c" IN ('1001', '1002')
      AND (
        "Flow_Context"."Consent_Status__c" = 'Yes'
      )
    )
    OR (
      (
        "Flow_Context"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '1008'
      )
      AND "Flow_Context"."Consent_Status__c" IN ('Yes', 'N/A')
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c"
  END AS "Latest_Primary_Consent_Date_for_Report__c", /* Latest primary consent report timestamp; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND "Flow_Context"."Survey_Index_Number__c" IN ('1003', '1004')
    AND (
      "Flow_Context"."Consent_Status__c" = 'Yes'
    )
    AND (
      "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NOT NULL
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.EHR_Consent_Date_Time__c"
  END AS "EHR_Consent_Date_Time__c", /* Ehr consent timestamp; source: FlowRecordUpdate.updateAccount1003_NegativeSF */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND "Flow_Context"."Survey_Index_Number__c" IN ('1003', '1004')
    AND (
      "Flow_Context"."Consent_Status__c" = 'Yes'
    )
    AND (
      "Flow_Context"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NULL
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.EHR_Reconsent_Date_Time__c"
  END AS "EHR_Reconsent_Date_Time__c", /* Ehr reconsent timestamp; source: FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '1005'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Update_to_Primary_Consent_Completed__c"
  END AS "Update_to_Primary_Consent_Completed__c", /* Primary consent update timestamp; source: FlowRecordUpdate.updateAccount1005 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND "Flow_Context"."Survey_Index_Number__c" IN ('2001', '2002')
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Basics_Date_Time__c"
  END AS "Basics_Date_Time__c", /* Basics completion timestamp; source: FlowRecordUpdate.updateAccount2001 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND "Flow_Context"."Survey_Index_Number__c" IN ('2003', '2004')
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Overall_Health_Date_Time__c"
  END AS "Overall_Health_Date_Time__c", /* Overall health completion timestamp; source: FlowRecordUpdate.updateAccount2003 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2005'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Lifestyle_Date_Time__c"
  END AS "Lifestyle_Date_Time__c", /* Lifestyle completion timestamp; source: FlowRecordUpdate.updateAccount2005 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2006'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Personal_and_Family_History_Complete__c"
  END AS "Personal_and_Family_History_Complete__c", /* Personal and family history completion timestamp; source: FlowRecordUpdate.updateAccount2006 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2007'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.HC_Access_Date_Time__c"
  END AS "HC_Access_Date_Time__c", /* Healthcare access completion timestamp; source: FlowRecordUpdate.updateAccount2007 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2008'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Life_Functioning_Date_Time__c"
  END AS "Life_Functioning_Date_Time__c", /* Life functioning completion timestamp; source: FlowRecordUpdate.updateAccount2008 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2009'
    )
    THEN "Flow_Context"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
    ELSE "Flow_Context"."Participant__r.Account.First_Physical_Measurement_Date_Time__c"
  END AS "First_Physical_Measurement_Date_Time__c", /* First remote physical measurement timestamp; source: FlowRecordUpdate.updateAccount2009, FlowRecordLookup.getFirstPhysicalMeasurement */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2009'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c"
  END AS "Last_Physical_Measurement_Date_Time__c", /* Latest processed remote physical measurement timestamp; source: FlowRecordUpdate.updateAccount2009 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2010'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.EH_Date_Time__c"
  END AS "EH_Date_Time__c", /* Emotional health completion timestamp; source: FlowRecordUpdate.updateAccount2010 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2011'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Behavioral_Health_Completion__c"
  END AS "Behavioral_Health_Completion__c", /* Behavioral health completion timestamp; source: FlowRecordUpdate.updateAccount2011 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2012'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Environmental_Exposures_Date_Time__c"
  END AS "Environmental_Exposures_Date_Time__c", /* Environmental exposures completion timestamp; source: FlowRecordUpdate.updateAccount2012 */
  CASE
    WHEN (
      "Flow_Context"."Completion_Status__c" = 'Complete'
    )
    AND (
      "Flow_Context"."Survey_Index_Number__c" /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */ = '2013'
    )
    THEN "Flow_Context"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "Flow_Context"."Participant__r.Account.Social_Determinants_of_Health_Completion__c"
  END AS "Social_Determinants_of_Health_Completion__c", /* Social determinants completion timestamp; source: FlowRecordUpdate.updateAccount2013 */
  NOT (
    COALESCE(
      (
        "Flow_Context"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Flow_Context"."Survey_Index_Number__c" = '1008'
      )
      AND "Flow_Context"."Consent_Status__c" IN ('Yes', 'N/A'),
      FALSE
    )
  )
  OR (
    "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count" /* Number of candidate pediatric permissions; source: FlowRecordLookup.Get_Permission_1007 */ <= 1
  ) AS "CABOR_Completion_Date__c_is_deterministic" /* Signature lookup has at most one candidate on the assent route; source: FlowRecordLookup.Get_Permission_1007 */
FROM "Flow_Context" AS "Flow_Context";

-- rollups
WITH "Account_At_Snapshot" AS (
  SELECT
    *
  FROM "example_account"."history" AS "history"
  WHERE
    "history"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
    AND (
      (
        "history"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      )
      OR (
        "history"."valid_to" IS NULL
      )
    )
), "Survey_Results_At_Execution" AS (
  SELECT
    *
  FROM "example_survey_result"."history" AS "history_2"
  WHERE
    "history_2"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
    AND (
      (
        "history_2"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      )
      OR (
        "history_2"."valid_to" IS NULL
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
  "Person_Account_2"."Account.Id", /* Source identity: Account.Id; source: Account.Id */
  "Person_Account_2"."PersonContactId", /* Source identity: PersonContactId; source: Account.PersonContactId */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1003'
      )
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Authorized__pc", /* Ehr authorized; source: Account.EHR_Authorized__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1003'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Count_of_Completed_EHR_Auth__pc", /* Count of completed ehr auth; source: Account.Count_of_Completed_EHR_Auth__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1001'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Count_of_Completed_Primary_Consent__pc", /* Count of completed primary consent; source: Account.Count_of_Completed_Primary_Consent__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1005'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Count_of_Completed_Reconsent__pc", /* Count of completed reconsent; source: Account.Count_of_Completed_Reconsent__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '2005'
      )
      THEN 1
      ELSE 0
    END
  ) AS "PPI_2_Completion_Count__pc", /* Ppi 2 completion count; source: Account.PPI_2_Completion_Count__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '2003'
      )
      THEN 1
      ELSE 0
    END
  ) AS "PPI_3_Completion_Count__pc", /* Ppi 3 completion count; source: Account.PPI_3_Completion_Count__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'Yes'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND "Person_Account_2"."Survey_Index_Number__c" IN ('1003', '1004')
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Consent_Active__pc", /* Ehr consent active; source: Account.EHR_Consent_Active__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'No'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND "Person_Account_2"."Survey_Index_Number__c" IN ('1003', '1004')
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Consent_Declined__pc", /* Ehr consent declined; source: Account.EHR_Consent_Declined__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND "Person_Account_2"."Survey_Index_Number__c" IN ('2001', '2002')
      THEN 1
      ELSE 0
    END
  ) AS "PP1_Basics_Survey_Complete__pc", /* Pp1 basics survey complete; source: Account.PP1_Basics_Survey_Complete__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'No'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1005'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Re_Consent_Declined__pc", /* Re consent declined; source: Account.Re_Consent_Declined__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'Yes'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1005'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Re_consent_Active__pc", /* Re consent active; source: Account.Re_consent_Active__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'No'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND "Person_Account_2"."Survey_Index_Number__c" IN ('1005', '1002')
      THEN 1
      ELSE 0
    END
  ) AS "Primary_Consent_Declined__pc", /* Primary consent declined; source: Account.Primary_Consent_Declined__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'Yes'
      )
      AND "Person_Account_2"."Survey_Index_Number__c" IN ('1003', '1004')
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Consent_Ever__pc", /* Ehr consent ever; source: Account.EHR_Consent_Ever__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'Yes'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1008'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Assent_Completion_Count__pc", /* Assent completion count; source: Account.Assent_Completion_Count__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'Yes'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1007'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Pediatric_Permission_Completion_Count__pc", /* Pediatric permission completion count; source: Account.Pediatric_Permission_Completion_Count__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Consent_Status__c" = 'Yes'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1002'
      )
      THEN 1
      ELSE 0
    END
  ) AS "X0_6_Peds_Permission_Count__pc", /* X0 6 peds permission count; source: Account.X0_6_Peds_Permission_Count__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Consent_Status__c" = 'No'
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1002'
      )
      THEN 1
      ELSE 0
    END
  ) AS "X0_6_Peds_Permission_Declined_Count__pc", /* X0 6 peds permission declined count; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Consent_Revoked__c" = TRUE
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1002'
      )
      THEN 1
      ELSE 0
    END
  ) AS "X0_6_Peds_Permission_Revoked_Count__pc", /* X0 6 peds permission revoked count; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
  SUM(
    CASE
      WHEN (
        "Person_Account_2"."Completion_Status__c" = 'Complete'
      )
      AND (
        "Person_Account_2"."Consent_Status__c" = 'Yes'
      )
      AND (
        "Person_Account_2"."Consent_Revoked__c" = FALSE
      )
      AND (
        "Person_Account_2"."Survey_Index_Number__c" = '1004'
      )
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Pediatric_Complete__pc" /* Ehr pediatric complete; source: Account.EHR_Pediatric_Complete__pc */
FROM (
  SELECT
    "Person_Account"."Id" AS "Account.Id",
    "Person_Account"."PersonContactId",
    "Survey_Result__c"."Completion_Status__c",
    "Survey_Result__c"."Survey_Index_Number__c",
    "Survey_Result__c"."Consent_Status__c",
    "Survey_Result__c"."Consent_Revoked__c"
  FROM "Person_Account" AS "Person_Account"
  LEFT OUTER JOIN "Survey_Result__c" AS "Survey_Result__c"
    ON "Person_Account"."PersonContactId" = "Survey_Result__c"."Participant__c"
) AS "Person_Account_2"
GROUP BY
  1,
  2;
