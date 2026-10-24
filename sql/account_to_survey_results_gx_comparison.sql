-- ILLUSTRATIVE bindings/event/times; source profiles are defined in core/schemas/.
-- Direct SELECTs over history. Verify physical catalog types before execution.
-- Execution: 2026-10-21 12:00; BEFORE: 11:59:59; settled AFTER: 12:05.

-- flow
SELECT
  "Flow_Context"."Id" AS "survey_result_id", /* Source identity: Record.Id; source: Survey_Result__c.Id */
  "Flow_Context"."Participant__c" AS "participant_contact_id", /* Source identity: Participant__c; source: Survey_Result__c.Participant__c */
  "Flow_Context"."Participant__r.Account.Id" AS "expected_account_id", /* Source identity: Account.Id; source: Account.Id */
  "Account_After"."Id" AS "observed_account_id", /* Source identity: Account.Id; source: Account.Id */
  "Flow_Context"."Survey_Index_Number__c" AS "survey_index_number", /* Source identity: Survey_Index_Number__c; source: Survey_Result__c.Survey_Index_Number__c */
  "Flow_Context"."Completion_Status_Timestamp__c" AS "survey_completion_timestamp", /* Source identity: Completion_Status_Timestamp__c; source: Survey_Result__c.Completion_Status_Timestamp__c */
  DATE("Flow_Context"."Completion_Status_Timestamp__c") >= FROM_ISO8601_DATE('2024-12-16') AS "survey_completion_occurred_on_or_after_launch", /* Survey completion calendar date is on or after launch (2024-12-16); source: Survey_Result__c.Completion_Status_Timestamp__c */
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
  ) AS "cabor_lookup_is_deterministic", /* The selected native assignment has deterministic lookup evidence; source: FlowRecordLookup.Get_Permission_1007 */
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
  END AS "expected__Age_at_Time_of_Consent__pc", /* Expected Account.Age_at_Time_of_Consent__pc: Native Flow assignments to Account.Age_at_Time_of_Consent__pc; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative */
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
  END AS "expected__CABOR_Completion_Date__c", /* Expected Account.CABOR_Completion_Date__c: Native Flow assignments to Account.CABOR_Completion_Date__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative */
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
  END AS "expected__Earliest_Primary_Consent_Date_for_Report__c", /* Expected Account.Earliest_Primary_Consent_Date_for_Report__c: Native Flow assignments to Account.Earliest_Primary_Consent_Date_for_Report__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Negative */
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
  END AS "expected__Latest_Primary_Consent_Date_for_Report__c", /* Expected Account.Latest_Primary_Consent_Date_for_Report__c: Native Flow assignments to Account.Latest_Primary_Consent_Date_for_Report__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1001_Positive, FlowRecordUpdate.updateAccount1001_Negative, FlowRecordUpdate.Update_Account_1007_Positive, FlowRecordUpdate.Update_Account_1007_Negative */
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
  END AS "expected__EHR_Consent_Date_Time__c", /* Expected Account.EHR_Consent_Date_Time__c: Native Flow assignments to Account.EHR_Consent_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1003_NegativeSF */
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
  END AS "expected__EHR_Reconsent_Date_Time__c", /* Expected Account.EHR_Reconsent_Date_Time__c: Native Flow assignments to Account.EHR_Reconsent_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF */
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
  END AS "expected__Update_to_Primary_Consent_Completed__c", /* Expected Account.Update_to_Primary_Consent_Completed__c: Native Flow assignments to Account.Update_to_Primary_Consent_Completed__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount1005 */
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
  END AS "expected__Basics_Date_Time__c", /* Expected Account.Basics_Date_Time__c: Native Flow assignments to Account.Basics_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2001 */
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
  END AS "expected__Overall_Health_Date_Time__c", /* Expected Account.Overall_Health_Date_Time__c: Native Flow assignments to Account.Overall_Health_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2003 */
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
  END AS "expected__Lifestyle_Date_Time__c", /* Expected Account.Lifestyle_Date_Time__c: Native Flow assignments to Account.Lifestyle_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2005 */
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
  END AS "expected__Personal_and_Family_History_Complete__c", /* Expected Account.Personal_and_Family_History_Complete__c: Native Flow assignments to Account.Personal_and_Family_History_Complete__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2006 */
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
  END AS "expected__HC_Access_Date_Time__c", /* Expected Account.HC_Access_Date_Time__c: Native Flow assignments to Account.HC_Access_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2007 */
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
  END AS "expected__Life_Functioning_Date_Time__c", /* Expected Account.Life_Functioning_Date_Time__c: Native Flow assignments to Account.Life_Functioning_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2008 */
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
  END AS "expected__First_Physical_Measurement_Date_Time__c", /* Expected Account.First_Physical_Measurement_Date_Time__c: Native Flow assignments to Account.First_Physical_Measurement_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2009 */
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
  END AS "expected__Last_Physical_Measurement_Date_Time__c", /* Expected Account.Last_Physical_Measurement_Date_Time__c: Native Flow assignments to Account.Last_Physical_Measurement_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2009 */
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
  END AS "expected__EH_Date_Time__c", /* Expected Account.EH_Date_Time__c: Native Flow assignments to Account.EH_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2010 */
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
  END AS "expected__Behavioral_Health_Completion__c", /* Expected Account.Behavioral_Health_Completion__c: Native Flow assignments to Account.Behavioral_Health_Completion__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2011 */
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
  END AS "expected__Environmental_Exposures_Date_Time__c", /* Expected Account.Environmental_Exposures_Date_Time__c: Native Flow assignments to Account.Environmental_Exposures_Date_Time__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2012 */
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
  END AS "expected__Social_Determinants_of_Health_Completion__c", /* Expected Account.Social_Determinants_of_Health_Completion__c: Native Flow assignments to Account.Social_Determinants_of_Health_Completion__c; retain BEFORE when unassigned; source: FlowRecordUpdate.updateAccount2013 */
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
FROM (
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
                                          FROM (
                                            SELECT
                                              *
                                            FROM (
                                              SELECT
                                                *
                                              FROM (
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
                                              ) AS "Survey_Results_At_Execution_5"
                                              WHERE
                                                "Survey_Results_At_Execution_5"."Id" = 'EXAMPLE_VERIFIED_SURVEY_EVENT'
                                            ) AS "Trigger_Survey_Result"
                                          ) AS "Survey_Result__c"
                                        ) AS "Survey_Result__c_2"
                                        LEFT OUTER JOIN (
                                          SELECT
                                            *
                                          FROM (
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
                                          ) AS "Contact_At_Execution"
                                        ) AS "Contact"
                                          ON "Survey_Result__c_2"."Participant__c" = "Contact"."Id"
                                        LEFT OUTER JOIN (
                                          SELECT
                                            *
                                          FROM (
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
                                          ) AS "Account_Before"
                                        ) AS "Account"
                                          ON "Contact"."AccountId" = "Account"."Id"
                                      ) AS "Survey_Result__c_3"
                                    ) AS "Survey_Result__c_4"
                                    LEFT OUTER JOIN (
                                      SELECT
                                        "getEarliestPrimaryConsent"."Id",
                                        "getEarliestPrimaryConsent"."Participant__c",
                                        "getEarliestPrimaryConsent"."Survey_Index_Number__c",
                                        "getEarliestPrimaryConsent"."Completion_Status__c",
                                        "getEarliestPrimaryConsent"."Consent_Status__c",
                                        "getEarliestPrimaryConsent"."Consent_Revoked__c",
                                        "getEarliestPrimaryConsent"."Completion_Status_Timestamp__c",
                                        "getEarliestPrimaryConsent"."Consent_Status_Timestamp__c",
                                        "getEarliestPrimaryConsent"."California_Signature__c",
                                        "getEarliestPrimaryConsent"."valid_from",
                                        "getEarliestPrimaryConsent"."valid_to",
                                        "getEarliestPrimaryConsent"."is_current",
                                        "getEarliestPrimaryConsent"."loaded_at",
                                        1 AS "__ppsc_match"
                                      FROM (
                                        SELECT
                                          *
                                        FROM (
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
                                        ) AS "Survey_Results_At_Execution_4"
                                      ) AS "getEarliestPrimaryConsent"
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
                                "getEarliestEgetEarliestEHRConsentHRConsent"."Id",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."Participant__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."Survey_Index_Number__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."Completion_Status__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."Consent_Status__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."Consent_Revoked__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."Completion_Status_Timestamp__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."Consent_Status_Timestamp__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."California_Signature__c",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."valid_from",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."valid_to",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."is_current",
                                "getEarliestEgetEarliestEHRConsentHRConsent"."loaded_at",
                                1 AS "__ppsc_match"
                              FROM (
                                SELECT
                                  *
                                FROM (
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
                                ) AS "Survey_Results_At_Execution_3"
                              ) AS "getEarliestEgetEarliestEHRConsentHRConsent"
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
                        "Get_Permission_1007"."Id",
                        "Get_Permission_1007"."Participant__c",
                        "Get_Permission_1007"."Survey_Index_Number__c",
                        "Get_Permission_1007"."Completion_Status__c",
                        "Get_Permission_1007"."Consent_Status__c",
                        "Get_Permission_1007"."Consent_Revoked__c",
                        "Get_Permission_1007"."Completion_Status_Timestamp__c",
                        "Get_Permission_1007"."Consent_Status_Timestamp__c",
                        "Get_Permission_1007"."California_Signature__c",
                        "Get_Permission_1007"."valid_from",
                        "Get_Permission_1007"."valid_to",
                        "Get_Permission_1007"."is_current",
                        "Get_Permission_1007"."loaded_at",
                        1 AS "__ppsc_match"
                      FROM (
                        SELECT
                          *
                        FROM (
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
                        ) AS "Survey_Results_At_Execution_2"
                      ) AS "Get_Permission_1007"
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
                "getFirstPhysicalMeasurement"."Id",
                "getFirstPhysicalMeasurement"."Participant__c",
                "getFirstPhysicalMeasurement"."Survey_Index_Number__c",
                "getFirstPhysicalMeasurement"."Completion_Status__c",
                "getFirstPhysicalMeasurement"."Consent_Status__c",
                "getFirstPhysicalMeasurement"."Consent_Revoked__c",
                "getFirstPhysicalMeasurement"."Completion_Status_Timestamp__c",
                "getFirstPhysicalMeasurement"."Consent_Status_Timestamp__c",
                "getFirstPhysicalMeasurement"."California_Signature__c",
                "getFirstPhysicalMeasurement"."valid_from",
                "getFirstPhysicalMeasurement"."valid_to",
                "getFirstPhysicalMeasurement"."is_current",
                "getFirstPhysicalMeasurement"."loaded_at",
                1 AS "__ppsc_match"
              FROM (
                SELECT
                  *
                FROM (
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
                ) AS "Survey_Results_At_Execution"
              ) AS "getFirstPhysicalMeasurement"
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
) AS "Flow_Context"
LEFT OUTER JOIN (
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
) AS "Account_After"
  ON "Flow_Context"."Participant__r.Account.Id" = "Account_After"."Id"
  AND "Flow_Context"."Id" = "Account_After"."survey_result_id";

-- rollups
SELECT
  "Person_Account_2"."Account.Id" AS "expected_account_id", /* Source identity: Account.Id; source: Account.Id */
  "Person_Account_2"."PersonContactId" AS "person_contact_id", /* Source identity: PersonContactId; source: Account.PersonContactId */
  "Person_Account_2"."observed_account_id" AS "observed_account_id", /* Source identity: Account.Id; source: Account.Id */
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
  ) AS "expected__EHR_Authorized__pc", /* Expected Account.EHR_Authorized__pc: Ehr authorized; source: Account.EHR_Authorized__pc */
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
  ) AS "expected__Count_of_Completed_EHR_Auth__pc", /* Expected Account.Count_of_Completed_EHR_Auth__pc: Count of completed ehr auth; source: Account.Count_of_Completed_EHR_Auth__pc */
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
  ) AS "expected__Count_of_Completed_Primary_Consent__pc", /* Expected Account.Count_of_Completed_Primary_Consent__pc: Count of completed primary consent; source: Account.Count_of_Completed_Primary_Consent__pc */
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
  ) AS "expected__Count_of_Completed_Reconsent__pc", /* Expected Account.Count_of_Completed_Reconsent__pc: Count of completed reconsent; source: Account.Count_of_Completed_Reconsent__pc */
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
  ) AS "expected__PPI_2_Completion_Count__pc", /* Expected Account.PPI_2_Completion_Count__pc: Ppi 2 completion count; source: Account.PPI_2_Completion_Count__pc */
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
  ) AS "expected__PPI_3_Completion_Count__pc", /* Expected Account.PPI_3_Completion_Count__pc: Ppi 3 completion count; source: Account.PPI_3_Completion_Count__pc */
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
  ) AS "expected__EHR_Consent_Active__pc", /* Expected Account.EHR_Consent_Active__pc: Ehr consent active; source: Account.EHR_Consent_Active__pc */
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
  ) AS "expected__EHR_Consent_Declined__pc", /* Expected Account.EHR_Consent_Declined__pc: Ehr consent declined; source: Account.EHR_Consent_Declined__pc */
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
  ) AS "expected__PP1_Basics_Survey_Complete__pc", /* Expected Account.PP1_Basics_Survey_Complete__pc: Pp1 basics survey complete; source: Account.PP1_Basics_Survey_Complete__pc */
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
  ) AS "expected__Re_Consent_Declined__pc", /* Expected Account.Re_Consent_Declined__pc: Re consent declined; source: Account.Re_Consent_Declined__pc */
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
  ) AS "expected__Re_consent_Active__pc", /* Expected Account.Re_consent_Active__pc: Re consent active; source: Account.Re_consent_Active__pc */
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
  ) AS "expected__Primary_Consent_Declined__pc", /* Expected Account.Primary_Consent_Declined__pc: Primary consent declined; source: Account.Primary_Consent_Declined__pc */
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
  ) AS "expected__EHR_Consent_Ever__pc", /* Expected Account.EHR_Consent_Ever__pc: Ehr consent ever; source: Account.EHR_Consent_Ever__pc */
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
  ) AS "expected__Assent_Completion_Count__pc", /* Expected Account.Assent_Completion_Count__pc: Assent completion count; source: Account.Assent_Completion_Count__pc */
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
  ) AS "expected__Pediatric_Permission_Completion_Count__pc", /* Expected Account.Pediatric_Permission_Completion_Count__pc: Pediatric permission completion count; source: Account.Pediatric_Permission_Completion_Count__pc */
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
  ) AS "expected__X0_6_Peds_Permission_Count__pc", /* Expected Account.X0_6_Peds_Permission_Count__pc: X0 6 peds permission count; source: Account.X0_6_Peds_Permission_Count__pc */
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
  ) AS "expected__X0_6_Peds_Permission_Declined_Count__pc", /* Expected Account.X0_6_Peds_Permission_Declined_Count__pc: X0 6 peds permission declined count; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
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
  ) AS "expected__X0_6_Peds_Permission_Revoked_Count__pc", /* Expected Account.X0_6_Peds_Permission_Revoked_Count__pc: X0 6 peds permission revoked count; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
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
  ) AS "expected__EHR_Pediatric_Complete__pc", /* Expected Account.EHR_Pediatric_Complete__pc: Ehr pediatric complete; source: Account.EHR_Pediatric_Complete__pc */
  "Person_Account_2"."observed__EHR_Authorized__pc" AS "observed__EHR_Authorized__pc", /* Independently observed Account.EHR_Authorized__pc; source: Account.EHR_Authorized__pc */
  "Person_Account_2"."observed__Count_of_Completed_EHR_Auth__pc" AS "observed__Count_of_Completed_EHR_Auth__pc", /* Independently observed Account.Count_of_Completed_EHR_Auth__pc; source: Account.Count_of_Completed_EHR_Auth__pc */
  "Person_Account_2"."observed__Count_of_Completed_Primary_Consent__pc" AS "observed__Count_of_Completed_Primary_Consent__pc", /* Independently observed Account.Count_of_Completed_Primary_Consent__pc; source: Account.Count_of_Completed_Primary_Consent__pc */
  "Person_Account_2"."observed__Count_of_Completed_Reconsent__pc" AS "observed__Count_of_Completed_Reconsent__pc", /* Independently observed Account.Count_of_Completed_Reconsent__pc; source: Account.Count_of_Completed_Reconsent__pc */
  "Person_Account_2"."observed__PPI_2_Completion_Count__pc" AS "observed__PPI_2_Completion_Count__pc", /* Independently observed Account.PPI_2_Completion_Count__pc; source: Account.PPI_2_Completion_Count__pc */
  "Person_Account_2"."observed__PPI_3_Completion_Count__pc" AS "observed__PPI_3_Completion_Count__pc", /* Independently observed Account.PPI_3_Completion_Count__pc; source: Account.PPI_3_Completion_Count__pc */
  "Person_Account_2"."observed__EHR_Consent_Active__pc" AS "observed__EHR_Consent_Active__pc", /* Independently observed Account.EHR_Consent_Active__pc; source: Account.EHR_Consent_Active__pc */
  "Person_Account_2"."observed__EHR_Consent_Declined__pc" AS "observed__EHR_Consent_Declined__pc", /* Independently observed Account.EHR_Consent_Declined__pc; source: Account.EHR_Consent_Declined__pc */
  "Person_Account_2"."observed__PP1_Basics_Survey_Complete__pc" AS "observed__PP1_Basics_Survey_Complete__pc", /* Independently observed Account.PP1_Basics_Survey_Complete__pc; source: Account.PP1_Basics_Survey_Complete__pc */
  "Person_Account_2"."observed__Re_Consent_Declined__pc" AS "observed__Re_Consent_Declined__pc", /* Independently observed Account.Re_Consent_Declined__pc; source: Account.Re_Consent_Declined__pc */
  "Person_Account_2"."observed__Re_consent_Active__pc" AS "observed__Re_consent_Active__pc", /* Independently observed Account.Re_consent_Active__pc; source: Account.Re_consent_Active__pc */
  "Person_Account_2"."observed__Primary_Consent_Declined__pc" AS "observed__Primary_Consent_Declined__pc", /* Independently observed Account.Primary_Consent_Declined__pc; source: Account.Primary_Consent_Declined__pc */
  "Person_Account_2"."observed__EHR_Consent_Ever__pc" AS "observed__EHR_Consent_Ever__pc", /* Independently observed Account.EHR_Consent_Ever__pc; source: Account.EHR_Consent_Ever__pc */
  "Person_Account_2"."observed__Assent_Completion_Count__pc" AS "observed__Assent_Completion_Count__pc", /* Independently observed Account.Assent_Completion_Count__pc; source: Account.Assent_Completion_Count__pc */
  "Person_Account_2"."observed__Pediatric_Permission_Completion_Count__pc" AS "observed__Pediatric_Permission_Completion_Count__pc", /* Independently observed Account.Pediatric_Permission_Completion_Count__pc; source: Account.Pediatric_Permission_Completion_Count__pc */
  "Person_Account_2"."observed__X0_6_Peds_Permission_Count__pc" AS "observed__X0_6_Peds_Permission_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Count__pc; source: Account.X0_6_Peds_Permission_Count__pc */
  "Person_Account_2"."observed__X0_6_Peds_Permission_Declined_Count__pc" AS "observed__X0_6_Peds_Permission_Declined_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Declined_Count__pc; source: Account.X0_6_Peds_Permission_Declined_Count__pc */
  "Person_Account_2"."observed__X0_6_Peds_Permission_Revoked_Count__pc" AS "observed__X0_6_Peds_Permission_Revoked_Count__pc", /* Independently observed Account.X0_6_Peds_Permission_Revoked_Count__pc; source: Account.X0_6_Peds_Permission_Revoked_Count__pc */
  "Person_Account_2"."observed__EHR_Pediatric_Complete__pc" AS "observed__EHR_Pediatric_Complete__pc" /* Independently observed Account.EHR_Pediatric_Complete__pc; source: Account.EHR_Pediatric_Complete__pc */
FROM (
  SELECT
    "Person_Account"."Id" AS "Account.Id",
    "Person_Account"."PersonContactId",
    "Survey_Result__c"."Completion_Status__c",
    "Survey_Result__c"."Survey_Index_Number__c",
    "Survey_Result__c"."Consent_Status__c",
    "Survey_Result__c"."Consent_Revoked__c",
    "Account_Snapshot"."Id" AS "observed_account_id",
    "Account_Snapshot"."_comparison_observation_row",
    "Account_Snapshot"."EHR_Authorized__pc" AS "observed__EHR_Authorized__pc",
    "Account_Snapshot"."Count_of_Completed_EHR_Auth__pc" AS "observed__Count_of_Completed_EHR_Auth__pc",
    "Account_Snapshot"."Count_of_Completed_Primary_Consent__pc" AS "observed__Count_of_Completed_Primary_Consent__pc",
    "Account_Snapshot"."Count_of_Completed_Reconsent__pc" AS "observed__Count_of_Completed_Reconsent__pc",
    "Account_Snapshot"."PPI_2_Completion_Count__pc" AS "observed__PPI_2_Completion_Count__pc",
    "Account_Snapshot"."PPI_3_Completion_Count__pc" AS "observed__PPI_3_Completion_Count__pc",
    "Account_Snapshot"."EHR_Consent_Active__pc" AS "observed__EHR_Consent_Active__pc",
    "Account_Snapshot"."EHR_Consent_Declined__pc" AS "observed__EHR_Consent_Declined__pc",
    "Account_Snapshot"."PP1_Basics_Survey_Complete__pc" AS "observed__PP1_Basics_Survey_Complete__pc",
    "Account_Snapshot"."Re_Consent_Declined__pc" AS "observed__Re_Consent_Declined__pc",
    "Account_Snapshot"."Re_consent_Active__pc" AS "observed__Re_consent_Active__pc",
    "Account_Snapshot"."Primary_Consent_Declined__pc" AS "observed__Primary_Consent_Declined__pc",
    "Account_Snapshot"."EHR_Consent_Ever__pc" AS "observed__EHR_Consent_Ever__pc",
    "Account_Snapshot"."Assent_Completion_Count__pc" AS "observed__Assent_Completion_Count__pc",
    "Account_Snapshot"."Pediatric_Permission_Completion_Count__pc" AS "observed__Pediatric_Permission_Completion_Count__pc",
    "Account_Snapshot"."X0_6_Peds_Permission_Count__pc" AS "observed__X0_6_Peds_Permission_Count__pc",
    "Account_Snapshot"."X0_6_Peds_Permission_Declined_Count__pc" AS "observed__X0_6_Peds_Permission_Declined_Count__pc",
    "Account_Snapshot"."X0_6_Peds_Permission_Revoked_Count__pc" AS "observed__X0_6_Peds_Permission_Revoked_Count__pc",
    "Account_Snapshot"."EHR_Pediatric_Complete__pc" AS "observed__EHR_Pediatric_Complete__pc"
  FROM (
    SELECT
      "Account_At_Snapshot"."Id",
      "Account_At_Snapshot"."PersonContactId"
    FROM (
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
    ) AS "Account_At_Snapshot"
    WHERE
      "Account_At_Snapshot"."IsPersonAccount"
  ) AS "Person_Account"
  LEFT OUTER JOIN (
    SELECT
      "Survey_Results_At_Snapshot"."Participant__c",
      "Survey_Results_At_Snapshot"."Completion_Status__c",
      "Survey_Results_At_Snapshot"."Survey_Index_Number__c",
      "Survey_Results_At_Snapshot"."Consent_Status__c",
      "Survey_Results_At_Snapshot"."Consent_Revoked__c"
    FROM (
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
    ) AS "Survey_Results_At_Snapshot"
  ) AS "Survey_Result__c"
    ON "Person_Account"."PersonContactId" = "Survey_Result__c"."Participant__c"
  LEFT OUTER JOIN (
    SELECT
      "Account_At_Snapshot_2"."Id",
      "Account_At_Snapshot_2"."PersonContactId",
      "Account_At_Snapshot_2"."IsPersonAccount",
      "Account_At_Snapshot_2"."Age_at_Time_of_Consent__pc",
      "Account_At_Snapshot_2"."CABOR_Completion_Date__c",
      "Account_At_Snapshot_2"."Earliest_Primary_Consent_Date_for_Report__c",
      "Account_At_Snapshot_2"."Latest_Primary_Consent_Date_for_Report__c",
      "Account_At_Snapshot_2"."EHR_Consent_Date_Time__c",
      "Account_At_Snapshot_2"."EHR_Reconsent_Date_Time__c",
      "Account_At_Snapshot_2"."Update_to_Primary_Consent_Completed__c",
      "Account_At_Snapshot_2"."Basics_Date_Time__c",
      "Account_At_Snapshot_2"."Overall_Health_Date_Time__c",
      "Account_At_Snapshot_2"."Lifestyle_Date_Time__c",
      "Account_At_Snapshot_2"."Personal_and_Family_History_Complete__c",
      "Account_At_Snapshot_2"."HC_Access_Date_Time__c",
      "Account_At_Snapshot_2"."Life_Functioning_Date_Time__c",
      "Account_At_Snapshot_2"."First_Physical_Measurement_Date_Time__c",
      "Account_At_Snapshot_2"."Last_Physical_Measurement_Date_Time__c",
      "Account_At_Snapshot_2"."EH_Date_Time__c",
      "Account_At_Snapshot_2"."Behavioral_Health_Completion__c",
      "Account_At_Snapshot_2"."Environmental_Exposures_Date_Time__c",
      "Account_At_Snapshot_2"."Social_Determinants_of_Health_Completion__c",
      "Account_At_Snapshot_2"."EHR_Authorized__pc",
      "Account_At_Snapshot_2"."Count_of_Completed_EHR_Auth__pc",
      "Account_At_Snapshot_2"."Count_of_Completed_Primary_Consent__pc",
      "Account_At_Snapshot_2"."Count_of_Completed_Reconsent__pc",
      "Account_At_Snapshot_2"."PPI_2_Completion_Count__pc",
      "Account_At_Snapshot_2"."PPI_3_Completion_Count__pc",
      "Account_At_Snapshot_2"."EHR_Consent_Active__pc",
      "Account_At_Snapshot_2"."EHR_Consent_Declined__pc",
      "Account_At_Snapshot_2"."PP1_Basics_Survey_Complete__pc",
      "Account_At_Snapshot_2"."Re_Consent_Declined__pc",
      "Account_At_Snapshot_2"."Re_consent_Active__pc",
      "Account_At_Snapshot_2"."Primary_Consent_Declined__pc",
      "Account_At_Snapshot_2"."EHR_Consent_Ever__pc",
      "Account_At_Snapshot_2"."Assent_Completion_Count__pc",
      "Account_At_Snapshot_2"."Pediatric_Permission_Completion_Count__pc",
      "Account_At_Snapshot_2"."X0_6_Peds_Permission_Count__pc",
      "Account_At_Snapshot_2"."X0_6_Peds_Permission_Declined_Count__pc",
      "Account_At_Snapshot_2"."X0_6_Peds_Permission_Revoked_Count__pc",
      "Account_At_Snapshot_2"."EHR_Pediatric_Complete__pc",
      "Account_At_Snapshot_2"."valid_from",
      "Account_At_Snapshot_2"."valid_to",
      "Account_At_Snapshot_2"."is_current",
      "Account_At_Snapshot_2"."loaded_at",
      ROW_NUMBER() OVER () - 1 AS "_comparison_observation_row"
    FROM (
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
    ) AS "Account_At_Snapshot_2"
  ) AS "Account_Snapshot"
    ON "Person_Account"."Id" = "Account_Snapshot"."Id"
) AS "Person_Account_2"
GROUP BY
  "Person_Account_2"."Account.Id",
  "Person_Account_2"."PersonContactId",
  "Person_Account_2"."observed_account_id",
  "Person_Account_2"."_comparison_observation_row",
  "Person_Account_2"."observed__EHR_Authorized__pc",
  "Person_Account_2"."observed__Count_of_Completed_EHR_Auth__pc",
  "Person_Account_2"."observed__Count_of_Completed_Primary_Consent__pc",
  "Person_Account_2"."observed__Count_of_Completed_Reconsent__pc",
  "Person_Account_2"."observed__PPI_2_Completion_Count__pc",
  "Person_Account_2"."observed__PPI_3_Completion_Count__pc",
  "Person_Account_2"."observed__EHR_Consent_Active__pc",
  "Person_Account_2"."observed__EHR_Consent_Declined__pc",
  "Person_Account_2"."observed__PP1_Basics_Survey_Complete__pc",
  "Person_Account_2"."observed__Re_Consent_Declined__pc",
  "Person_Account_2"."observed__Re_consent_Active__pc",
  "Person_Account_2"."observed__Primary_Consent_Declined__pc",
  "Person_Account_2"."observed__EHR_Consent_Ever__pc",
  "Person_Account_2"."observed__Assent_Completion_Count__pc",
  "Person_Account_2"."observed__Pediatric_Permission_Completion_Count__pc",
  "Person_Account_2"."observed__X0_6_Peds_Permission_Count__pc",
  "Person_Account_2"."observed__X0_6_Peds_Permission_Declined_Count__pc",
  "Person_Account_2"."observed__X0_6_Peds_Permission_Revoked_Count__pc",
  "Person_Account_2"."observed__EHR_Pediatric_Complete__pc";
