-- ILLUSTRATIVE bindings/event/times; source profiles are defined in schemas/.
-- Direct SELECTs over history. Verify physical catalog types before execution.
-- Execution: 2026-10-21 12:00; BEFORE: 11:59:59; settled AFTER: 12:05.

-- flow comparison
SELECT
  *
FROM (
  SELECT
    "t41"."Record.Id" AS "survey_result_id", /* Source identity: Record.Id; source: Survey_Result__c.Id */
    "t41"."Participant__c" AS "participant_contact_id", /* Source identity: Participant__c; source: Survey_Result__c.Participant__c */
    "t41"."Account.Id" AS "expected_account_id", /* Source identity: Account.Id; source: Account.Id */
    "t11"."Id" AS "observed_account_id", /* Source identity: Account.Id; source: Account.Id */
    "t41"."Survey_Index_Number__c" AS "survey_index_number", /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */
    "t41"."CABOR_Completion_Date__c_is_deterministic" AS "cabor_lookup_is_deterministic", /* Signature lookup has at most one candidate on the assent route; source: FlowRecordLookup.Get_Permission_1007 */
    "t41"."Age_at_Time_of_Consent__pc" AS "expected__Age_at_Time_of_Consent__pc", /* Expected Account.Age_at_Time_of_Consent__pc: Age at flow execution; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowFormula.formAgeCalculation */
    "t41"."CABOR_Completion_Date__c" AS "expected__CABOR_Completion_Date__c", /* Expected Account.CABOR_Completion_Date__c: California signature timestamp; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowRecordLookup.Get_Permission_1007 */
    "t41"."Earliest_Primary_Consent_Date_for_Report__c" AS "expected__Earliest_Primary_Consent_Date_for_Report__c", /* Expected Account.Earliest_Primary_Consent_Date_for_Report__c: Earliest primary consent report timestamp; source: FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Negative */
    "t41"."Latest_Primary_Consent_Date_for_Report__c" AS "expected__Latest_Primary_Consent_Date_for_Report__c", /* Expected Account.Latest_Primary_Consent_Date_for_Report__c: Latest primary consent report timestamp; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative */
    "t41"."EHR_Consent_Date_Time__c" AS "expected__EHR_Consent_Date_Time__c", /* Expected Account.EHR_Consent_Date_Time__c: Ehr consent timestamp; source: FlowRecordUpdate.updateAccount1003_NegativeSF */
    "t41"."EHR_Reconsent_Date_Time__c" AS "expected__EHR_Reconsent_Date_Time__c", /* Expected Account.EHR_Reconsent_Date_Time__c: Ehr reconsent timestamp; source: FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF */
    "t41"."Update_to_Primary_Consent_Completed__c" AS "expected__Update_to_Primary_Consent_Completed__c", /* Expected Account.Update_to_Primary_Consent_Completed__c: Primary consent update timestamp; source: FlowRecordUpdate.updateAccount1005 */
    "t41"."Basics_Date_Time__c" AS "expected__Basics_Date_Time__c", /* Expected Account.Basics_Date_Time__c: Basics completion timestamp; source: FlowRecordUpdate.updateAccount2001 */
    "t41"."Overall_Health_Date_Time__c" AS "expected__Overall_Health_Date_Time__c", /* Expected Account.Overall_Health_Date_Time__c: Overall health completion timestamp; source: FlowRecordUpdate.updateAccount2003 */
    "t41"."Lifestyle_Date_Time__c" AS "expected__Lifestyle_Date_Time__c", /* Expected Account.Lifestyle_Date_Time__c: Lifestyle completion timestamp; source: FlowRecordUpdate.updateAccount2005 */
    "t41"."Personal_and_Family_History_Complete__c" AS "expected__Personal_and_Family_History_Complete__c", /* Expected Account.Personal_and_Family_History_Complete__c: Personal and family history completion timestamp; source: FlowRecordUpdate.updateAccount2006 */
    "t41"."HC_Access_Date_Time__c" AS "expected__HC_Access_Date_Time__c", /* Expected Account.HC_Access_Date_Time__c: Healthcare access completion timestamp; source: FlowRecordUpdate.updateAccount2007 */
    "t41"."Life_Functioning_Date_Time__c" AS "expected__Life_Functioning_Date_Time__c", /* Expected Account.Life_Functioning_Date_Time__c: Life functioning completion timestamp; source: FlowRecordUpdate.updateAccount2008 */
    "t41"."First_Physical_Measurement_Date_Time__c" AS "expected__First_Physical_Measurement_Date_Time__c", /* Expected Account.First_Physical_Measurement_Date_Time__c: First remote physical measurement timestamp; source: FlowRecordUpdate.updateAccount2009, FlowRecordLookup.getFirstPhysicalMeasurement */
    "t41"."Last_Physical_Measurement_Date_Time__c" AS "expected__Last_Physical_Measurement_Date_Time__c", /* Expected Account.Last_Physical_Measurement_Date_Time__c: Latest processed remote physical measurement timestamp; source: FlowRecordUpdate.updateAccount2009 */
    "t41"."EH_Date_Time__c" AS "expected__EH_Date_Time__c", /* Expected Account.EH_Date_Time__c: Emotional health completion timestamp; source: FlowRecordUpdate.updateAccount2010 */
    "t41"."Behavioral_Health_Completion__c" AS "expected__Behavioral_Health_Completion__c", /* Expected Account.Behavioral_Health_Completion__c: Behavioral health completion timestamp; source: FlowRecordUpdate.updateAccount2011 */
    "t41"."Environmental_Exposures_Date_Time__c" AS "expected__Environmental_Exposures_Date_Time__c", /* Expected Account.Environmental_Exposures_Date_Time__c: Environmental exposures completion timestamp; source: FlowRecordUpdate.updateAccount2012 */
    "t41"."Social_Determinants_of_Health_Completion__c" AS "expected__Social_Determinants_of_Health_Completion__c", /* Expected Account.Social_Determinants_of_Health_Completion__c: Social determinants completion timestamp; source: FlowRecordUpdate.updateAccount2013 */
    "t11"."Age_at_Time_of_Consent__pc" AS "observed__Age_at_Time_of_Consent__pc", /* Independently observed Account.Age_at_Time_of_Consent__pc; source: Account.Age_at_Time_of_Consent__pc */
    "t11"."CABOR_Completion_Date__c" AS "observed__CABOR_Completion_Date__c", /* Independently observed Account.CABOR_Completion_Date__c; source: Account.CABOR_Completion_Date__c */
    "t11"."Earliest_Primary_Consent_Date_for_Report__c" AS "observed__Earliest_Primary_Consent_Date_for_Report__c", /* Independently observed Account.Earliest_Primary_Consent_Date_for_Report__c; source: Account.Earliest_Primary_Consent_Date_for_Report__c */
    "t11"."Latest_Primary_Consent_Date_for_Report__c" AS "observed__Latest_Primary_Consent_Date_for_Report__c", /* Independently observed Account.Latest_Primary_Consent_Date_for_Report__c; source: Account.Latest_Primary_Consent_Date_for_Report__c */
    "t11"."EHR_Consent_Date_Time__c" AS "observed__EHR_Consent_Date_Time__c", /* Independently observed Account.EHR_Consent_Date_Time__c; source: Account.EHR_Consent_Date_Time__c */
    "t11"."EHR_Reconsent_Date_Time__c" AS "observed__EHR_Reconsent_Date_Time__c", /* Independently observed Account.EHR_Reconsent_Date_Time__c; source: Account.EHR_Reconsent_Date_Time__c */
    "t11"."Update_to_Primary_Consent_Completed__c" AS "observed__Update_to_Primary_Consent_Completed__c", /* Independently observed Account.Update_to_Primary_Consent_Completed__c; source: Account.Update_to_Primary_Consent_Completed__c */
    "t11"."Basics_Date_Time__c" AS "observed__Basics_Date_Time__c", /* Independently observed Account.Basics_Date_Time__c; source: Account.Basics_Date_Time__c */
    "t11"."Overall_Health_Date_Time__c" AS "observed__Overall_Health_Date_Time__c", /* Independently observed Account.Overall_Health_Date_Time__c; source: Account.Overall_Health_Date_Time__c */
    "t11"."Lifestyle_Date_Time__c" AS "observed__Lifestyle_Date_Time__c", /* Independently observed Account.Lifestyle_Date_Time__c; source: Account.Lifestyle_Date_Time__c */
    "t11"."Personal_and_Family_History_Complete__c" AS "observed__Personal_and_Family_History_Complete__c", /* Independently observed Account.Personal_and_Family_History_Complete__c; source: Account.Personal_and_Family_History_Complete__c */
    "t11"."HC_Access_Date_Time__c" AS "observed__HC_Access_Date_Time__c", /* Independently observed Account.HC_Access_Date_Time__c; source: Account.HC_Access_Date_Time__c */
    "t11"."Life_Functioning_Date_Time__c" AS "observed__Life_Functioning_Date_Time__c", /* Independently observed Account.Life_Functioning_Date_Time__c; source: Account.Life_Functioning_Date_Time__c */
    "t11"."First_Physical_Measurement_Date_Time__c" AS "observed__First_Physical_Measurement_Date_Time__c", /* Independently observed Account.First_Physical_Measurement_Date_Time__c; source: Account.First_Physical_Measurement_Date_Time__c */
    "t11"."Last_Physical_Measurement_Date_Time__c" AS "observed__Last_Physical_Measurement_Date_Time__c", /* Independently observed Account.Last_Physical_Measurement_Date_Time__c; source: Account.Last_Physical_Measurement_Date_Time__c */
    "t11"."EH_Date_Time__c" AS "observed__EH_Date_Time__c", /* Independently observed Account.EH_Date_Time__c; source: Account.EH_Date_Time__c */
    "t11"."Behavioral_Health_Completion__c" AS "observed__Behavioral_Health_Completion__c", /* Independently observed Account.Behavioral_Health_Completion__c; source: Account.Behavioral_Health_Completion__c */
    "t11"."Environmental_Exposures_Date_Time__c" AS "observed__Environmental_Exposures_Date_Time__c", /* Independently observed Account.Environmental_Exposures_Date_Time__c; source: Account.Environmental_Exposures_Date_Time__c */
    "t11"."Social_Determinants_of_Health_Completion__c" AS "observed__Social_Determinants_of_Health_Completion__c" /* Independently observed Account.Social_Determinants_of_Health_Completion__c; source: Account.Social_Determinants_of_Health_Completion__c */
  FROM (
    SELECT
      "t39"."Id" AS "Record.Id",
      "t39"."Participant__r.Account.Id" AS "Account.Id",
      "t39"."Participant__c",
      "t39"."Survey_Index_Number__c",
      "t39"."FlowDecision_Survey_Completion_Route_target",
      "t39"."FlowDecision_Primary_Consent_Account_Update_target",
      "t39"."FlowDecision_EHR_Consent_Account_Update_target",
      "t39"."FlowDecision_Assent_Account_Update_target",
      "t39"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" IN (
          'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent',
          'FlowRecordLookup.Pediatric_Permission_For_Assent'
        )
        THEN "t39"."FlowFormula_Age_At_Execution"
        ELSE "t39"."Participant__r.Account.Age_at_Time_of_Consent__pc"
      END AS "Age_at_Time_of_Consent__pc",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
        THEN "t39"."California_Signature__c"
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
        THEN "t39"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
        ELSE "t39"."Participant__r.Account.CABOR_Completion_Date__c"
      END AS "CABOR_Completion_Date__c",
      CASE
        WHEN (
          "t39"."FlowDecision_Primary_Consent_Account_Update_target" = 'FlowRecordUpdate.Primary_Consent_With_Prior_Yes'
        )
        OR (
          "t39"."FlowDecision_Assent_Account_Update_target" = 'FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date'
        )
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c"
      END AS "Earliest_Primary_Consent_Date_for_Report__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" IN (
          'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent',
          'FlowRecordLookup.Pediatric_Permission_For_Assent'
        )
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c"
      END AS "Latest_Primary_Consent_Date_for_Report__c",
      CASE
        WHEN "t39"."FlowDecision_EHR_Consent_Account_Update_target" = 'FlowRecordUpdate.EHR_Consent_With_Prior_Yes'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.EHR_Consent_Date_Time__c"
      END AS "EHR_Consent_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_EHR_Consent_Account_Update_target" = 'FlowRecordUpdate.EHR_Consent_Without_Prior_Yes'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.EHR_Reconsent_Date_Time__c"
      END AS "EHR_Reconsent_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Primary_Consent_Update_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Update_to_Primary_Consent_Completed__c"
      END AS "Update_to_Primary_Consent_Completed__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Basics_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Basics_Date_Time__c"
      END AS "Basics_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Overall_Health_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Overall_Health_Date_Time__c"
      END AS "Overall_Health_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Lifestyle_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Lifestyle_Date_Time__c"
      END AS "Lifestyle_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Personal_And_Family_History_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Personal_and_Family_History_Complete__c"
      END AS "Personal_and_Family_History_Complete__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Healthcare_Access_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.HC_Access_Date_Time__c"
      END AS "HC_Access_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Life_Functioning_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Life_Functioning_Date_Time__c"
      END AS "Life_Functioning_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.First_Remote_Physical_Measurement'
        THEN "t39"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.First_Physical_Measurement_Date_Time__c"
      END AS "First_Physical_Measurement_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.First_Remote_Physical_Measurement'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c"
      END AS "Last_Physical_Measurement_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Emotional_Health_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.EH_Date_Time__c"
      END AS "EH_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Behavioral_Health_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Behavioral_Health_Completion__c"
      END AS "Behavioral_Health_Completion__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Environmental_Exposures_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Environmental_Exposures_Date_Time__c"
      END AS "Environmental_Exposures_Date_Time__c",
      CASE
        WHEN "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordUpdate.Social_Determinants_Completion'
        THEN "t39"."Completion_Status_Timestamp__c"
        ELSE "t39"."Participant__r.Account.Social_Determinants_of_Health_Completion__c"
      END AS "Social_Determinants_of_Health_Completion__c",
      NOT (
        COALESCE(
          "t39"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent',
          FALSE
        )
      )
      OR (
        "t39"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count" <= 1
      ) AS "CABOR_Completion_Date__c_is_deterministic"
    FROM (
      SELECT
        "t38"."Id",
        "t38"."Participant__c",
        "t38"."Survey_Index_Number__c",
        "t38"."Completion_Status__c",
        "t38"."Consent_Status__c",
        "t38"."Completion_Status_Timestamp__c",
        "t38"."California_Signature__c",
        "t38"."Participant__r.AccountId",
        "t38"."Participant__r.Birthdate",
        "t38"."Participant__r.Account.Id",
        "t38"."Participant__r.Account.Age_at_Time_of_Consent__pc",
        "t38"."Participant__r.Account.CABOR_Completion_Date__c",
        "t38"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
        "t38"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
        "t38"."Participant__r.Account.EHR_Consent_Date_Time__c",
        "t38"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
        "t38"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
        "t38"."Participant__r.Account.Basics_Date_Time__c",
        "t38"."Participant__r.Account.Overall_Health_Date_Time__c",
        "t38"."Participant__r.Account.Lifestyle_Date_Time__c",
        "t38"."Participant__r.Account.Personal_and_Family_History_Complete__c",
        "t38"."Participant__r.Account.HC_Access_Date_Time__c",
        "t38"."Participant__r.Account.Life_Functioning_Date_Time__c",
        "t38"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
        "t38"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
        "t38"."Participant__r.Account.EH_Date_Time__c",
        "t38"."Participant__r.Account.Behavioral_Health_Completion__c",
        "t38"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
        "t38"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
        "t38"."FlowDecision_Survey_Completion_Route_target",
        "t38"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
        "t38"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
        "t38"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
        "t38"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
        "t38"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
        "t38"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
        "t38"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
        "t38"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
        "t38"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
        CASE
          WHEN (
            "t38"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
          )
          AND (
            "t38"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NULL
          )
          THEN 'FlowRecordUpdate.Primary_Consent_Without_Prior_Yes'
          WHEN (
            "t38"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
          )
          AND NOT (
            "t38"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NULL
          )
          THEN 'FlowRecordUpdate.Primary_Consent_With_Prior_Yes'
          ELSE CAST(NULL AS VARCHAR)
        END AS "FlowDecision_Primary_Consent_Account_Update_target",
        CASE
          WHEN (
            "t38"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
          )
          AND (
            "t38"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NULL
          )
          THEN 'FlowRecordUpdate.EHR_Consent_Without_Prior_Yes'
          WHEN (
            "t38"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
          )
          AND NOT (
            "t38"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NULL
          )
          THEN 'FlowRecordUpdate.EHR_Consent_With_Prior_Yes'
          ELSE CAST(NULL AS VARCHAR)
        END AS "FlowDecision_EHR_Consent_Account_Update_target",
        CASE
          WHEN (
            "t38"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
          )
          AND (
            (
              "t38"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NULL
            )
            AND (
              "t38"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NULL
            )
          )
          THEN 'FlowRecordUpdate.Assent_No_Permission_And_No_Primary_Date'
          WHEN (
            "t38"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
          )
          AND NOT (
            (
              "t38"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NULL
            )
            AND (
              "t38"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NULL
            )
          )
          THEN 'FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date'
          ELSE CAST(NULL AS VARCHAR)
        END AS "FlowDecision_Assent_Account_Update_target",
        CAST(FLOOR(
          DATE_DIFF(
            'DAY',
            DATE_TRUNC('DAY', "t38"."Participant__r.Birthdate"),
            DATE_TRUNC('DAY', FROM_ISO8601_DATE('2026-10-21'))
          ) / CAST(365.25 AS DOUBLE)
        ) AS BIGINT) AS "FlowFormula_Age_At_Execution"
      FROM (
        SELECT
          "t37"."Id",
          "t37"."Participant__c",
          "t37"."Survey_Index_Number__c",
          "t37"."Completion_Status__c",
          "t37"."Consent_Status__c",
          "t37"."Completion_Status_Timestamp__c",
          "t37"."California_Signature__c",
          "t37"."Participant__r.AccountId",
          "t37"."Participant__r.Birthdate",
          "t37"."Participant__r.Account.Id",
          "t37"."Participant__r.Account.Age_at_Time_of_Consent__pc",
          "t37"."Participant__r.Account.CABOR_Completion_Date__c",
          "t37"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
          "t37"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
          "t37"."Participant__r.Account.EHR_Consent_Date_Time__c",
          "t37"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
          "t37"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
          "t37"."Participant__r.Account.Basics_Date_Time__c",
          "t37"."Participant__r.Account.Overall_Health_Date_Time__c",
          "t37"."Participant__r.Account.Lifestyle_Date_Time__c",
          "t37"."Participant__r.Account.Personal_and_Family_History_Complete__c",
          "t37"."Participant__r.Account.HC_Access_Date_Time__c",
          "t37"."Participant__r.Account.Life_Functioning_Date_Time__c",
          "t37"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
          "t37"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
          "t37"."Participant__r.Account.EH_Date_Time__c",
          "t37"."Participant__r.Account.Behavioral_Health_Completion__c",
          "t37"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
          "t37"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
          "t37"."FlowDecision_Survey_Completion_Route_target",
          "t37"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
          "t37"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
          "t37"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
          "t37"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
          "t37"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
          "t37"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
          "t19"."Id" AS "FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
          COALESCE("t19"."match_count", 0) AS "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
          "t19"."California_Signature__c" AS "FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
        FROM (
          SELECT
            "t35"."Id",
            "t35"."Participant__c",
            "t35"."Survey_Index_Number__c",
            "t35"."Completion_Status__c",
            "t35"."Consent_Status__c",
            "t35"."Completion_Status_Timestamp__c",
            "t35"."California_Signature__c",
            "t35"."Participant__r.AccountId",
            "t35"."Participant__r.Birthdate",
            "t35"."Participant__r.Account.Id",
            "t35"."Participant__r.Account.Age_at_Time_of_Consent__pc",
            "t35"."Participant__r.Account.CABOR_Completion_Date__c",
            "t35"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
            "t35"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
            "t35"."Participant__r.Account.EHR_Consent_Date_Time__c",
            "t35"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
            "t35"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
            "t35"."Participant__r.Account.Basics_Date_Time__c",
            "t35"."Participant__r.Account.Overall_Health_Date_Time__c",
            "t35"."Participant__r.Account.Lifestyle_Date_Time__c",
            "t35"."Participant__r.Account.Personal_and_Family_History_Complete__c",
            "t35"."Participant__r.Account.HC_Access_Date_Time__c",
            "t35"."Participant__r.Account.Life_Functioning_Date_Time__c",
            "t35"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
            "t35"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
            "t35"."Participant__r.Account.EH_Date_Time__c",
            "t35"."Participant__r.Account.Behavioral_Health_Completion__c",
            "t35"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
            "t35"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
            "t35"."FlowDecision_Survey_Completion_Route_target",
            "t35"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
            "t35"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
            "t35"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
            "t35"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
            "t35"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
            "t35"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
          FROM (
            SELECT
              *
            FROM (
              SELECT
                "t33"."Id",
                "t33"."Participant__c",
                "t33"."Survey_Index_Number__c",
                "t33"."Completion_Status__c",
                "t33"."Consent_Status__c",
                "t33"."Completion_Status_Timestamp__c",
                "t33"."California_Signature__c",
                "t33"."Participant__r.AccountId",
                "t33"."Participant__r.Birthdate",
                "t33"."Participant__r.Account.Id",
                "t33"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                "t33"."Participant__r.Account.CABOR_Completion_Date__c",
                "t33"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                "t33"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                "t33"."Participant__r.Account.EHR_Consent_Date_Time__c",
                "t33"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                "t33"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                "t33"."Participant__r.Account.Basics_Date_Time__c",
                "t33"."Participant__r.Account.Overall_Health_Date_Time__c",
                "t33"."Participant__r.Account.Lifestyle_Date_Time__c",
                "t33"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                "t33"."Participant__r.Account.HC_Access_Date_Time__c",
                "t33"."Participant__r.Account.Life_Functioning_Date_Time__c",
                "t33"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                "t33"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                "t33"."Participant__r.Account.EH_Date_Time__c",
                "t33"."Participant__r.Account.Behavioral_Health_Completion__c",
                "t33"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                "t33"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                "t33"."FlowDecision_Survey_Completion_Route_target",
                "t33"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                "t33"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                "t33"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                "t33"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                "t33"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
                "t33"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
                ROW_NUMBER() OVER (
                  PARTITION BY "t33"."Id"
                  ORDER BY "t33"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c" ASC NULLS FIRST
                ) - 1 AS "_lookup_rank"
              FROM (
                SELECT
                  "t32"."Id",
                  "t32"."Participant__c",
                  "t32"."Survey_Index_Number__c",
                  "t32"."Completion_Status__c",
                  "t32"."Consent_Status__c",
                  "t32"."Completion_Status_Timestamp__c",
                  "t32"."California_Signature__c",
                  "t32"."Participant__r.AccountId",
                  "t32"."Participant__r.Birthdate",
                  "t32"."Participant__r.Account.Id",
                  "t32"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                  "t32"."Participant__r.Account.CABOR_Completion_Date__c",
                  "t32"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                  "t32"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                  "t32"."Participant__r.Account.EHR_Consent_Date_Time__c",
                  "t32"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                  "t32"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                  "t32"."Participant__r.Account.Basics_Date_Time__c",
                  "t32"."Participant__r.Account.Overall_Health_Date_Time__c",
                  "t32"."Participant__r.Account.Lifestyle_Date_Time__c",
                  "t32"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                  "t32"."Participant__r.Account.HC_Access_Date_Time__c",
                  "t32"."Participant__r.Account.Life_Functioning_Date_Time__c",
                  "t32"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                  "t32"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                  "t32"."Participant__r.Account.EH_Date_Time__c",
                  "t32"."Participant__r.Account.Behavioral_Health_Completion__c",
                  "t32"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                  "t32"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                  "t32"."FlowDecision_Survey_Completion_Route_target",
                  "t32"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                  "t32"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                  "t32"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                  "t32"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                  "t13"."Id" AS "FlowRecordLookup.First_Remote_Physical_Measurement.Id",
                  "t13"."Completion_Status_Timestamp__c" AS "FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
                FROM (
                  SELECT
                    "t30"."Id",
                    "t30"."Participant__c",
                    "t30"."Survey_Index_Number__c",
                    "t30"."Completion_Status__c",
                    "t30"."Consent_Status__c",
                    "t30"."Completion_Status_Timestamp__c",
                    "t30"."California_Signature__c",
                    "t30"."Participant__r.AccountId",
                    "t30"."Participant__r.Birthdate",
                    "t30"."Participant__r.Account.Id",
                    "t30"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                    "t30"."Participant__r.Account.CABOR_Completion_Date__c",
                    "t30"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                    "t30"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                    "t30"."Participant__r.Account.EHR_Consent_Date_Time__c",
                    "t30"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                    "t30"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                    "t30"."Participant__r.Account.Basics_Date_Time__c",
                    "t30"."Participant__r.Account.Overall_Health_Date_Time__c",
                    "t30"."Participant__r.Account.Lifestyle_Date_Time__c",
                    "t30"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                    "t30"."Participant__r.Account.HC_Access_Date_Time__c",
                    "t30"."Participant__r.Account.Life_Functioning_Date_Time__c",
                    "t30"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                    "t30"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                    "t30"."Participant__r.Account.EH_Date_Time__c",
                    "t30"."Participant__r.Account.Behavioral_Health_Completion__c",
                    "t30"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                    "t30"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                    "t30"."FlowDecision_Survey_Completion_Route_target",
                    "t30"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                    "t30"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                    "t30"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                    "t30"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c"
                  FROM (
                    SELECT
                      *
                    FROM (
                      SELECT
                        "t28"."Id",
                        "t28"."Participant__c",
                        "t28"."Survey_Index_Number__c",
                        "t28"."Completion_Status__c",
                        "t28"."Consent_Status__c",
                        "t28"."Completion_Status_Timestamp__c",
                        "t28"."California_Signature__c",
                        "t28"."Participant__r.AccountId",
                        "t28"."Participant__r.Birthdate",
                        "t28"."Participant__r.Account.Id",
                        "t28"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                        "t28"."Participant__r.Account.CABOR_Completion_Date__c",
                        "t28"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                        "t28"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                        "t28"."Participant__r.Account.EHR_Consent_Date_Time__c",
                        "t28"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                        "t28"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                        "t28"."Participant__r.Account.Basics_Date_Time__c",
                        "t28"."Participant__r.Account.Overall_Health_Date_Time__c",
                        "t28"."Participant__r.Account.Lifestyle_Date_Time__c",
                        "t28"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                        "t28"."Participant__r.Account.HC_Access_Date_Time__c",
                        "t28"."Participant__r.Account.Life_Functioning_Date_Time__c",
                        "t28"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                        "t28"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                        "t28"."Participant__r.Account.EH_Date_Time__c",
                        "t28"."Participant__r.Account.Behavioral_Health_Completion__c",
                        "t28"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                        "t28"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                        "t28"."FlowDecision_Survey_Completion_Route_target",
                        "t28"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                        "t28"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                        "t28"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                        "t28"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                        ROW_NUMBER() OVER (
                          PARTITION BY "t28"."Id"
                          ORDER BY "t28"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
                        ) - 1 AS "_lookup_rank"
                      FROM (
                        SELECT
                          "t27"."Id",
                          "t27"."Participant__c",
                          "t27"."Survey_Index_Number__c",
                          "t27"."Completion_Status__c",
                          "t27"."Consent_Status__c",
                          "t27"."Completion_Status_Timestamp__c",
                          "t27"."California_Signature__c",
                          "t27"."Participant__r.AccountId",
                          "t27"."Participant__r.Birthdate",
                          "t27"."Participant__r.Account.Id",
                          "t27"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                          "t27"."Participant__r.Account.CABOR_Completion_Date__c",
                          "t27"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                          "t27"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                          "t27"."Participant__r.Account.EHR_Consent_Date_Time__c",
                          "t27"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                          "t27"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                          "t27"."Participant__r.Account.Basics_Date_Time__c",
                          "t27"."Participant__r.Account.Overall_Health_Date_Time__c",
                          "t27"."Participant__r.Account.Lifestyle_Date_Time__c",
                          "t27"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                          "t27"."Participant__r.Account.HC_Access_Date_Time__c",
                          "t27"."Participant__r.Account.Life_Functioning_Date_Time__c",
                          "t27"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                          "t27"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                          "t27"."Participant__r.Account.EH_Date_Time__c",
                          "t27"."Participant__r.Account.Behavioral_Health_Completion__c",
                          "t27"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                          "t27"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                          "t27"."FlowDecision_Survey_Completion_Route_target",
                          "t27"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                          "t27"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                          "t14"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                          "t14"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c"
                        FROM (
                          SELECT
                            "t25"."Id",
                            "t25"."Participant__c",
                            "t25"."Survey_Index_Number__c",
                            "t25"."Completion_Status__c",
                            "t25"."Consent_Status__c",
                            "t25"."Completion_Status_Timestamp__c",
                            "t25"."California_Signature__c",
                            "t25"."Participant__r.AccountId",
                            "t25"."Participant__r.Birthdate",
                            "t25"."Participant__r.Account.Id",
                            "t25"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                            "t25"."Participant__r.Account.CABOR_Completion_Date__c",
                            "t25"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                            "t25"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                            "t25"."Participant__r.Account.EHR_Consent_Date_Time__c",
                            "t25"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                            "t25"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                            "t25"."Participant__r.Account.Basics_Date_Time__c",
                            "t25"."Participant__r.Account.Overall_Health_Date_Time__c",
                            "t25"."Participant__r.Account.Lifestyle_Date_Time__c",
                            "t25"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                            "t25"."Participant__r.Account.HC_Access_Date_Time__c",
                            "t25"."Participant__r.Account.Life_Functioning_Date_Time__c",
                            "t25"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                            "t25"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                            "t25"."Participant__r.Account.EH_Date_Time__c",
                            "t25"."Participant__r.Account.Behavioral_Health_Completion__c",
                            "t25"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                            "t25"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                            "t25"."FlowDecision_Survey_Completion_Route_target",
                            "t25"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                            "t25"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c"
                          FROM (
                            SELECT
                              *
                            FROM (
                              SELECT
                                "t23"."Id",
                                "t23"."Participant__c",
                                "t23"."Survey_Index_Number__c",
                                "t23"."Completion_Status__c",
                                "t23"."Consent_Status__c",
                                "t23"."Completion_Status_Timestamp__c",
                                "t23"."California_Signature__c",
                                "t23"."Participant__r.AccountId",
                                "t23"."Participant__r.Birthdate",
                                "t23"."Participant__r.Account.Id",
                                "t23"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                "t23"."Participant__r.Account.CABOR_Completion_Date__c",
                                "t23"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                "t23"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                "t23"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                "t23"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                "t23"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                "t23"."Participant__r.Account.Basics_Date_Time__c",
                                "t23"."Participant__r.Account.Overall_Health_Date_Time__c",
                                "t23"."Participant__r.Account.Lifestyle_Date_Time__c",
                                "t23"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                "t23"."Participant__r.Account.HC_Access_Date_Time__c",
                                "t23"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                "t23"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                "t23"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                "t23"."Participant__r.Account.EH_Date_Time__c",
                                "t23"."Participant__r.Account.Behavioral_Health_Completion__c",
                                "t23"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                "t23"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                "t23"."FlowDecision_Survey_Completion_Route_target",
                                "t23"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                                "t23"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                                ROW_NUMBER() OVER (
                                  PARTITION BY "t23"."Id"
                                  ORDER BY "t23"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
                                ) - 1 AS "_lookup_rank"
                              FROM (
                                SELECT
                                  "t22"."Id",
                                  "t22"."Participant__c",
                                  "t22"."Survey_Index_Number__c",
                                  "t22"."Completion_Status__c",
                                  "t22"."Consent_Status__c",
                                  "t22"."Completion_Status_Timestamp__c",
                                  "t22"."California_Signature__c",
                                  "t22"."Participant__r.AccountId",
                                  "t22"."Participant__r.Birthdate",
                                  "t22"."Participant__r.Account.Id",
                                  "t22"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                  "t22"."Participant__r.Account.CABOR_Completion_Date__c",
                                  "t22"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                  "t22"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                  "t22"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                  "t22"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                  "t22"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                  "t22"."Participant__r.Account.Basics_Date_Time__c",
                                  "t22"."Participant__r.Account.Overall_Health_Date_Time__c",
                                  "t22"."Participant__r.Account.Lifestyle_Date_Time__c",
                                  "t22"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                  "t22"."Participant__r.Account.HC_Access_Date_Time__c",
                                  "t22"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                  "t22"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                  "t22"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                  "t22"."Participant__r.Account.EH_Date_Time__c",
                                  "t22"."Participant__r.Account.Behavioral_Health_Completion__c",
                                  "t22"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                  "t22"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                  "t22"."FlowDecision_Survey_Completion_Route_target",
                                  "t15"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                                  "t15"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c"
                                FROM (
                                  SELECT
                                    "t20"."Id",
                                    "t20"."Participant__c",
                                    "t20"."Survey_Index_Number__c",
                                    "t20"."Completion_Status__c",
                                    "t20"."Consent_Status__c",
                                    "t20"."Completion_Status_Timestamp__c",
                                    "t20"."California_Signature__c",
                                    "t20"."Participant__r.AccountId",
                                    "t20"."Participant__r.Birthdate",
                                    "t20"."Participant__r.Account.Id",
                                    "t20"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                    "t20"."Participant__r.Account.CABOR_Completion_Date__c",
                                    "t20"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                    "t20"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                    "t20"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                    "t20"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                    "t20"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                    "t20"."Participant__r.Account.Basics_Date_Time__c",
                                    "t20"."Participant__r.Account.Overall_Health_Date_Time__c",
                                    "t20"."Participant__r.Account.Lifestyle_Date_Time__c",
                                    "t20"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                    "t20"."Participant__r.Account.HC_Access_Date_Time__c",
                                    "t20"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                    "t20"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                    "t20"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                    "t20"."Participant__r.Account.EH_Date_Time__c",
                                    "t20"."Participant__r.Account.Behavioral_Health_Completion__c",
                                    "t20"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                    "t20"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                    CASE
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" IN ('1001', '1002')
                                        AND (
                                          "t20"."Consent_Status__c" = 'Yes'
                                        )
                                      )
                                      THEN 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" IN ('1003', '1004')
                                        AND (
                                          "t20"."Consent_Status__c" = 'Yes'
                                        )
                                      )
                                      THEN 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '1005'
                                      )
                                      THEN 'FlowRecordUpdate.Primary_Consent_Update_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        (
                                          "t20"."Survey_Index_Number__c" = '1008'
                                        )
                                        AND "t20"."Consent_Status__c" IN ('Yes', 'N/A')
                                      )
                                      THEN 'FlowRecordLookup.Pediatric_Permission_For_Assent'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND "t20"."Survey_Index_Number__c" IN ('2001', '2002')
                                      THEN 'FlowRecordUpdate.Basics_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND "t20"."Survey_Index_Number__c" IN ('2003', '2004')
                                      THEN 'FlowRecordUpdate.Overall_Health_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2005'
                                      )
                                      THEN 'FlowRecordUpdate.Lifestyle_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2006'
                                      )
                                      THEN 'FlowRecordUpdate.Personal_And_Family_History_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2007'
                                      )
                                      THEN 'FlowRecordUpdate.Healthcare_Access_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2008'
                                      )
                                      THEN 'FlowRecordUpdate.Life_Functioning_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2009'
                                      )
                                      THEN 'FlowRecordLookup.First_Remote_Physical_Measurement'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2010'
                                      )
                                      THEN 'FlowRecordUpdate.Emotional_Health_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2011'
                                      )
                                      THEN 'FlowRecordUpdate.Behavioral_Health_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2012'
                                      )
                                      THEN 'FlowRecordUpdate.Environmental_Exposures_Completion'
                                      WHEN (
                                        "t20"."Completion_Status__c" = 'Complete'
                                      )
                                      AND (
                                        "t20"."Survey_Index_Number__c" = '2013'
                                      )
                                      THEN 'FlowRecordUpdate.Social_Determinants_Completion'
                                      ELSE CAST(NULL AS VARCHAR)
                                    END AS "FlowDecision_Survey_Completion_Route_target"
                                  FROM (
                                    SELECT
                                      "t16"."Id",
                                      "t16"."Participant__c",
                                      "t16"."Survey_Index_Number__c",
                                      "t16"."Completion_Status__c",
                                      "t16"."Consent_Status__c",
                                      "t16"."Completion_Status_Timestamp__c",
                                      "t16"."California_Signature__c",
                                      "t17"."AccountId" AS "Participant__r.AccountId",
                                      "t17"."Birthdate" AS "Participant__r.Birthdate",
                                      "t12"."Id" AS "Participant__r.Account.Id",
                                      "t12"."Age_at_Time_of_Consent__pc" AS "Participant__r.Account.Age_at_Time_of_Consent__pc",
                                      "t12"."CABOR_Completion_Date__c" AS "Participant__r.Account.CABOR_Completion_Date__c",
                                      "t12"."Earliest_Primary_Consent_Date_for_Report__c" AS "Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                      "t12"."Latest_Primary_Consent_Date_for_Report__c" AS "Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                      "t12"."EHR_Consent_Date_Time__c" AS "Participant__r.Account.EHR_Consent_Date_Time__c",
                                      "t12"."EHR_Reconsent_Date_Time__c" AS "Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                      "t12"."Update_to_Primary_Consent_Completed__c" AS "Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                      "t12"."Basics_Date_Time__c" AS "Participant__r.Account.Basics_Date_Time__c",
                                      "t12"."Overall_Health_Date_Time__c" AS "Participant__r.Account.Overall_Health_Date_Time__c",
                                      "t12"."Lifestyle_Date_Time__c" AS "Participant__r.Account.Lifestyle_Date_Time__c",
                                      "t12"."Personal_and_Family_History_Complete__c" AS "Participant__r.Account.Personal_and_Family_History_Complete__c",
                                      "t12"."HC_Access_Date_Time__c" AS "Participant__r.Account.HC_Access_Date_Time__c",
                                      "t12"."Life_Functioning_Date_Time__c" AS "Participant__r.Account.Life_Functioning_Date_Time__c",
                                      "t12"."First_Physical_Measurement_Date_Time__c" AS "Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                      "t12"."Last_Physical_Measurement_Date_Time__c" AS "Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                      "t12"."EH_Date_Time__c" AS "Participant__r.Account.EH_Date_Time__c",
                                      "t12"."Behavioral_Health_Completion__c" AS "Participant__r.Account.Behavioral_Health_Completion__c",
                                      "t12"."Environmental_Exposures_Date_Time__c" AS "Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                      "t12"."Social_Determinants_of_Health_Completion__c" AS "Participant__r.Account.Social_Determinants_of_Health_Completion__c"
                                    FROM (
                                      SELECT
                                        "t1"."Id",
                                        "t1"."Participant__c",
                                        "t1"."Survey_Index_Number__c",
                                        "t1"."Completion_Status__c",
                                        "t1"."Consent_Status__c",
                                        "t1"."Completion_Status_Timestamp__c",
                                        "t1"."California_Signature__c"
                                      FROM "example_survey_result"."history" AS "t1"
                                      WHERE
                                        "t1"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                                        AND (
                                          (
                                            "t1"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                                          )
                                          OR (
                                            "t1"."valid_to" IS NULL
                                          )
                                        )
                                        AND "t1"."Id" = 'EXAMPLE_VERIFIED_SURVEY_EVENT'
                                    ) AS "t16"
                                    LEFT OUTER JOIN (
                                      SELECT
                                        *
                                      FROM "example_contact"."history" AS "t2"
                                      WHERE
                                        "t2"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                                        AND (
                                          (
                                            "t2"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                                          )
                                          OR (
                                            "t2"."valid_to" IS NULL
                                          )
                                        )
                                    ) AS "t17"
                                      ON "t16"."Participant__c" = "t17"."Id"
                                    LEFT OUTER JOIN (
                                      SELECT
                                        *
                                      FROM "example_account"."history" AS "t0"
                                      WHERE
                                        "t0"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
                                        AND (
                                          (
                                            "t0"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
                                          )
                                          OR (
                                            "t0"."valid_to" IS NULL
                                          )
                                        )
                                    ) AS "t12"
                                      ON "t17"."AccountId" = "t12"."Id"
                                  ) AS "t20"
                                ) AS "t22"
                                LEFT OUTER JOIN (
                                  SELECT
                                    "t1"."Id",
                                    "t1"."Participant__c",
                                    "t1"."Consent_Status_Timestamp__c"
                                  FROM "example_survey_result"."history" AS "t1"
                                  WHERE
                                    "t1"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                                    AND (
                                      (
                                        "t1"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                                      )
                                      OR (
                                        "t1"."valid_to" IS NULL
                                      )
                                    )
                                    AND "t1"."Survey_Index_Number__c" IN ('1001', '1002')
                                    AND "t1"."Consent_Status__c" = 'Yes'
                                ) AS "t15"
                                  ON "t22"."Participant__c" = "t15"."Participant__c" AND "t22"."Id" <> "t15"."Id"
                              ) AS "t23"
                            ) AS "t24"
                            WHERE
                              "t24"."_lookup_rank" = 0
                          ) AS "t25"
                        ) AS "t27"
                        LEFT OUTER JOIN (
                          SELECT
                            "t1"."Id",
                            "t1"."Participant__c",
                            "t1"."Consent_Status_Timestamp__c"
                          FROM "example_survey_result"."history" AS "t1"
                          WHERE
                            "t1"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                            AND (
                              (
                                "t1"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                              )
                              OR (
                                "t1"."valid_to" IS NULL
                              )
                            )
                            AND "t1"."Survey_Index_Number__c" IN ('1003', '1004')
                            AND "t1"."Consent_Status__c" = 'Yes'
                        ) AS "t14"
                          ON "t27"."Participant__c" = "t14"."Participant__c" AND "t27"."Id" <> "t14"."Id"
                      ) AS "t28"
                    ) AS "t29"
                    WHERE
                      "t29"."_lookup_rank" = 0
                  ) AS "t30"
                ) AS "t32"
                LEFT OUTER JOIN (
                  SELECT
                    "t1"."Id",
                    "t1"."Participant__c",
                    "t1"."Completion_Status_Timestamp__c"
                  FROM "example_survey_result"."history" AS "t1"
                  WHERE
                    "t1"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                    AND (
                      (
                        "t1"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                      )
                      OR (
                        "t1"."valid_to" IS NULL
                      )
                    )
                    AND "t1"."Survey_Index_Number__c" = '2009'
                ) AS "t13"
                  ON "t32"."Participant__c" = "t13"."Participant__c"
              ) AS "t33"
            ) AS "t34"
            WHERE
              "t34"."_lookup_rank" = 0
          ) AS "t35"
        ) AS "t37"
        LEFT OUTER JOIN (
          SELECT
            "t5"."Participant__c",
            MIN("t5"."Id") AS "Id",
            COUNT(*) AS "match_count",
            CASE
              WHEN COUNT(*) = 1
              THEN MIN("t5"."California_Signature__c")
              ELSE CAST(NULL AS TIMESTAMP)
            END AS "California_Signature__c"
          FROM (
            SELECT
              *
            FROM "example_survey_result"."history" AS "t1"
            WHERE
              "t1"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
              AND (
                (
                  "t1"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
                )
                OR (
                  "t1"."valid_to" IS NULL
                )
              )
              AND "t1"."Survey_Index_Number__c" = '1007'
              AND "t1"."Consent_Status__c" = 'Yes'
          ) AS "t5"
          GROUP BY
            1
        ) AS "t19"
          ON "t37"."Participant__c" = "t19"."Participant__c"
          AND "t37"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
      ) AS "t38"
    ) AS "t39"
  ) AS "t41"
  LEFT OUTER JOIN (
    SELECT
      "t0"."Id",
      "t0"."PersonContactId",
      "t0"."IsPersonAccount",
      "t0"."Age_at_Time_of_Consent__pc",
      "t0"."CABOR_Completion_Date__c",
      "t0"."Earliest_Primary_Consent_Date_for_Report__c",
      "t0"."Latest_Primary_Consent_Date_for_Report__c",
      "t0"."EHR_Consent_Date_Time__c",
      "t0"."EHR_Reconsent_Date_Time__c",
      "t0"."Update_to_Primary_Consent_Completed__c",
      "t0"."Basics_Date_Time__c",
      "t0"."Overall_Health_Date_Time__c",
      "t0"."Lifestyle_Date_Time__c",
      "t0"."Personal_and_Family_History_Complete__c",
      "t0"."HC_Access_Date_Time__c",
      "t0"."Life_Functioning_Date_Time__c",
      "t0"."First_Physical_Measurement_Date_Time__c",
      "t0"."Last_Physical_Measurement_Date_Time__c",
      "t0"."EH_Date_Time__c",
      "t0"."Behavioral_Health_Completion__c",
      "t0"."Environmental_Exposures_Date_Time__c",
      "t0"."Social_Determinants_of_Health_Completion__c",
      "t0"."EHR_Authorized__pc",
      "t0"."Count_of_Completed_EHR_Auth__pc",
      "t0"."Count_of_Completed_Primary_Consent__pc",
      "t0"."Count_of_Completed_Reconsent__pc",
      "t0"."PPI_2_Completion_Count__pc",
      "t0"."PPI_3_Completion_Count__pc",
      "t0"."EHR_Consent_Active__pc",
      "t0"."EHR_Consent_Declined__pc",
      "t0"."PP1_Basics_Survey_Complete__pc",
      "t0"."Re_Consent_Declined__pc",
      "t0"."Re_consent_Active__pc",
      "t0"."Primary_Consent_Declined__pc",
      "t0"."EHR_Consent_Ever__pc",
      "t0"."Assent_Completion_Count__pc",
      "t0"."Pediatric_Permission_Completion_Count__pc",
      "t0"."X0_6_Peds_Permission_Count__pc",
      "t0"."X0_6_Peds_Permission_Declined_Count__pc",
      "t0"."X0_6_Peds_Permission_Revoked_Count__pc",
      "t0"."EHR_Pediatric_Complete__pc",
      "t0"."valid_from",
      "t0"."valid_to",
      "t0"."is_current",
      "t0"."loaded_at",
      'EXAMPLE_VERIFIED_SURVEY_EVENT' AS "survey_result_id"
    FROM "example_account"."history" AS "t0"
    WHERE
      "t0"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:05:00') AS TIMESTAMP)
      AND (
        (
          "t0"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:05:00') AS TIMESTAMP)
        )
        OR (
          "t0"."valid_to" IS NULL
        )
      )
  ) AS "t11"
    ON "t41"."Account.Id" = "t11"."Id" AND "t41"."Record.Id" = "t11"."survey_result_id"
) AS comparison;

-- rollup comparison
SELECT
  *
FROM (
  SELECT
    "t10"."Account.Id" AS "expected_account_id", /* Source identity: Account.Id; source: Account.Id */
    "t10"."PersonContactId" AS "person_contact_id", /* Source identity: PersonContactId; source: Account.PersonContactId */
    "t5"."Id" AS "observed_account_id", /* Source identity: Account.Id; source: Account.Id */
    "t10"."EHR_Authorized__pc" AS "expected__EHR_Authorized__pc", /* Expected Account.EHR_Authorized__pc: Ehr authorized; source: Account.EHR_Authorized__pc */
    "t10"."Count_of_Completed_EHR_Auth__pc" AS "expected__Count_of_Completed_EHR_Auth__pc", /* Expected Account.Count_of_Completed_EHR_Auth__pc: Count of completed ehr auth; source: Account.Count_of_Completed_EHR_Auth__pc */
    "t10"."Count_of_Completed_Primary_Consent__pc" AS "expected__Count_of_Completed_Primary_Consent__pc", /* Expected Account.Count_of_Completed_Primary_Consent__pc: Count of completed primary consent; source: Account.Count_of_Completed_Primary_Consent__pc */
    "t10"."Count_of_Completed_Reconsent__pc" AS "expected__Count_of_Completed_Reconsent__pc", /* Expected Account.Count_of_Completed_Reconsent__pc: Count of completed reconsent; source: Account.Count_of_Completed_Reconsent__pc */
    "t10"."PPI_2_Completion_Count__pc" AS "expected__PPI_2_Completion_Count__pc", /* Expected Account.PPI_2_Completion_Count__pc: Ppi 2 completion count; source: Account.PPI_2_Completion_Count__pc */
    "t10"."PPI_3_Completion_Count__pc" AS "expected__PPI_3_Completion_Count__pc", /* Expected Account.PPI_3_Completion_Count__pc: Ppi 3 completion count; source: Account.PPI_3_Completion_Count__pc */
    "t10"."EHR_Consent_Active__pc" AS "expected__EHR_Consent_Active__pc", /* Expected Account.EHR_Consent_Active__pc: Ehr consent active; source: Account.EHR_Consent_Active__pc */
    "t10"."EHR_Consent_Declined__pc" AS "expected__EHR_Consent_Declined__pc", /* Expected Account.EHR_Consent_Declined__pc: Ehr consent declined; source: Account.EHR_Consent_Declined__pc */
    "t10"."PP1_Basics_Survey_Complete__pc" AS "expected__PP1_Basics_Survey_Complete__pc", /* Expected Account.PP1_Basics_Survey_Complete__pc: Pp1 basics survey complete; source: Account.PP1_Basics_Survey_Complete__pc */
    "t10"."Re_Consent_Declined__pc" AS "expected__Re_Consent_Declined__pc", /* Expected Account.Re_Consent_Declined__pc: Re consent declined; source: Account.Re_Consent_Declined__pc */
    "t10"."Re_consent_Active__pc" AS "expected__Re_consent_Active__pc", /* Expected Account.Re_consent_Active__pc: Re consent active; source: Account.Re_consent_Active__pc */
    "t10"."Primary_Consent_Declined__pc" AS "expected__Primary_Consent_Declined__pc", /* Expected Account.Primary_Consent_Declined__pc: Primary consent declined; source: Account.Primary_Consent_Declined__pc */
    "t10"."EHR_Consent_Ever__pc" AS "expected__EHR_Consent_Ever__pc", /* Expected Account.EHR_Consent_Ever__pc: Ehr consent ever; source: Account.EHR_Consent_Ever__pc */
    "t10"."Assent_Completion_Count__pc" AS "expected__Assent_Completion_Count__pc", /* Expected Account.Assent_Completion_Count__pc: Assent completion count; source: Account.Assent_Completion_Count__pc */
    "t10"."Pediatric_Permission_Completion_Count__pc" AS "expected__Pediatric_Permission_Completion_Count__pc", /* Expected Account.Pediatric_Permission_Completion_Count__pc: Pediatric permission completion count; source: Account.Pediatric_Permission_Completion_Count__pc */
    "t10"."X0_6_Peds_Permission_Count__pc" AS "expected__X0_6_Peds_Permission_Count__pc", /* Expected Account.X0_6_Peds_Permission_Count__pc: X0 6 peds permission count; source: Account.X0_6_Peds_Permission_Count__pc */
    "t10"."X0_6_Peds_Permission_Declined_Count__pc" AS "expected__X0_6_Peds_Permission_Declined_Count__pc", /* Expected Account.X0_6_Peds_Permission_Declined_Count__pc: X0 6 peds permission declined count; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
    "t10"."X0_6_Peds_Permission_Revoked_Count__pc" AS "expected__X0_6_Peds_Permission_Revoked_Count__pc", /* Expected Account.X0_6_Peds_Permission_Revoked_Count__pc: X0 6 peds permission revoked count; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
    "t10"."EHR_Pediatric_Complete__pc" AS "expected__EHR_Pediatric_Complete__pc", /* Expected Account.EHR_Pediatric_Complete__pc: Ehr pediatric complete; source: Account.EHR_Pediatric_Complete__pc */
    "t5"."EHR_Authorized__pc" AS "observed__EHR_Authorized__pc", /* Independently observed Account.EHR_Authorized__pc; source: Account.EHR_Authorized__pc */
    "t5"."Count_of_Completed_EHR_Auth__pc" AS "observed__Count_of_Completed_EHR_Auth__pc", /* Independently observed Account.Count_of_Completed_EHR_Auth__pc; source: Account.Count_of_Completed_EHR_Auth__pc */
    "t5"."Count_of_Completed_Primary_Consent__pc" AS "observed__Count_of_Completed_Primary_Consent__pc", /* Independently observed Account.Count_of_Completed_Primary_Consent__pc; source: Account.Count_of_Completed_Primary_Consent__pc */
    "t5"."Count_of_Completed_Reconsent__pc" AS "observed__Count_of_Completed_Reconsent__pc", /* Independently observed Account.Count_of_Completed_Reconsent__pc; source: Account.Count_of_Completed_Reconsent__pc */
    "t5"."PPI_2_Completion_Count__pc" AS "observed__PPI_2_Completion_Count__pc", /* Independently observed Account.PPI_2_Completion_Count__pc; source: Account.PPI_2_Completion_Count__pc */
    "t5"."PPI_3_Completion_Count__pc" AS "observed__PPI_3_Completion_Count__pc", /* Independently observed Account.PPI_3_Completion_Count__pc; source: Account.PPI_3_Completion_Count__pc */
    "t5"."EHR_Consent_Active__pc" AS "observed__EHR_Consent_Active__pc", /* Independently observed Account.EHR_Consent_Active__pc; source: Account.EHR_Consent_Active__pc */
    "t5"."EHR_Consent_Declined__pc" AS "observed__EHR_Consent_Declined__pc", /* Independently observed Account.EHR_Consent_Declined__pc; source: Account.EHR_Consent_Declined__pc */
    "t5"."PP1_Basics_Survey_Complete__pc" AS "observed__PP1_Basics_Survey_Complete__pc", /* Independently observed Account.PP1_Basics_Survey_Complete__pc; source: Account.PP1_Basics_Survey_Complete__pc */
    "t5"."Re_Consent_Declined__pc" AS "observed__Re_Consent_Declined__pc", /* Independently observed Account.Re_Consent_Declined__pc; source: Account.Re_Consent_Declined__pc */
    "t5"."Re_consent_Active__pc" AS "observed__Re_consent_Active__pc", /* Independently observed Account.Re_consent_Active__pc; source: Account.Re_consent_Active__pc */
    "t5"."Primary_Consent_Declined__pc" AS "observed__Primary_Consent_Declined__pc", /* Independently observed Account.Primary_Consent_Declined__pc; source: Account.Primary_Consent_Declined__pc */
    "t5"."EHR_Consent_Ever__pc" AS "observed__EHR_Consent_Ever__pc", /* Independently observed Account.EHR_Consent_Ever__pc; source: Account.EHR_Consent_Ever__pc */
    "t5"."Assent_Completion_Count__pc" AS "observed__Assent_Completion_Count__pc", /* Independently observed Account.Assent_Completion_Count__pc; source: Account.Assent_Completion_Count__pc */
    "t5"."Pediatric_Permission_Completion_Count__pc" AS "observed__Pediatric_Permission_Completion_Count__pc", /* Independently observed Account.Pediatric_Permission_Completion_Count__pc; source: Account.Pediatric_Permission_Completion_Count__pc */
    "t5"."X0_6_Peds_Permission_Count__pc" AS "observed__X0_6_Peds_Permission_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Count__pc; source: Account.X0_6_Peds_Permission_Count__pc */
    "t5"."X0_6_Peds_Permission_Declined_Count__pc" AS "observed__X0_6_Peds_Permission_Declined_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Declined_Count__pc; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
    "t5"."X0_6_Peds_Permission_Revoked_Count__pc" AS "observed__X0_6_Peds_Permission_Revoked_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Revoked_Count__pc; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
    "t5"."EHR_Pediatric_Complete__pc" AS "observed__EHR_Pediatric_Complete__pc" /* Independently observed Account.EHR_Pediatric_Complete__pc; source: Account.EHR_Pediatric_Complete__pc */
  FROM (
    SELECT
      "t8"."Account.Id",
      "t8"."PersonContactId",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1003'
          )
          THEN 1
          ELSE 0
        END
      ) AS "EHR_Authorized__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1003'
          )
          THEN 1
          ELSE 0
        END
      ) AS "Count_of_Completed_EHR_Auth__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1001'
          )
          THEN 1
          ELSE 0
        END
      ) AS "Count_of_Completed_Primary_Consent__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1005'
          )
          THEN 1
          ELSE 0
        END
      ) AS "Count_of_Completed_Reconsent__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Survey_Index_Number__c" = '2005'
          )
          THEN 1
          ELSE 0
        END
      ) AS "PPI_2_Completion_Count__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Survey_Index_Number__c" = '2003'
          )
          THEN 1
          ELSE 0
        END
      ) AS "PPI_3_Completion_Count__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'Yes'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND "t8"."Survey_Index_Number__c" IN ('1003', '1004')
          THEN 1
          ELSE 0
        END
      ) AS "EHR_Consent_Active__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'No'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND "t8"."Survey_Index_Number__c" IN ('1003', '1004')
          THEN 1
          ELSE 0
        END
      ) AS "EHR_Consent_Declined__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND "t8"."Survey_Index_Number__c" IN ('2001', '2002')
          THEN 1
          ELSE 0
        END
      ) AS "PP1_Basics_Survey_Complete__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'No'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1005'
          )
          THEN 1
          ELSE 0
        END
      ) AS "Re_Consent_Declined__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'Yes'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1005'
          )
          THEN 1
          ELSE 0
        END
      ) AS "Re_consent_Active__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'No'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND "t8"."Survey_Index_Number__c" IN ('1005', '1002')
          THEN 1
          ELSE 0
        END
      ) AS "Primary_Consent_Declined__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'Yes'
          )
          AND "t8"."Survey_Index_Number__c" IN ('1003', '1004')
          THEN 1
          ELSE 0
        END
      ) AS "EHR_Consent_Ever__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'Yes'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1008'
          )
          THEN 1
          ELSE 0
        END
      ) AS "Assent_Completion_Count__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'Yes'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1007'
          )
          THEN 1
          ELSE 0
        END
      ) AS "Pediatric_Permission_Completion_Count__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Consent_Status__c" = 'Yes'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1002'
          )
          THEN 1
          ELSE 0
        END
      ) AS "X0_6_Peds_Permission_Count__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Consent_Status__c" = 'No'
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1002'
          )
          THEN 1
          ELSE 0
        END
      ) AS "X0_6_Peds_Permission_Declined_Count__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Consent_Revoked__c" = TRUE
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1002'
          )
          THEN 1
          ELSE 0
        END
      ) AS "X0_6_Peds_Permission_Revoked_Count__pc",
      SUM(
        CASE
          WHEN (
            "t8"."Completion_Status__c" = 'Complete'
          )
          AND (
            "t8"."Consent_Status__c" = 'Yes'
          )
          AND (
            "t8"."Consent_Revoked__c" = FALSE
          )
          AND (
            "t8"."Survey_Index_Number__c" = '1004'
          )
          THEN 1
          ELSE 0
        END
      ) AS "EHR_Pediatric_Complete__pc"
    FROM (
      SELECT
        "t6"."Id" AS "Account.Id",
        "t6"."PersonContactId",
        "t7"."Completion_Status__c",
        "t7"."Survey_Index_Number__c",
        "t7"."Consent_Status__c",
        "t7"."Consent_Revoked__c"
      FROM (
        SELECT
          "t0"."Id",
          "t0"."PersonContactId"
        FROM "example_account"."history" AS "t0"
        WHERE
          "t0"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
          AND (
            (
              "t0"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
            )
            OR (
              "t0"."valid_to" IS NULL
            )
          )
          AND "t0"."IsPersonAccount"
      ) AS "t6"
      LEFT OUTER JOIN (
        SELECT
          "t1"."Participant__c",
          "t1"."Completion_Status__c",
          "t1"."Survey_Index_Number__c",
          "t1"."Consent_Status__c",
          "t1"."Consent_Revoked__c"
        FROM "example_survey_result"."history" AS "t1"
        WHERE
          "t1"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
          AND (
            (
              "t1"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
            )
            OR (
              "t1"."valid_to" IS NULL
            )
          )
      ) AS "t7"
        ON "t6"."PersonContactId" = "t7"."Participant__c"
    ) AS "t8"
    GROUP BY
      1,
      2
  ) AS "t10"
  LEFT OUTER JOIN (
    SELECT
      *
    FROM "example_account"."history" AS "t0"
    WHERE
      "t0"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
      AND (
        (
          "t0"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T12:00:00') AS TIMESTAMP)
        )
        OR (
          "t0"."valid_to" IS NULL
        )
      )
  ) AS "t5"
    ON "t10"."Account.Id" = "t5"."Id"
) AS comparison;
