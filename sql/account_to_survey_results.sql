-- ILLUSTRATIVE bindings/event/times; source profiles are defined in schemas/.
-- Direct SELECTs over history. Verify physical catalog types before execution.
-- Execution: 2026-10-21 12:00; BEFORE: 11:59:59; settled AFTER: 12:05.

SELECT
  "t37"."Id" AS "Record.Id", /* Source identity: Record.Id; source: Survey_Result__c.Id */
  "t37"."Participant__r.Account.Id" AS "Account.Id", /* Source identity: Account.Id; source: Account.Id */
  "t37"."Participant__c", /* Source identity: Participant__c; source: Survey_Result__c.Participant__c */
  "t37"."Survey_Index_Number__c", /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */
  "t37"."Completion_Status_Timestamp__c", /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
  "t37"."FlowDecision_Survey_Completion_Route_target", /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */
  "t37"."FlowDecision_Primary_Consent_Account_Update_target", /* Translated FlowDecision.Primary_Consent_Account_Update; source: FlowDecision.Previous_Primary_Consent_Exists */
  "t37"."FlowDecision_EHR_Consent_Account_Update_target", /* Translated FlowDecision.EHR_Consent_Account_Update; source: FlowDecision.Previous_EHR_Exists */
  "t37"."FlowDecision_Assent_Account_Update_target", /* Translated FlowDecision.Assent_Account_Update; source: FlowDecision.Decision_4 */
  "t37"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count", /* Number of candidate pediatric permissions; source: FlowRecordLookup.Get_Permission_1007 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" IN (
      'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent',
      'FlowRecordLookup.Pediatric_Permission_For_Assent'
    )
    THEN "t37"."FlowFormula_Age_At_Execution"
    ELSE "t37"."Participant__r.Account.Age_at_Time_of_Consent__pc"
  END AS "Age_at_Time_of_Consent__pc", /* Age at flow execution; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowFormula.formAgeCalculation */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
    THEN "t37"."California_Signature__c"
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
    THEN "t37"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
    ELSE "t37"."Participant__r.Account.CABOR_Completion_Date__c"
  END AS "CABOR_Completion_Date__c", /* California signature timestamp; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative, FlowRecordLookup.Get_Permission_1007 */
  CASE
    WHEN (
      "t37"."FlowDecision_Primary_Consent_Account_Update_target" /* Translated FlowDecision.Primary_Consent_Account_Update; source: FlowDecision.Previous_Primary_Consent_Exists */ = 'FlowRecordUpdate.Primary_Consent_With_Prior_Yes'
    )
    OR (
      "t37"."FlowDecision_Assent_Account_Update_target" /* Translated FlowDecision.Assent_Account_Update; source: FlowDecision.Decision_4 */ = 'FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date'
    )
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c"
  END AS "Earliest_Primary_Consent_Date_for_Report__c", /* Earliest primary consent report timestamp; source: FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Negative */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" IN (
      'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent',
      'FlowRecordLookup.Pediatric_Permission_For_Assent'
    )
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c"
  END AS "Latest_Primary_Consent_Date_for_Report__c", /* Latest primary consent report timestamp; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative */
  CASE
    WHEN "t37"."FlowDecision_EHR_Consent_Account_Update_target" /* Translated FlowDecision.EHR_Consent_Account_Update; source: FlowDecision.Previous_EHR_Exists */ = 'FlowRecordUpdate.EHR_Consent_With_Prior_Yes'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.EHR_Consent_Date_Time__c"
  END AS "EHR_Consent_Date_Time__c", /* Ehr consent timestamp; source: FlowRecordUpdate.updateAccount1003_NegativeSF */
  CASE
    WHEN "t37"."FlowDecision_EHR_Consent_Account_Update_target" /* Translated FlowDecision.EHR_Consent_Account_Update; source: FlowDecision.Previous_EHR_Exists */ = 'FlowRecordUpdate.EHR_Consent_Without_Prior_Yes'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.EHR_Reconsent_Date_Time__c"
  END AS "EHR_Reconsent_Date_Time__c", /* Ehr reconsent timestamp; source: FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Primary_Consent_Update_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Update_to_Primary_Consent_Completed__c"
  END AS "Update_to_Primary_Consent_Completed__c", /* Primary consent update timestamp; source: FlowRecordUpdate.updateAccount1005 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Basics_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Basics_Date_Time__c"
  END AS "Basics_Date_Time__c", /* Basics completion timestamp; source: FlowRecordUpdate.updateAccount2001 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Overall_Health_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Overall_Health_Date_Time__c"
  END AS "Overall_Health_Date_Time__c", /* Overall health completion timestamp; source: FlowRecordUpdate.updateAccount2003 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Lifestyle_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Lifestyle_Date_Time__c"
  END AS "Lifestyle_Date_Time__c", /* Lifestyle completion timestamp; source: FlowRecordUpdate.updateAccount2005 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Personal_And_Family_History_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Personal_and_Family_History_Complete__c"
  END AS "Personal_and_Family_History_Complete__c", /* Personal and family history completion timestamp; source: FlowRecordUpdate.updateAccount2006 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Healthcare_Access_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.HC_Access_Date_Time__c"
  END AS "HC_Access_Date_Time__c", /* Healthcare access completion timestamp; source: FlowRecordUpdate.updateAccount2007 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Life_Functioning_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Life_Functioning_Date_Time__c"
  END AS "Life_Functioning_Date_Time__c", /* Life functioning completion timestamp; source: FlowRecordUpdate.updateAccount2008 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordLookup.First_Remote_Physical_Measurement'
    THEN "t37"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
    ELSE "t37"."Participant__r.Account.First_Physical_Measurement_Date_Time__c"
  END AS "First_Physical_Measurement_Date_Time__c", /* First remote physical measurement timestamp; source: FlowRecordUpdate.updateAccount2009, FlowRecordLookup.getFirstPhysicalMeasurement */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordLookup.First_Remote_Physical_Measurement'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c"
  END AS "Last_Physical_Measurement_Date_Time__c", /* Latest processed remote physical measurement timestamp; source: FlowRecordUpdate.updateAccount2009 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Emotional_Health_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.EH_Date_Time__c"
  END AS "EH_Date_Time__c", /* Emotional health completion timestamp; source: FlowRecordUpdate.updateAccount2010 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Behavioral_Health_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Behavioral_Health_Completion__c"
  END AS "Behavioral_Health_Completion__c", /* Behavioral health completion timestamp; source: FlowRecordUpdate.updateAccount2011 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Environmental_Exposures_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Environmental_Exposures_Date_Time__c"
  END AS "Environmental_Exposures_Date_Time__c", /* Environmental exposures completion timestamp; source: FlowRecordUpdate.updateAccount2012 */
  CASE
    WHEN "t37"."FlowDecision_Survey_Completion_Route_target" /* Translated FlowDecision.Survey_Completion_Route; source: FlowDecision.Survey_Index, FlowStart.start */ = 'FlowRecordUpdate.Social_Determinants_Completion'
    THEN "t37"."Completion_Status_Timestamp__c" /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
    ELSE "t37"."Participant__r.Account.Social_Determinants_of_Health_Completion__c"
  END AS "Social_Determinants_of_Health_Completion__c", /* Social determinants completion timestamp; source: FlowRecordUpdate.updateAccount2013 */
  NOT (
    COALESCE(
      "t37"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent',
      FALSE
    )
  )
  OR (
    "t37"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count" /* Number of candidate pediatric permissions; source: FlowRecordLookup.Get_Permission_1007 */ <= 1
  ) AS "CABOR_Completion_Date__c_is_deterministic" /* Signature lookup has at most one candidate on the assent route; source: FlowRecordLookup.Get_Permission_1007 */
FROM (
  SELECT
    "t36"."Id",
    "t36"."Participant__c",
    "t36"."Survey_Index_Number__c",
    "t36"."Completion_Status__c",
    "t36"."Consent_Status__c",
    "t36"."Completion_Status_Timestamp__c",
    "t36"."California_Signature__c",
    "t36"."Participant__r.AccountId",
    "t36"."Participant__r.Birthdate",
    "t36"."Participant__r.Account.Id",
    "t36"."Participant__r.Account.Age_at_Time_of_Consent__pc",
    "t36"."Participant__r.Account.CABOR_Completion_Date__c",
    "t36"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
    "t36"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
    "t36"."Participant__r.Account.EHR_Consent_Date_Time__c",
    "t36"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
    "t36"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
    "t36"."Participant__r.Account.Basics_Date_Time__c",
    "t36"."Participant__r.Account.Overall_Health_Date_Time__c",
    "t36"."Participant__r.Account.Lifestyle_Date_Time__c",
    "t36"."Participant__r.Account.Personal_and_Family_History_Complete__c",
    "t36"."Participant__r.Account.HC_Access_Date_Time__c",
    "t36"."Participant__r.Account.Life_Functioning_Date_Time__c",
    "t36"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
    "t36"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
    "t36"."Participant__r.Account.EH_Date_Time__c",
    "t36"."Participant__r.Account.Behavioral_Health_Completion__c",
    "t36"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
    "t36"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
    "t36"."FlowDecision_Survey_Completion_Route_target",
    "t36"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
    "t36"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
    "t36"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
    "t36"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
    "t36"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
    "t36"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
    "t36"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
    "t36"."FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
    "t36"."FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c",
    CASE
      WHEN (
        "t36"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
      )
      AND (
        "t36"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NULL
      )
      THEN 'FlowRecordUpdate.Primary_Consent_Without_Prior_Yes'
      WHEN (
        "t36"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
      )
      AND NOT (
        "t36"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id" IS NULL
      )
      THEN 'FlowRecordUpdate.Primary_Consent_With_Prior_Yes'
      ELSE CAST(NULL AS VARCHAR)
    END AS "FlowDecision_Primary_Consent_Account_Update_target",
    CASE
      WHEN (
        "t36"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
      )
      AND (
        "t36"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NULL
      )
      THEN 'FlowRecordUpdate.EHR_Consent_Without_Prior_Yes'
      WHEN (
        "t36"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
      )
      AND NOT (
        "t36"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id" IS NULL
      )
      THEN 'FlowRecordUpdate.EHR_Consent_With_Prior_Yes'
      ELSE CAST(NULL AS VARCHAR)
    END AS "FlowDecision_EHR_Consent_Account_Update_target",
    CASE
      WHEN (
        "t36"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
      )
      AND (
        (
          "t36"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NULL
        )
        AND (
          "t36"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NULL
        )
      )
      THEN 'FlowRecordUpdate.Assent_No_Permission_And_No_Primary_Date'
      WHEN (
        "t36"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
      )
      AND NOT (
        (
          "t36"."FlowRecordLookup.Pediatric_Permission_For_Assent.Id" IS NULL
        )
        AND (
          "t36"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c" IS NULL
        )
      )
      THEN 'FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date'
      ELSE CAST(NULL AS VARCHAR)
    END AS "FlowDecision_Assent_Account_Update_target",
    CAST(FLOOR(
      DATE_DIFF(
        'DAY',
        DATE_TRUNC('DAY', "t36"."Participant__r.Birthdate"),
        DATE_TRUNC('DAY', FROM_ISO8601_DATE('2026-10-21'))
      ) / CAST(365.25 AS DOUBLE)
    ) AS BIGINT) AS "FlowFormula_Age_At_Execution"
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
      "t35"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
      "t17"."Id" AS "FlowRecordLookup.Pediatric_Permission_For_Assent.Id",
      COALESCE("t17"."match_count", 0) AS "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
      "t17"."California_Signature__c" AS "FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
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
        "t33"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
      FROM (
        SELECT
          *
        FROM (
          SELECT
            "t31"."Id",
            "t31"."Participant__c",
            "t31"."Survey_Index_Number__c",
            "t31"."Completion_Status__c",
            "t31"."Consent_Status__c",
            "t31"."Completion_Status_Timestamp__c",
            "t31"."California_Signature__c",
            "t31"."Participant__r.AccountId",
            "t31"."Participant__r.Birthdate",
            "t31"."Participant__r.Account.Id",
            "t31"."Participant__r.Account.Age_at_Time_of_Consent__pc",
            "t31"."Participant__r.Account.CABOR_Completion_Date__c",
            "t31"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
            "t31"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
            "t31"."Participant__r.Account.EHR_Consent_Date_Time__c",
            "t31"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
            "t31"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
            "t31"."Participant__r.Account.Basics_Date_Time__c",
            "t31"."Participant__r.Account.Overall_Health_Date_Time__c",
            "t31"."Participant__r.Account.Lifestyle_Date_Time__c",
            "t31"."Participant__r.Account.Personal_and_Family_History_Complete__c",
            "t31"."Participant__r.Account.HC_Access_Date_Time__c",
            "t31"."Participant__r.Account.Life_Functioning_Date_Time__c",
            "t31"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
            "t31"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
            "t31"."Participant__r.Account.EH_Date_Time__c",
            "t31"."Participant__r.Account.Behavioral_Health_Completion__c",
            "t31"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
            "t31"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
            "t31"."FlowDecision_Survey_Completion_Route_target",
            "t31"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
            "t31"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
            "t31"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
            "t31"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
            "t31"."FlowRecordLookup.First_Remote_Physical_Measurement.Id",
            "t31"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c",
            ROW_NUMBER() OVER (
              PARTITION BY "t31"."Id"
              ORDER BY "t31"."FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c" ASC NULLS FIRST
            ) - 1 AS "_lookup_rank"
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
              "t30"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
              "t10"."Id" AS "FlowRecordLookup.First_Remote_Physical_Measurement.Id",
              "t10"."Completion_Status_Timestamp__c" AS "FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
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
                "t28"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c"
              FROM (
                SELECT
                  *
                FROM (
                  SELECT
                    "t26"."Id",
                    "t26"."Participant__c",
                    "t26"."Survey_Index_Number__c",
                    "t26"."Completion_Status__c",
                    "t26"."Consent_Status__c",
                    "t26"."Completion_Status_Timestamp__c",
                    "t26"."California_Signature__c",
                    "t26"."Participant__r.AccountId",
                    "t26"."Participant__r.Birthdate",
                    "t26"."Participant__r.Account.Id",
                    "t26"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                    "t26"."Participant__r.Account.CABOR_Completion_Date__c",
                    "t26"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                    "t26"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                    "t26"."Participant__r.Account.EHR_Consent_Date_Time__c",
                    "t26"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                    "t26"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                    "t26"."Participant__r.Account.Basics_Date_Time__c",
                    "t26"."Participant__r.Account.Overall_Health_Date_Time__c",
                    "t26"."Participant__r.Account.Lifestyle_Date_Time__c",
                    "t26"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                    "t26"."Participant__r.Account.HC_Access_Date_Time__c",
                    "t26"."Participant__r.Account.Life_Functioning_Date_Time__c",
                    "t26"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                    "t26"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                    "t26"."Participant__r.Account.EH_Date_Time__c",
                    "t26"."Participant__r.Account.Behavioral_Health_Completion__c",
                    "t26"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                    "t26"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                    "t26"."FlowDecision_Survey_Completion_Route_target",
                    "t26"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                    "t26"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                    "t26"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                    "t26"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c",
                    ROW_NUMBER() OVER (
                      PARTITION BY "t26"."Id"
                      ORDER BY "t26"."FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
                    ) - 1 AS "_lookup_rank"
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
                      "t25"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                      "t11"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id",
                      "t11"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Consent_Status_Timestamp__c"
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
                        "t23"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c"
                      FROM (
                        SELECT
                          *
                        FROM (
                          SELECT
                            "t21"."Id",
                            "t21"."Participant__c",
                            "t21"."Survey_Index_Number__c",
                            "t21"."Completion_Status__c",
                            "t21"."Consent_Status__c",
                            "t21"."Completion_Status_Timestamp__c",
                            "t21"."California_Signature__c",
                            "t21"."Participant__r.AccountId",
                            "t21"."Participant__r.Birthdate",
                            "t21"."Participant__r.Account.Id",
                            "t21"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                            "t21"."Participant__r.Account.CABOR_Completion_Date__c",
                            "t21"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                            "t21"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                            "t21"."Participant__r.Account.EHR_Consent_Date_Time__c",
                            "t21"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                            "t21"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                            "t21"."Participant__r.Account.Basics_Date_Time__c",
                            "t21"."Participant__r.Account.Overall_Health_Date_Time__c",
                            "t21"."Participant__r.Account.Lifestyle_Date_Time__c",
                            "t21"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                            "t21"."Participant__r.Account.HC_Access_Date_Time__c",
                            "t21"."Participant__r.Account.Life_Functioning_Date_Time__c",
                            "t21"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                            "t21"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                            "t21"."Participant__r.Account.EH_Date_Time__c",
                            "t21"."Participant__r.Account.Behavioral_Health_Completion__c",
                            "t21"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                            "t21"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                            "t21"."FlowDecision_Survey_Completion_Route_target",
                            "t21"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                            "t21"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c",
                            ROW_NUMBER() OVER (
                              PARTITION BY "t21"."Id"
                              ORDER BY "t21"."FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c" ASC NULLS FIRST
                            ) - 1 AS "_lookup_rank"
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
                              "t20"."FlowDecision_Survey_Completion_Route_target",
                              "t12"."Id" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id",
                              "t12"."Consent_Status_Timestamp__c" AS "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Consent_Status_Timestamp__c"
                            FROM (
                              SELECT
                                "t18"."Id",
                                "t18"."Participant__c",
                                "t18"."Survey_Index_Number__c",
                                "t18"."Completion_Status__c",
                                "t18"."Consent_Status__c",
                                "t18"."Completion_Status_Timestamp__c",
                                "t18"."California_Signature__c",
                                "t18"."Participant__r.AccountId",
                                "t18"."Participant__r.Birthdate",
                                "t18"."Participant__r.Account.Id",
                                "t18"."Participant__r.Account.Age_at_Time_of_Consent__pc",
                                "t18"."Participant__r.Account.CABOR_Completion_Date__c",
                                "t18"."Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                "t18"."Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                "t18"."Participant__r.Account.EHR_Consent_Date_Time__c",
                                "t18"."Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                "t18"."Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                "t18"."Participant__r.Account.Basics_Date_Time__c",
                                "t18"."Participant__r.Account.Overall_Health_Date_Time__c",
                                "t18"."Participant__r.Account.Lifestyle_Date_Time__c",
                                "t18"."Participant__r.Account.Personal_and_Family_History_Complete__c",
                                "t18"."Participant__r.Account.HC_Access_Date_Time__c",
                                "t18"."Participant__r.Account.Life_Functioning_Date_Time__c",
                                "t18"."Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                "t18"."Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                "t18"."Participant__r.Account.EH_Date_Time__c",
                                "t18"."Participant__r.Account.Behavioral_Health_Completion__c",
                                "t18"."Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                "t18"."Participant__r.Account.Social_Determinants_of_Health_Completion__c",
                                CASE
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" IN ('1001', '1002')
                                    AND (
                                      "t18"."Consent_Status__c" = 'Yes'
                                    )
                                  )
                                  THEN 'FlowRecordLookup.Earliest_Other_Yes_Primary_Consent'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" IN ('1003', '1004')
                                    AND (
                                      "t18"."Consent_Status__c" = 'Yes'
                                    )
                                  )
                                  THEN 'FlowRecordLookup.Earliest_Other_Yes_EHR_Consent'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '1005'
                                  )
                                  THEN 'FlowRecordUpdate.Primary_Consent_Update_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    (
                                      "t18"."Survey_Index_Number__c" = '1008'
                                    )
                                    AND "t18"."Consent_Status__c" IN ('Yes', 'N/A')
                                  )
                                  THEN 'FlowRecordLookup.Pediatric_Permission_For_Assent'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND "t18"."Survey_Index_Number__c" IN ('2001', '2002')
                                  THEN 'FlowRecordUpdate.Basics_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND "t18"."Survey_Index_Number__c" IN ('2003', '2004')
                                  THEN 'FlowRecordUpdate.Overall_Health_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2005'
                                  )
                                  THEN 'FlowRecordUpdate.Lifestyle_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2006'
                                  )
                                  THEN 'FlowRecordUpdate.Personal_And_Family_History_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2007'
                                  )
                                  THEN 'FlowRecordUpdate.Healthcare_Access_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2008'
                                  )
                                  THEN 'FlowRecordUpdate.Life_Functioning_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2009'
                                  )
                                  THEN 'FlowRecordLookup.First_Remote_Physical_Measurement'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2010'
                                  )
                                  THEN 'FlowRecordUpdate.Emotional_Health_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2011'
                                  )
                                  THEN 'FlowRecordUpdate.Behavioral_Health_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2012'
                                  )
                                  THEN 'FlowRecordUpdate.Environmental_Exposures_Completion'
                                  WHEN (
                                    "t18"."Completion_Status__c" = 'Complete'
                                  )
                                  AND (
                                    "t18"."Survey_Index_Number__c" = '2013'
                                  )
                                  THEN 'FlowRecordUpdate.Social_Determinants_Completion'
                                  ELSE CAST(NULL AS VARCHAR)
                                END AS "FlowDecision_Survey_Completion_Route_target"
                              FROM (
                                SELECT
                                  "t13"."Id",
                                  "t13"."Participant__c",
                                  "t13"."Survey_Index_Number__c",
                                  "t13"."Completion_Status__c",
                                  "t13"."Consent_Status__c",
                                  "t13"."Completion_Status_Timestamp__c",
                                  "t13"."California_Signature__c",
                                  "t14"."AccountId" AS "Participant__r.AccountId",
                                  "t14"."Birthdate" AS "Participant__r.Birthdate",
                                  "t15"."Id" AS "Participant__r.Account.Id",
                                  "t15"."Age_at_Time_of_Consent__pc" AS "Participant__r.Account.Age_at_Time_of_Consent__pc",
                                  "t15"."CABOR_Completion_Date__c" AS "Participant__r.Account.CABOR_Completion_Date__c",
                                  "t15"."Earliest_Primary_Consent_Date_for_Report__c" AS "Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c",
                                  "t15"."Latest_Primary_Consent_Date_for_Report__c" AS "Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c",
                                  "t15"."EHR_Consent_Date_Time__c" AS "Participant__r.Account.EHR_Consent_Date_Time__c",
                                  "t15"."EHR_Reconsent_Date_Time__c" AS "Participant__r.Account.EHR_Reconsent_Date_Time__c",
                                  "t15"."Update_to_Primary_Consent_Completed__c" AS "Participant__r.Account.Update_to_Primary_Consent_Completed__c",
                                  "t15"."Basics_Date_Time__c" AS "Participant__r.Account.Basics_Date_Time__c",
                                  "t15"."Overall_Health_Date_Time__c" AS "Participant__r.Account.Overall_Health_Date_Time__c",
                                  "t15"."Lifestyle_Date_Time__c" AS "Participant__r.Account.Lifestyle_Date_Time__c",
                                  "t15"."Personal_and_Family_History_Complete__c" AS "Participant__r.Account.Personal_and_Family_History_Complete__c",
                                  "t15"."HC_Access_Date_Time__c" AS "Participant__r.Account.HC_Access_Date_Time__c",
                                  "t15"."Life_Functioning_Date_Time__c" AS "Participant__r.Account.Life_Functioning_Date_Time__c",
                                  "t15"."First_Physical_Measurement_Date_Time__c" AS "Participant__r.Account.First_Physical_Measurement_Date_Time__c",
                                  "t15"."Last_Physical_Measurement_Date_Time__c" AS "Participant__r.Account.Last_Physical_Measurement_Date_Time__c",
                                  "t15"."EH_Date_Time__c" AS "Participant__r.Account.EH_Date_Time__c",
                                  "t15"."Behavioral_Health_Completion__c" AS "Participant__r.Account.Behavioral_Health_Completion__c",
                                  "t15"."Environmental_Exposures_Date_Time__c" AS "Participant__r.Account.Environmental_Exposures_Date_Time__c",
                                  "t15"."Social_Determinants_of_Health_Completion__c" AS "Participant__r.Account.Social_Determinants_of_Health_Completion__c"
                                FROM (
                                  SELECT
                                    "t0"."Id",
                                    "t0"."Participant__c",
                                    "t0"."Survey_Index_Number__c",
                                    "t0"."Completion_Status__c",
                                    "t0"."Consent_Status__c",
                                    "t0"."Completion_Status_Timestamp__c",
                                    "t0"."California_Signature__c"
                                  FROM "example_survey_result"."history" AS "t0"
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
                                    AND "t0"."Id" = 'EXAMPLE_VERIFIED_SURVEY_EVENT'
                                ) AS "t13"
                                LEFT OUTER JOIN (
                                  SELECT
                                    *
                                  FROM "example_contact"."history" AS "t1"
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
                                ) AS "t14"
                                  ON "t13"."Participant__c" = "t14"."Id"
                                LEFT OUTER JOIN (
                                  SELECT
                                    *
                                  FROM "example_account"."history" AS "t2"
                                  WHERE
                                    "t2"."valid_from" <= CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
                                    AND (
                                      (
                                        "t2"."valid_to" > CAST(FROM_ISO8601_TIMESTAMP('2026-10-21T11:59:59') AS TIMESTAMP)
                                      )
                                      OR (
                                        "t2"."valid_to" IS NULL
                                      )
                                    )
                                ) AS "t15"
                                  ON "t14"."AccountId" = "t15"."Id"
                              ) AS "t18"
                            ) AS "t20"
                            LEFT OUTER JOIN (
                              SELECT
                                "t0"."Id",
                                "t0"."Participant__c",
                                "t0"."Consent_Status_Timestamp__c"
                              FROM "example_survey_result"."history" AS "t0"
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
                                AND "t0"."Survey_Index_Number__c" IN ('1001', '1002')
                                AND "t0"."Consent_Status__c" = 'Yes'
                            ) AS "t12"
                              ON "t20"."Participant__c" = "t12"."Participant__c" AND "t20"."Id" <> "t12"."Id"
                          ) AS "t21"
                        ) AS "t22"
                        WHERE
                          "t22"."_lookup_rank" = 0
                      ) AS "t23"
                    ) AS "t25"
                    LEFT OUTER JOIN (
                      SELECT
                        "t0"."Id",
                        "t0"."Participant__c",
                        "t0"."Consent_Status_Timestamp__c"
                      FROM "example_survey_result"."history" AS "t0"
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
                        AND "t0"."Survey_Index_Number__c" IN ('1003', '1004')
                        AND "t0"."Consent_Status__c" = 'Yes'
                    ) AS "t11"
                      ON "t25"."Participant__c" = "t11"."Participant__c" AND "t25"."Id" <> "t11"."Id"
                  ) AS "t26"
                ) AS "t27"
                WHERE
                  "t27"."_lookup_rank" = 0
              ) AS "t28"
            ) AS "t30"
            LEFT OUTER JOIN (
              SELECT
                "t0"."Id",
                "t0"."Participant__c",
                "t0"."Completion_Status_Timestamp__c"
              FROM "example_survey_result"."history" AS "t0"
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
                AND "t0"."Survey_Index_Number__c" = '2009'
            ) AS "t10"
              ON "t30"."Participant__c" = "t10"."Participant__c"
          ) AS "t31"
        ) AS "t32"
        WHERE
          "t32"."_lookup_rank" = 0
      ) AS "t33"
    ) AS "t35"
    LEFT OUTER JOIN (
      SELECT
        "t3"."Participant__c",
        MIN("t3"."Id") AS "Id",
        COUNT(*) AS "match_count",
        CASE
          WHEN COUNT(*) = 1
          THEN MIN("t3"."California_Signature__c")
          ELSE CAST(NULL AS TIMESTAMP)
        END AS "California_Signature__c"
      FROM (
        SELECT
          *
        FROM "example_survey_result"."history" AS "t0"
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
          AND "t0"."Survey_Index_Number__c" = '1007'
          AND "t0"."Consent_Status__c" = 'Yes'
      ) AS "t3"
      GROUP BY
        1
    ) AS "t17"
      ON "t35"."Participant__c" = "t17"."Participant__c"
      AND "t35"."FlowDecision_Survey_Completion_Route_target" = 'FlowRecordLookup.Pediatric_Permission_For_Assent'
  ) AS "t36"
) AS "t37";

SELECT
  "t6"."Account.Id", /* Source identity: Account.Id; source: Account.Id */
  "t6"."PersonContactId", /* Source identity: PersonContactId; source: Account.PersonContactId */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1003'
      )
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Authorized__pc", /* Ehr authorized; source: Account.EHR_Authorized__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1003'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Count_of_Completed_EHR_Auth__pc", /* Count of completed ehr auth; source: Account.Count_of_Completed_EHR_Auth__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1001'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Count_of_Completed_Primary_Consent__pc", /* Count of completed primary consent; source: Account.Count_of_Completed_Primary_Consent__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1005'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Count_of_Completed_Reconsent__pc", /* Count of completed reconsent; source: Account.Count_of_Completed_Reconsent__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Survey_Index_Number__c" = '2005'
      )
      THEN 1
      ELSE 0
    END
  ) AS "PPI_2_Completion_Count__pc", /* Ppi 2 completion count; source: Account.PPI_2_Completion_Count__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Survey_Index_Number__c" = '2003'
      )
      THEN 1
      ELSE 0
    END
  ) AS "PPI_3_Completion_Count__pc", /* Ppi 3 completion count; source: Account.PPI_3_Completion_Count__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'Yes'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND "t6"."Survey_Index_Number__c" IN ('1003', '1004')
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Consent_Active__pc", /* Ehr consent active; source: Account.EHR_Consent_Active__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'No'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND "t6"."Survey_Index_Number__c" IN ('1003', '1004')
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Consent_Declined__pc", /* Ehr consent declined; source: Account.EHR_Consent_Declined__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND "t6"."Survey_Index_Number__c" IN ('2001', '2002')
      THEN 1
      ELSE 0
    END
  ) AS "PP1_Basics_Survey_Complete__pc", /* Pp1 basics survey complete; source: Account.PP1_Basics_Survey_Complete__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'No'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1005'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Re_Consent_Declined__pc", /* Re consent declined; source: Account.Re_Consent_Declined__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'Yes'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1005'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Re_consent_Active__pc", /* Re consent active; source: Account.Re_consent_Active__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'No'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND "t6"."Survey_Index_Number__c" IN ('1005', '1002')
      THEN 1
      ELSE 0
    END
  ) AS "Primary_Consent_Declined__pc", /* Primary consent declined; source: Account.Primary_Consent_Declined__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'Yes'
      )
      AND "t6"."Survey_Index_Number__c" IN ('1003', '1004')
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Consent_Ever__pc", /* Ehr consent ever; source: Account.EHR_Consent_Ever__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'Yes'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1008'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Assent_Completion_Count__pc", /* Assent completion count; source: Account.Assent_Completion_Count__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'Yes'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1007'
      )
      THEN 1
      ELSE 0
    END
  ) AS "Pediatric_Permission_Completion_Count__pc", /* Pediatric permission completion count; source: Account.Pediatric_Permission_Completion_Count__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Consent_Status__c" = 'Yes'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1002'
      )
      THEN 1
      ELSE 0
    END
  ) AS "X0_6_Peds_Permission_Count__pc", /* X0 6 peds permission count; source: Account.X0_6_Peds_Permission_Count__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Consent_Status__c" = 'No'
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1002'
      )
      THEN 1
      ELSE 0
    END
  ) AS "X0_6_Peds_Permission_Declined_Count__pc", /* X0 6 peds permission declined count; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Consent_Revoked__c" = TRUE
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1002'
      )
      THEN 1
      ELSE 0
    END
  ) AS "X0_6_Peds_Permission_Revoked_Count__pc", /* X0 6 peds permission revoked count; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
  SUM(
    CASE
      WHEN (
        "t6"."Completion_Status__c" = 'Complete'
      )
      AND (
        "t6"."Consent_Status__c" = 'Yes'
      )
      AND (
        "t6"."Consent_Revoked__c" = FALSE
      )
      AND (
        "t6"."Survey_Index_Number__c" = '1004'
      )
      THEN 1
      ELSE 0
    END
  ) AS "EHR_Pediatric_Complete__pc" /* Ehr pediatric complete; source: Account.EHR_Pediatric_Complete__pc */
FROM (
  SELECT
    "t4"."Id" AS "Account.Id",
    "t4"."PersonContactId",
    "t5"."Completion_Status__c",
    "t5"."Survey_Index_Number__c",
    "t5"."Consent_Status__c",
    "t5"."Consent_Revoked__c"
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
  ) AS "t4"
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
  ) AS "t5"
    ON "t4"."PersonContactId" = "t5"."Participant__c"
) AS "t6"
GROUP BY
  1,
  2;
