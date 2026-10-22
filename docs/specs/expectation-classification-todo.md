# TODO: classify expectations independently of provenance

Status: inventory complete; taxonomy and report-schema changes deferred.

Purpose answers what a check establishes. Provenance kind answers where its
definition/evidence came from. Keep these independent: a structural, referential,
or expected-versus-observed check may be authored from a Flow, a schema profile,
or an independent requirement. Row conditions describe scope, not purpose.

## Proposed dimensions

| Dimension | Candidate values | Examples |
| --- | --- | --- |
| Check purpose | structural; referential; expected-versus-observed; population/coverage | Required columns; observed Account identity present; Basics expected/observed pair; independent source count |
| Provenance kind | schema profile; Salesforce Flow; Salesforce rollup definition; independent requirement | Input profile; FlowRecordUpdate; CustomField rollup; verified event-count contract |

Do not automatically classify every non-null check as structural. A missing
observed Account ID tests parent/observation resolution; the same GX class on
an unrelated column may serve a different purpose. Column-pair equality with
both-missing policy can compare identities or derived values.

## Current metadata and gaps

Existing `check_id`, expectation class/kwargs, exact row condition, target fields,
and nested `ppsc` field/branch lineage provide most of the inventory. Domain
lineage exposes `entity_type`, `source_entity`/`source_entities`, `target_field`,
`branches`, descriptions and workbook rows where applicable. Derived field pairs
and lookup determinism already carry their provenance; do not duplicate it.

The following remain authoring decisions: purpose of identity/uniqueness checks,
independent sources for count contracts, and provenance for required columns.
Do not infer those facts solely from a GX class, suffix, or absence of lineage.

## Inventory

Includes optional independent counts (53 checks); baseline suites omit the two
count checks (27 Flow + 24 rollup). Each row lists the actual class, check ID,
serialized scope and available lineage fields. No suite or report behavior changes.

### Flow

| Check ID | GX class | Row condition | Lineage fields |
| --- | --- | --- | --- |
| flow_comparison_required_columns | ExpectTableColumnsToMatchSet | None | None |
| flow_survey_result_id_is_present | ExpectColumnValuesToNotBeNull | survey_completion_occurred_on_or_after_launch == True | None |
| flow_participant_contact_id_is_present | ExpectColumnValuesToNotBeNull | survey_completion_occurred_on_or_after_launch == True | None |
| flow_expected_account_id_is_present | ExpectColumnValuesToNotBeNull | survey_completion_occurred_on_or_after_launch == True | None |
| flow_observed_account_id_is_present | ExpectColumnValuesToNotBeNull | survey_completion_occurred_on_or_after_launch == True | None |
| one_comparison_row_per_survey_event | ExpectColumnValuesToBeUnique | survey_completion_occurred_on_or_after_launch == True | None |
| permission_lookup_resolution_evidence_is_present | ExpectColumnValuesToNotBeNull | survey_completion_occurred_on_or_after_launch == True | None |
| permission_lookup_is_deterministic | ExpectColumnValuesToBeInSet | survey_completion_occurred_on_or_after_launch == True | description, entity_type, rule_id, source_entities, source_entity, source_flow, workbook_row, workbook_tab |
| observed_Age_at_Time_of_Consent__pc_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_CABOR_Completion_Date__c_equals_expected | ExpectColumnPairValuesToBeEqual | (survey_completion_occurred_on_or_after_launch == True AND cabor_lookup_is_deterministic == True) | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Earliest_Primary_Consent_Date_for_Report__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Latest_Primary_Consent_Date_for_Report__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_EHR_Consent_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_EHR_Reconsent_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Update_to_Primary_Consent_Completed__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Basics_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Overall_Health_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Lifestyle_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Personal_and_Family_History_Complete__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_HC_Access_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Life_Functioning_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_First_Physical_Measurement_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Last_Physical_Measurement_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_EH_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Behavioral_Health_Completion__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Environmental_Exposures_Date_Time__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| observed_Social_Determinants_of_Health_Completion__c_equals_expected | ExpectColumnPairValuesToBeEqual | survey_completion_occurred_on_or_after_launch == True | branches, description, entity_type, expression, rule_id, source_entities, source_flow, source_notes, target_field, workbook_rows, workbook_tab |
| flow_comparison_row_count_matches_source | ExpectTableRowCountToEqual | survey_completion_occurred_on_or_after_launch == True | None |

### Rollups

| Check ID | GX class | Row condition | Lineage fields |
| --- | --- | --- | --- |
| rollup_comparison_required_columns | ExpectTableColumnsToMatchSet | None | None |
| rollup_expected_account_id_is_present | ExpectColumnValuesToNotBeNull | None | None |
| rollup_person_contact_id_is_present | ExpectColumnValuesToNotBeNull | None | None |
| rollup_observed_account_id_is_present | ExpectColumnValuesToNotBeNull | None | None |
| one_rollup_comparison_row_per_person_account | ExpectColumnValuesToBeUnique | None | None |
| observed_EHR_Authorized__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_Count_of_Completed_EHR_Auth__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_Count_of_Completed_Primary_Consent__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_Count_of_Completed_Reconsent__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_PPI_2_Completion_Count__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_PPI_3_Completion_Count__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_EHR_Consent_Active__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_EHR_Consent_Declined__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_PP1_Basics_Survey_Complete__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_Re_Consent_Declined__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_Re_consent_Active__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_Primary_Consent_Declined__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_EHR_Consent_Ever__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_Assent_Completion_Count__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_Pediatric_Permission_Completion_Count__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_X0_6_Peds_Permission_Count__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_X0_6_Peds_Permission_Declined_Count__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_X0_6_Peds_Permission_Revoked_Count__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| observed_EHR_Pediatric_Complete__pc_equals_expected_rollup | ExpectColumnPairValuesToBeEqual | None | branches, description, entity_type, expression, rule_id, source_entities, source_entity, target_field, workbook_row, workbook_tab |
| rollup_comparison_row_count_matches_source | ExpectTableRowCountToEqual | None | None |

## Follow-up acceptance

1. Review independent purpose/provenance vocabularies with check authors.
2. Trace every proposed value to authored metadata or a documented inference rule.
3. Add explicit metadata only where the inventory identifies a real gap.
4. Test representative structural, referential and derived-value checks, including
   shared GX classes with different purposes and the CABOR combined scope.
5. Propose report-schema changes and backfill/versioning separately. Preserve
   existing provenance and expectation identities.

Implementation remains deferred; this document is the work item.
