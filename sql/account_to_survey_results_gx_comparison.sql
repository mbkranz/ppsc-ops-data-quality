-- ILLUSTRATIVE bindings/event/times; source profiles are defined in core/schemas/.
-- Direct SELECTs over history. Verify physical catalog types before execution.
-- Execution: 2026-10-21 12:00; BEFORE: 11:59:59; settled AFTER: 12:05.

-- flow
SELECT
  *
FROM (
  WITH "Account_After" AS (
    SELECT
      "history"."Id",
      "history"."PersonContactId",
      "history"."IsPersonAccount",
      "history"."Age_at_Time_of_Consent__pc",
      "history"."CABOR_Completion_Date__c",
      "history"."Earliest_Primary_Consent_Date_for_Report__c",
      "history"."Latest_Primary_Consent_Date_for_Report__c",
      "history"."EHR_Consent_Date_Time__c",
      "history"."EHR_Reconsent_Date_Time__c",
      "history"."Update_to_Primary_Consent_Completed__c",
      "history"."Basics_Date_Time__c",
      "history"."Overall_Health_Date_Time__c",
      "history"."Lifestyle_Date_Time__c",
      "history"."Personal_and_Family_History_Complete__c",
      "history"."HC_Access_Date_Time__c",
      "history"."Life_Functioning_Date_Time__c",
      "history"."First_Physical_Measurement_Date_Time__c",
      "history"."Last_Physical_Measurement_Date_Time__c",
      "history"."EH_Date_Time__c",
      "history"."Behavioral_Health_Completion__c",
      "history"."Environmental_Exposures_Date_Time__c",
      "history"."Social_Determinants_of_Health_Completion__c",
      "history"."EHR_Authorized__pc",
      "history"."Count_of_Completed_EHR_Auth__pc",
      "history"."Count_of_Completed_Primary_Consent__pc",
      "history"."Count_of_Completed_Reconsent__pc",
      "history"."PPI_2_Completion_Count__pc",
      "history"."PPI_3_Completion_Count__pc",
      "history"."EHR_Consent_Active__pc",
      "history"."EHR_Consent_Declined__pc",
      "history"."PP1_Basics_Survey_Complete__pc",
      "history"."Re_Consent_Declined__pc",
      "history"."Re_consent_Active__pc",
      "history"."Primary_Consent_Declined__pc",
      "history"."EHR_Consent_Ever__pc",
      "history"."Assent_Completion_Count__pc",
      "history"."Pediatric_Permission_Completion_Count__pc",
      "history"."X0_6_Peds_Permission_Count__pc",
      "history"."X0_6_Peds_Permission_Declined_Count__pc",
      "history"."X0_6_Peds_Permission_Revoked_Count__pc",
      "history"."EHR_Pediatric_Complete__pc",
      "history"."valid_from",
      "history"."valid_to",
      "history"."is_current",
      "history"."loaded_at",
      'EXAMPLE_VERIFIED_SURVEY_EVENT' AS "survey_result_id"
    FROM "example_account"."history" AS "history"
    WHERE
      "history"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:05:00') AS TIMESTAMP)
      AND (
        (
          "history"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:05:00') AS TIMESTAMP)
        )
        OR (
          "history"."valid_to" IS NULL
        )
      )
  ), "Account_Before" AS (
    SELECT
      *
    FROM "example_account"."history" AS "history_2"
    WHERE
      "history_2"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
      AND (
        (
          "history_2"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
        )
        OR (
          "history_2"."valid_to" IS NULL
        )
      )
  ), "Survey_Results_At_Execution" AS (
    SELECT
      *
    FROM "example_survey_result"."history" AS "history_3"
    WHERE
      "history_3"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      AND (
        (
          "history_3"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
        )
        OR (
          "history_3"."valid_to" IS NULL
        )
      )
  ), "Contact_At_Execution" AS (
    SELECT
      *
    FROM "example_contact"."history" AS "history_4"
    WHERE
      "history_4"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      AND (
        (
          "history_4"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
        )
        OR (
          "history_4"."valid_to" IS NULL
        )
      )
  ), "Account" AS (
    SELECT
      *
    FROM "Account_Before" AS "Account_Before"
  ), "Contact" AS (
    SELECT
      *
    FROM "Contact_At_Execution" AS "Contact_At_Execution"
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
  ), "Survey_Completion_Route" AS (
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
      CASE
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" IN ('1001', '1002')
          AND (
            "Survey_Result__c_3"."Consent_Status__c" = 'Yes'
          )
        )
        THEN 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" IN ('1003', '1004')
          AND (
            "Survey_Result__c_3"."Consent_Status__c" = 'Yes'
          )
        )
        THEN 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '1005'
        )
        THEN 'FlowRecordUpdate.Primary_Consent_Update_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          (
            "Survey_Result__c_3"."Survey_Index_Number__c" = '1008'
          )
          AND "Survey_Result__c_3"."Consent_Status__c" IN ('Yes', 'N/A')
        )
        THEN 'FlowRecordLookup.Pediatric_Permission_For_Assent'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND "Survey_Result__c_3"."Survey_Index_Number__c" IN ('2001', '2002')
        THEN 'FlowRecordUpdate.Basics_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND "Survey_Result__c_3"."Survey_Index_Number__c" IN ('2003', '2004')
        THEN 'FlowRecordUpdate.Overall_Health_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2005'
        )
        THEN 'FlowRecordUpdate.Lifestyle_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2006'
        )
        THEN 'FlowRecordUpdate.Personal_And_Family_History_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2007'
        )
        THEN 'FlowRecordUpdate.Healthcare_Access_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2008'
        )
        THEN 'FlowRecordUpdate.Life_Functioning_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2009'
        )
        THEN 'FlowRecordLookup.First_Remote_Physical_Measurement'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2010'
        )
        THEN 'FlowRecordUpdate.Emotional_Health_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2011'
        )
        THEN 'FlowRecordUpdate.Behavioral_Health_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2012'
        )
        THEN 'FlowRecordUpdate.Environmental_Exposures_Completion'
        WHEN (
          "Survey_Result__c_3"."Completion_Status__c" = 'Complete'
        )
        AND (
          "Survey_Result__c_3"."Survey_Index_Number__c" = '2013'
        )
        THEN 'FlowRecordUpdate.Social_Determinants_Completion'
        ELSE CAST(NULL AS VARCHAR)
      END AS "FlowDecision_Survey_Completion_Route_target"
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
  ), "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked" AS (
    SELECT
      "Survey_Completion_Route_2"."Id",
      "Survey_Completion_Route_2"."Participant__c",
      "Survey_Completion_Route_2"."Survey_Index_Number__c",
      "Survey_Completion_Route_2"."Completion_Status__c",
      "Survey_Completion_Route_2"."Consent_Status__c",
      "Survey_Completion_Route_2"."Completion_Status_Timestamp__c",
      "Survey_Completion_Route_2"."California_Signature__c",
      "Survey_Completion_Route_2"."Participant__r.AccountId",
      "Survey_Completion_Route_2"."Participant__r.Birthdate",
      "Survey_Completion_Route_2"."Participant__r.Account.Id",
      "Survey_Completion_Route_2"."Participant__r.Account.Age_at_Time_of_Consent__pc",
      "Survey_Completion_Route_2"."Participant__r.Account.CABOR_Completion_Date__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
      "Survey_Completion_Route_2"."Participant__r.Account.EHR_Consent_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Basics_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Overall_Health_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Lifestyle_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Personal_and_Family_History_Complete__c",
      "Survey_Completion_Route_2"."Participant__r.Account.HC_Access_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Life_Functioning_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.EH_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Behavioral_Health_Completion__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
      "Survey_Completion_Route_2"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
      "Survey_Completion_Route_2"."FlowDecision_Survey_Completion_Route_target",
      "Survey_Completion_Route_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
      "Survey_Completion_Route_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
      ROW_NUMBER() OVER (
        PARTITION BY "Survey_Completion_Route_2"."Id"
        ORDER BY "Survey_Completion_Route_2"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
      ) - 1 AS "_lookup_rank"
    FROM (
      SELECT
        "Survey_Completion_Route"."Id",
        "Survey_Completion_Route"."Participant__c",
        "Survey_Completion_Route"."Survey_Index_Number__c",
        "Survey_Completion_Route"."Completion_Status__c",
        "Survey_Completion_Route"."Consent_Status__c",
        "Survey_Completion_Route"."Completion_Status_Timestamp__c",
        "Survey_Completion_Route"."California_Signature__c",
        "Survey_Completion_Route"."Participant__r.AccountId",
        "Survey_Completion_Route"."Participant__r.Birthdate",
        "Survey_Completion_Route"."Participant__r.Account.Id",
        "Survey_Completion_Route"."Participant__r.Account.Age_at_Time_of_Consent__pc",
        "Survey_Completion_Route"."Participant__r.Account.CABOR_Completion_Date__c",
        "Survey_Completion_Route"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
        "Survey_Completion_Route"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
        "Survey_Completion_Route"."Participant__r.Account.EHR_Consent_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
        "Survey_Completion_Route"."Participant__r.Account.Basics_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.Overall_Health_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.Lifestyle_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.Personal_and_Family_History_Complete__c",
        "Survey_Completion_Route"."Participant__r.Account.HC_Access_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.Life_Functioning_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.EH_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.Behavioral_Health_Completion__c",
        "Survey_Completion_Route"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
        "Survey_Completion_Route"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
        "Survey_Completion_Route"."FlowDecision_Survey_Completion_Route_target",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c"
      FROM "Survey_Completion_Route" AS "Survey_Completion_Route"
      LEFT OUTER JOIN "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent" AS "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"
        ON "Survey_Completion_Route"."Participant__c" = "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"."Participant__c"
        AND "Survey_Completion_Route"."Id" <> "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent"."Id"
    ) AS "Survey_Completion_Route_2"
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
      "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_4"."FlowDecision_Survey_Completion_Route_target",
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
        "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_3"."FlowDecision_Survey_Completion_Route_target",
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
          "FlowRecordLookup_Earliest_Other_Yes_Primary_Consent_Ranked_2"."FlowDecision_Survey_Completion_Route_target",
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
      "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_4"."FlowDecision_Survey_Completion_Route_target",
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
        "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_3"."FlowDecision_Survey_Completion_Route_target",
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
          "FlowRecordLookup_Earliest_Other_Yes_EHR_Consent_Ranked_2"."FlowDecision_Survey_Completion_Route_target",
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
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowDecision_Survey_Completion_Route_target",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
      "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
      CASE
        WHEN (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
        )
        AND (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NULL
        )
        THEN 'FlowRecordUpdate.Primary_Consent_Without_Prior_Yes'
        WHEN (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
        )
        AND NOT (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NULL
        )
        THEN 'FlowRecordUpdate.Primary_Consent_With_Prior_Yes'
        ELSE CAST(NULL AS VARCHAR)
      END AS "FlowDecision_Primary_Consent_Account_Update_target",
      CASE
        WHEN (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
        )
        AND (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NULL
        )
        THEN 'FlowRecordUpdate.EHR_Consent_Without_Prior_Yes'
        WHEN (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
        )
        AND NOT (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NULL
        )
        THEN 'FlowRecordUpdate.EHR_Consent_With_Prior_Yes'
        ELSE CAST(NULL AS VARCHAR)
      END AS "FlowDecision_EHR_Consent_Account_Update_target",
      CASE
        WHEN (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
        )
        AND (
          (
            "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NULL
          )
          AND (
            "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NULL
          )
        )
        THEN 'FlowRecordUpdate.Assent_No_Permission_And_No_Primary_Date'
        WHEN (
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
        )
        AND NOT (
          (
            "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NULL
          )
          AND (
            "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NULL
          )
        )
        THEN 'FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date'
        ELSE CAST(NULL AS VARCHAR)
      END AS "FlowDecision_Assent_Account_Update_target",
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
        "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."FlowDecision_Survey_Completion_Route_target",
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
          "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_2"."FlowDecision_Survey_Completion_Route_target",
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
        AND "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_3"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
    ) AS "FlowRecordLookup_First_Remote_Physical_Measurement_Ranked_4"
  ), "Expected_Account" AS (
    SELECT
      "Flow_Context"."Id" AS "Record.Id",
      "Flow_Context"."Participant__r.Account.Id" AS "Account.Id",
      "Flow_Context"."Participant__c",
      "Flow_Context"."Survey_Index_Number__c",
      "Flow_Context"."Completion_Status_Timestamp__c",
      "Flow_Context"."FlowDecision_Survey_Completion_Route_target",
      "Flow_Context"."FlowDecision_Primary_Consent_Account_Update_target",
      "Flow_Context"."FlowDecision_EHR_Consent_Account_Update_target",
      "Flow_Context"."FlowDecision_Assent_Account_Update_target",
      "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" IN (
          'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent',
          'FlowRecordLookup.Pediatric_Permission_For_Assent'
        )
        THEN "Flow_Context"."FlowFormula_Age_At_Execution"
        ELSE "Flow_Context"."Participant__r.Account.Age_at_Time_of_Consent__pc"
      END AS "Age_at_Time_of_Consent__pc",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
        THEN "Flow_Context"."California_Signature__c"
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
        THEN "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
        ELSE "Flow_Context"."Participant__r.Account.CABOR_Completion_Date__c"
      END AS "CABOR_Completion_Date__c",
      CASE
        WHEN (
          "Flow_Context"."FlowDecision_Primary_Consent_Account_Update_target" = 'FlowRecordUpdate.Primary_Consent_With_Prior_Yes'
        )
        OR (
          "Flow_Context"."FlowDecision_Assent_Account_Update_target" = 'FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date'
        )
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c"
      END AS "Earliest_Primary_Consent_Date_for_Report__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" IN (
          'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent',
          'FlowRecordLookup.Pediatric_Permission_For_Assent'
        )
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c"
      END AS "Latest_Primary_Consent_Date_for_Report__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_EHR_Consent_Account_Update_target" = 'FlowRecordUpdate.EHR_Consent_With_Prior_Yes'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.EHR_Consent_Date_Time__c"
      END AS "EHR_Consent_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_EHR_Consent_Account_Update_target" = 'FlowRecordUpdate.EHR_Consent_Without_Prior_Yes'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.EHR_Reconsent_Date_Time__c"
      END AS "EHR_Reconsent_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Primary_Consent_Update_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Update_to_Primary_Consent_Completed__c"
      END AS "Update_to_Primary_Consent_Completed__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Basics_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Basics_Date_Time__c"
      END AS "Basics_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Overall_Health_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Overall_Health_Date_Time__c"
      END AS "Overall_Health_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Lifestyle_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Lifestyle_Date_Time__c"
      END AS "Lifestyle_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Personal_And_Family_History_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Personal_and_Family_History_Complete__c"
      END AS "Personal_and_Family_History_Complete__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Healthcare_Access_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.HC_Access_Date_Time__c"
      END AS "HC_Access_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Life_Functioning_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Life_Functioning_Date_Time__c"
      END AS "Life_Functioning_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.First_Remote_Physical_Measurement'
        THEN "Flow_Context"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.First_Physical_Measurement_Date_Time__c"
      END AS "First_Physical_Measurement_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.First_Remote_Physical_Measurement'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c"
      END AS "Last_Physical_Measurement_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Emotional_Health_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.EH_Date_Time__c"
      END AS "EH_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Behavioral_Health_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Behavioral_Health_Completion__c"
      END AS "Behavioral_Health_Completion__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Environmental_Exposures_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Environmental_Exposures_Date_Time__c"
      END AS "Environmental_Exposures_Date_Time__c",
      CASE
        WHEN "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Social_Determinants_Completion'
        THEN "Flow_Context"."Completion_Status_Timestamp__c"
        ELSE "Flow_Context"."Participant__r.Account.Social_Determinants_of_Health_Completion__c"
      END AS "Social_Determinants_of_Health_Completion__c",
      NOT (
        COALESCE(
          "Flow_Context"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent',
          FALSE
        )
      )
      OR (
        "Flow_Context"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count" <= 1
      ) AS "CABOR_Completion_Date__c_is_deterministic"
    FROM "Flow_Context" AS "Flow_Context"
  )
  SELECT
    "Expected_Account"."Record.Id" AS "survey_result_id", /* Source identity: Record.Id; source: Survey_Result__c.Id */
    "Expected_Account"."Participant__c" AS "participant_contact_id", /* Source identity: Participant__c; source: Survey_Result__c.Participant__c */
    "Expected_Account"."Account.Id" AS "expected_account_id", /* Source identity: Account.Id; source: Account.Id */
    "Account_After"."Id" AS "observed_account_id", /* Source identity: Account.Id; source: Account.Id */
    "Expected_Account"."Survey_Index_Number__c" AS "survey_index_number", /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */
    "Expected_Account"."Completion_Status_Timestamp__c" AS "survey_completion_timestamp", /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    DATE("Expected_Account"."Completion_Status_Timestamp__c") >= FROM_ISO8601_DATE('2024-12-16') AS "survey_completion_occurred_on_or_after_launch", /* Survey completion calendar date is on or after launch (2024-12-16); source: Survey_Result__c.Completion_Status_Timestamp__c */
    "Expected_Account"."CABOR_Completion_Date__c_is_deterministic" AS "cabor_lookup_is_deterministic", /* Signature lookup has at most one candidate on the assent route; source: FlowRecordLookup.Get_Permission_1007 */
    "Expected_Account"."Age_at_Time_of_Consent__pc" AS "expected__Age_at_Time_of_Consent__pc", /* Expected Account.Age_at_Time_of_Consent__pc: Age at flow execution; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowFormula.formAgeCalculation */
    "Expected_Account"."CABOR_Completion_Date__c" AS "expected__CABOR_Completion_Date__c", /* Expected Account.CABOR_Completion_Date__c: California signature timestamp; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowRecordLookup.Get_Permission_1007 */
    "Expected_Account"."Earliest_Primary_Consent_Date_for_Report__c" AS "expected__Earliest_Primary_Consent_Date_for_Report__c", /* Expected Account.Earliest_Primary_Consent_Date_for_Report__c: Earliest primary consent report timestamp; source: FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Negative */
    "Expected_Account"."Latest_Primary_Consent_Date_for_Report__c" AS "expected__Latest_Primary_Consent_Date_for_Report__c", /* Expected Account.Latest_Primary_Consent_Date_for_Report__c: Latest primary consent report timestamp; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative */
    "Expected_Account"."EHR_Consent_Date_Time__c" AS "expected__EHR_Consent_Date_Time__c", /* Expected Account.EHR_Consent_Date_Time__c: Ehr consent timestamp; source: FlowRecordUpdate.updateAccount1003_NegativeSF */
    "Expected_Account"."EHR_Reconsent_Date_Time__c" AS "expected__EHR_Reconsent_Date_Time__c", /* Expected Account.EHR_Reconsent_Date_Time__c: Ehr reconsent timestamp; source: FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF */
    "Expected_Account"."Update_to_Primary_Consent_Completed__c" AS "expected__Update_to_Primary_Consent_Completed__c", /* Expected Account.Update_to_Primary_Consent_Completed__c: Primary consent update timestamp; source: FlowRecordUpdate.updateAccount1005 */
    "Expected_Account"."Basics_Date_Time__c" AS "expected__Basics_Date_Time__c", /* Expected Account.Basics_Date_Time__c: Basics completion timestamp; source: FlowRecordUpdate.updateAccount2001 */
    "Expected_Account"."Overall_Health_Date_Time__c" AS "expected__Overall_Health_Date_Time__c", /* Expected Account.Overall_Health_Date_Time__c: Overall health completion timestamp; source: FlowRecordUpdate.updateAccount2003 */
    "Expected_Account"."Lifestyle_Date_Time__c" AS "expected__Lifestyle_Date_Time__c", /* Expected Account.Lifestyle_Date_Time__c: Lifestyle completion timestamp; source: FlowRecordUpdate.updateAccount2005 */
    "Expected_Account"."Personal_and_Family_History_Complete__c" AS "expected__Personal_and_Family_History_Complete__c", /* Expected Account.Personal_and_Family_History_Complete__c: Personal and family history completion timestamp; source: FlowRecordUpdate.updateAccount2006 */
    "Expected_Account"."HC_Access_Date_Time__c" AS "expected__HC_Access_Date_Time__c", /* Expected Account.HC_Access_Date_Time__c: Healthcare access completion timestamp; source: FlowRecordUpdate.updateAccount2007 */
    "Expected_Account"."Life_Functioning_Date_Time__c" AS "expected__Life_Functioning_Date_Time__c", /* Expected Account.Life_Functioning_Date_Time__c: Life functioning completion timestamp; source: FlowRecordUpdate.updateAccount2008 */
    "Expected_Account"."First_Physical_Measurement_Date_Time__c" AS "expected__First_Physical_Measurement_Date_Time__c", /* Expected Account.First_Physical_Measurement_Date_Time__c: First remote physical measurement timestamp; source: FlowRecordUpdate.updateAccount2009, FlowRecordLookup.getFirstPhysicalMeasurement */
    "Expected_Account"."Last_Physical_Measurement_Date_Time__c" AS "expected__Last_Physical_Measurement_Date_Time__c", /* Expected Account.Last_Physical_Measurement_Date_Time__c: Latest processed remote physical measurement timestamp; source: FlowRecordUpdate.updateAccount2009 */
    "Expected_Account"."EH_Date_Time__c" AS "expected__EH_Date_Time__c", /* Expected Account.EH_Date_Time__c: Emotional health completion timestamp; source: FlowRecordUpdate.updateAccount2010 */
    "Expected_Account"."Behavioral_Health_Completion__c" AS "expected__Behavioral_Health_Completion__c", /* Expected Account.Behavioral_Health_Completion__c: Behavioral health completion timestamp; source: FlowRecordUpdate.updateAccount2011 */
    "Expected_Account"."Environmental_Exposures_Date_Time__c" AS "expected__Environmental_Exposures_Date_Time__c", /* Expected Account.Environmental_Exposures_Date_Time__c: Environmental exposures completion timestamp; source: FlowRecordUpdate.updateAccount2012 */
    "Expected_Account"."Social_Determinants_of_Health_Completion__c" AS "expected__Social_Determinants_of_Health_Completion__c", /* Expected Account.Social_Determinants_of_Health_Completion__c: Social determinants completion timestamp; source: FlowRecordUpdate.updateAccount2013 */
    "Account_After"."Age_at_Time_of_Consent__pc" AS "observed__Age_at_Time_of_Consent__pc", /* Independently observed Account.Age_at_Time_of_Consent__pc; source: Account.Age_at_Time_of_Consent__pc */
    "Account_After"."CABOR_Completion_Date__c" AS "observed__CABOR_Completion_Date__c", /* Independently observed Account.CABOR_Completion_Date__c; source: Account.CABOR_Completion_Date__c */
    "Account_After"."Earliest_Primary_Consent_Date_for_Report__c" AS "observed__Earliest_Primary_Consent_Date_for_Report__c", /* Independently observed Account.Earliest_Primary_Consent_Date_for_Report__c; source: Account.Earliest_Primary_Consent_Date_for_Report__c */
    "Account_After"."Latest_Primary_Consent_Date_for_Report__c" AS "observed__Latest_Primary_Consent_Date_for_Report__c", /* Independently observed Account.Latest_Primary_Consent_Date_for_Report__c; source: Account.Latest_Primary_Consent_Date_for_Report__c */
    "Account_After"."EHR_Consent_Date_Time__c" AS "observed__EHR_Consent_Date_Time__c", /* Independently observed Account.EHR_Consent_Date_Time__c; source: Account.EHR_Consent_Date_Time__c */
    "Account_After"."EHR_Reconsent_Date_Time__c" AS "observed__EHR_Reconsent_Date_Time__c", /* Independently observed Account.EHR_Reconsent_Date_Time__c; source: Account.EHR_Reconsent_Date_Time__c */
    "Account_After"."Update_to_Primary_Consent_Completed__c" AS "observed__Update_to_Primary_Consent_Completed__c", /* Independently observed Account.Update_to_Primary_Consent_Completed__c; source: Account.Update_to_Primary_Consent_Completed__c */
    "Account_After"."Basics_Date_Time__c" AS "observed__Basics_Date_Time__c", /* Independently observed Account.Basics_Date_Time__c; source: Account.Basics_Date_Time__c */
    "Account_After"."Overall_Health_Date_Time__c" AS "observed__Overall_Health_Date_Time__c", /* Independently observed Account.Overall_Health_Date_Time__c; source: Account.Overall_Health_Date_Time__c */
    "Account_After"."Lifestyle_Date_Time__c" AS "observed__Lifestyle_Date_Time__c", /* Independently observed Account.Lifestyle_Date_Time__c; source: Account.Lifestyle_Date_Time__c */
    "Account_After"."Personal_and_Family_History_Complete__c" AS "observed__Personal_and_Family_History_Complete__c", /* Independently observed Account.Personal_and_Family_History_Complete__c; source: Account.Personal_and_Family_History_Complete__c */
    "Account_After"."HC_Access_Date_Time__c" AS "observed__HC_Access_Date_Time__c", /* Independently observed Account.HC_Access_Date_Time__c; source: Account.HC_Access_Date_Time__c */
    "Account_After"."Life_Functioning_Date_Time__c" AS "observed__Life_Functioning_Date_Time__c", /* Independently observed Account.Life_Functioning_Date_Time__c; source: Account.Life_Functioning_Date_Time__c */
    "Account_After"."First_Physical_Measurement_Date_Time__c" AS "observed__First_Physical_Measurement_Date_Time__c", /* Independently observed Account.First_Physical_Measurement_Date_Time__c; source: Account.First_Physical_Measurement_Date_Time__c */
    "Account_After"."Last_Physical_Measurement_Date_Time__c" AS "observed__Last_Physical_Measurement_Date_Time__c", /* Independently observed Account.Last_Physical_Measurement_Date_Time__c; source: Account.Last_Physical_Measurement_Date_Time__c */
    "Account_After"."EH_Date_Time__c" AS "observed__EH_Date_Time__c", /* Independently observed Account.EH_Date_Time__c; source: Account.EH_Date_Time__c */
    "Account_After"."Behavioral_Health_Completion__c" AS "observed__Behavioral_Health_Completion__c", /* Independently observed Account.Behavioral_Health_Completion__c; source: Account.Behavioral_Health_Completion__c */
    "Account_After"."Environmental_Exposures_Date_Time__c" AS "observed__Environmental_Exposures_Date_Time__c", /* Independently observed Account.Environmental_Exposures_Date_Time__c; source: Account.Environmental_Exposures_Date_Time__c */
    "Account_After"."Social_Determinants_of_Health_Completion__c" AS "observed__Social_Determinants_of_Health_Completion__c" /* Independently observed Account.Social_Determinants_of_Health_Completion__c; source: Account.Social_Determinants_of_Health_Completion__c */
  FROM "Expected_Account" AS "Expected_Account"
  LEFT OUTER JOIN "Account_After" AS "Account_After"
    ON "Expected_Account"."Account.Id" = "Account_After"."Id"
    AND "Expected_Account"."Record.Id" = "Account_After"."survey_result_id"
) AS comparison;

-- rollups
SELECT
  *
FROM (
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
  ), "Survey_Results_At_Snapshot" AS (
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
  ), "Account_Snapshot" AS (
    SELECT
      *
    FROM "Account_At_Snapshot" AS "Account_At_Snapshot"
  ), "Person_Account" AS (
    SELECT
      "Account_At_Snapshot_2"."Id",
      "Account_At_Snapshot_2"."PersonContactId"
    FROM "Account_At_Snapshot" AS "Account_At_Snapshot_2"
    WHERE
      "Account_At_Snapshot_2"."IsPersonAccount"
  ), "Survey_Result__c" AS (
    SELECT
      "Survey_Results_At_Snapshot"."Participant__c",
      "Survey_Results_At_Snapshot"."Completion_Status__c",
      "Survey_Results_At_Snapshot"."Survey_Index_Number__c",
      "Survey_Results_At_Snapshot"."Consent_Status__c",
      "Survey_Results_At_Snapshot"."Consent_Revoked__c"
    FROM "Survey_Results_At_Snapshot" AS "Survey_Results_At_Snapshot"
  ), "Expected_Rollups" AS (
    SELECT
      "Person_Account_2"."Account.Id",
      "Person_Account_2"."PersonContactId",
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
      ) AS "EHR_Authorized__pc",
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
      ) AS "Count_of_Completed_EHR_Auth__pc",
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
      ) AS "Count_of_Completed_Primary_Consent__pc",
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
      ) AS "Count_of_Completed_Reconsent__pc",
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
      ) AS "PPI_2_Completion_Count__pc",
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
      ) AS "PPI_3_Completion_Count__pc",
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
      ) AS "EHR_Consent_Active__pc",
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
      ) AS "EHR_Consent_Declined__pc",
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
      ) AS "PP1_Basics_Survey_Complete__pc",
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
      ) AS "Re_Consent_Declined__pc",
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
      ) AS "Re_consent_Active__pc",
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
      ) AS "Primary_Consent_Declined__pc",
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
      ) AS "EHR_Consent_Ever__pc",
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
      ) AS "Assent_Completion_Count__pc",
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
      ) AS "Pediatric_Permission_Completion_Count__pc",
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
      ) AS "X0_6_Peds_Permission_Count__pc",
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
      ) AS "X0_6_Peds_Permission_Declined_Count__pc",
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
      ) AS "X0_6_Peds_Permission_Revoked_Count__pc",
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
      ) AS "EHR_Pediatric_Complete__pc"
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
      2
  )
  SELECT
    "Expected_Rollups"."Account.Id" AS "expected_account_id", /* Source identity: Account.Id; source: Account.Id */
    "Expected_Rollups"."PersonContactId" AS "person_contact_id", /* Source identity: PersonContactId; source: Account.PersonContactId */
    "Account_Snapshot"."Id" AS "observed_account_id", /* Source identity: Account.Id; source: Account.Id */
    "Expected_Rollups"."EHR_Authorized__pc" AS "expected__EHR_Authorized__pc", /* Expected Account.EHR_Authorized__pc: Ehr authorized; source: Account.EHR_Authorized__pc */
    "Expected_Rollups"."Count_of_Completed_EHR_Auth__pc" AS "expected__Count_of_Completed_EHR_Auth__pc", /* Expected Account.Count_of_Completed_EHR_Auth__pc: Count of completed ehr auth; source: Account.Count_of_Completed_EHR_Auth__pc */
    "Expected_Rollups"."Count_of_Completed_Primary_Consent__pc" AS "expected__Count_of_Completed_Primary_Consent__pc", /* Expected Account.Count_of_Completed_Primary_Consent__pc: Count of completed primary consent; source: Account.Count_of_Completed_Primary_Consent__pc */
    "Expected_Rollups"."Count_of_Completed_Reconsent__pc" AS "expected__Count_of_Completed_Reconsent__pc", /* Expected Account.Count_of_Completed_Reconsent__pc: Count of completed reconsent; source: Account.Count_of_Completed_Reconsent__pc */
    "Expected_Rollups"."PPI_2_Completion_Count__pc" AS "expected__PPI_2_Completion_Count__pc", /* Expected Account.PPI_2_Completion_Count__pc: Ppi 2 completion count; source: Account.PPI_2_Completion_Count__pc */
    "Expected_Rollups"."PPI_3_Completion_Count__pc" AS "expected__PPI_3_Completion_Count__pc", /* Expected Account.PPI_3_Completion_Count__pc: Ppi 3 completion count; source: Account.PPI_3_Completion_Count__pc */
    "Expected_Rollups"."EHR_Consent_Active__pc" AS "expected__EHR_Consent_Active__pc", /* Expected Account.EHR_Consent_Active__pc: Ehr consent active; source: Account.EHR_Consent_Active__pc */
    "Expected_Rollups"."EHR_Consent_Declined__pc" AS "expected__EHR_Consent_Declined__pc", /* Expected Account.EHR_Consent_Declined__pc: Ehr consent declined; source: Account.EHR_Consent_Declined__pc */
    "Expected_Rollups"."PP1_Basics_Survey_Complete__pc" AS "expected__PP1_Basics_Survey_Complete__pc", /* Expected Account.PP1_Basics_Survey_Complete__pc: Pp1 basics survey complete; source: Account.PP1_Basics_Survey_Complete__pc */
    "Expected_Rollups"."Re_Consent_Declined__pc" AS "expected__Re_Consent_Declined__pc", /* Expected Account.Re_Consent_Declined__pc: Re consent declined; source: Account.Re_Consent_Declined__pc */
    "Expected_Rollups"."Re_consent_Active__pc" AS "expected__Re_consent_Active__pc", /* Expected Account.Re_consent_Active__pc: Re consent active; source: Account.Re_consent_Active__pc */
    "Expected_Rollups"."Primary_Consent_Declined__pc" AS "expected__Primary_Consent_Declined__pc", /* Expected Account.Primary_Consent_Declined__pc: Primary consent declined; source: Account.Primary_Consent_Declined__pc */
    "Expected_Rollups"."EHR_Consent_Ever__pc" AS "expected__EHR_Consent_Ever__pc", /* Expected Account.EHR_Consent_Ever__pc: Ehr consent ever; source: Account.EHR_Consent_Ever__pc */
    "Expected_Rollups"."Assent_Completion_Count__pc" AS "expected__Assent_Completion_Count__pc", /* Expected Account.Assent_Completion_Count__pc: Assent completion count; source: Account.Assent_Completion_Count__pc */
    "Expected_Rollups"."Pediatric_Permission_Completion_Count__pc" AS "expected__Pediatric_Permission_Completion_Count__pc", /* Expected Account.Pediatric_Permission_Completion_Count__pc: Pediatric permission completion count; source: Account.Pediatric_Permission_Completion_Count__pc */
    "Expected_Rollups"."X0_6_Peds_Permission_Count__pc" AS "expected__X0_6_Peds_Permission_Count__pc", /* Expected Account.X0_6_Peds_Permission_Count__pc: X0 6 peds permission count; source: Account.X0_6_Peds_Permission_Count__pc */
    "Expected_Rollups"."X0_6_Peds_Permission_Declined_Count__pc" AS "expected__X0_6_Peds_Permission_Declined_Count__pc", /* Expected Account.X0_6_Peds_Permission_Declined_Count__pc: X0 6 peds permission declined count; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
    "Expected_Rollups"."X0_6_Peds_Permission_Revoked_Count__pc" AS "expected__X0_6_Peds_Permission_Revoked_Count__pc", /* Expected Account.X0_6_Peds_Permission_Revoked_Count__pc: X0 6 peds permission revoked count; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
    "Expected_Rollups"."EHR_Pediatric_Complete__pc" AS "expected__EHR_Pediatric_Complete__pc", /* Expected Account.EHR_Pediatric_Complete__pc: Ehr pediatric complete; source: Account.EHR_Pediatric_Complete__pc */
    "Account_Snapshot"."EHR_Authorized__pc" AS "observed__EHR_Authorized__pc", /* Independently observed Account.EHR_Authorized__pc; source: Account.EHR_Authorized__pc */
    "Account_Snapshot"."Count_of_Completed_EHR_Auth__pc" AS "observed__Count_of_Completed_EHR_Auth__pc", /* Independently observed Account.Count_of_Completed_EHR_Auth__pc; source: Account.Count_of_Completed_EHR_Auth__pc */
    "Account_Snapshot"."Count_of_Completed_Primary_Consent__pc" AS "observed__Count_of_Completed_Primary_Consent__pc", /* Independently observed Account.Count_of_Completed_Primary_Consent__pc; source: Account.Count_of_Completed_Primary_Consent__pc */
    "Account_Snapshot"."Count_of_Completed_Reconsent__pc" AS "observed__Count_of_Completed_Reconsent__pc", /* Independently observed Account.Count_of_Completed_Reconsent__pc; source: Account.Count_of_Completed_Reconsent__pc */
    "Account_Snapshot"."PPI_2_Completion_Count__pc" AS "observed__PPI_2_Completion_Count__pc", /* Independently observed Account.PPI_2_Completion_Count__pc; source: Account.PPI_2_Completion_Count__pc */
    "Account_Snapshot"."PPI_3_Completion_Count__pc" AS "observed__PPI_3_Completion_Count__pc", /* Independently observed Account.PPI_3_Completion_Count__pc; source: Account.PPI_3_Completion_Count__pc */
    "Account_Snapshot"."EHR_Consent_Active__pc" AS "observed__EHR_Consent_Active__pc", /* Independently observed Account.EHR_Consent_Active__pc; source: Account.EHR_Consent_Active__pc */
    "Account_Snapshot"."EHR_Consent_Declined__pc" AS "observed__EHR_Consent_Declined__pc", /* Independently observed Account.EHR_Consent_Declined__pc; source: Account.EHR_Consent_Declined__pc */
    "Account_Snapshot"."PP1_Basics_Survey_Complete__pc" AS "observed__PP1_Basics_Survey_Complete__pc", /* Independently observed Account.PP1_Basics_Survey_Complete__pc; source: Account.PP1_Basics_Survey_Complete__pc */
    "Account_Snapshot"."Re_Consent_Declined__pc" AS "observed__Re_Consent_Declined__pc", /* Independently observed Account.Re_Consent_Declined__pc; source: Account.Re_Consent_Declined__pc */
    "Account_Snapshot"."Re_consent_Active__pc" AS "observed__Re_consent_Active__pc", /* Independently observed Account.Re_consent_Active__pc; source: Account.Re_consent_Active__pc */
    "Account_Snapshot"."Primary_Consent_Declined__pc" AS "observed__Primary_Consent_Declined__pc", /* Independently observed Account.Primary_Consent_Declined__pc; source: Account.Primary_Consent_Declined__pc */
    "Account_Snapshot"."EHR_Consent_Ever__pc" AS "observed__EHR_Consent_Ever__pc", /* Independently observed Account.EHR_Consent_Ever__pc; source: Account.EHR_Consent_Ever__pc */
    "Account_Snapshot"."Assent_Completion_Count__pc" AS "observed__Assent_Completion_Count__pc", /* Independently observed Account.Assent_Completion_Count__pc; source: Account.Assent_Completion_Count__pc */
    "Account_Snapshot"."Pediatric_Permission_Completion_Count__pc" AS "observed__Pediatric_Permission_Completion_Count__pc", /* Independently observed Account.Pediatric_Permission_Completion_Count__pc; source: Account.Pediatric_Permission_Completion_Count__pc */
    "Account_Snapshot"."X0_6_Peds_Permission_Count__pc" AS "observed__X0_6_Peds_Permission_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Count__pc; source: Account.X0_6_Peds_Permission_Count__pc */
    "Account_Snapshot"."X0_6_Peds_Permission_Declined_Count__pc" AS "observed__X0_6_Peds_Permission_Declined_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Declined_Count__pc; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
    "Account_Snapshot"."X0_6_Peds_Permission_Revoked_Count__pc" AS "observed__X0_6_Peds_Permission_Revoked_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Revoked_Count__pc; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
    "Account_Snapshot"."EHR_Pediatric_Complete__pc" AS "observed__EHR_Pediatric_Complete__pc" /* Independently observed Account.EHR_Pediatric_Complete__pc; source: Account.EHR_Pediatric_Complete__pc */
  FROM "Expected_Rollups" AS "Expected_Rollups"
  LEFT OUTER JOIN "Account_Snapshot" AS "Account_Snapshot"
    ON "Expected_Rollups"."Account.Id" = "Account_Snapshot"."Id"
) AS comparison;
