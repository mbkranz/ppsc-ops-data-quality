"""Native Flow provenance plus the remaining workbook-authored rollup evidence.

Flow branches are generated from the selected metadata. Workbook rows are
supplemental navigation only. No Flow conditions or assignments are authored here.
Rollup rules remain unchanged pending verified native rollup metadata.
"""

from ppsc_metadata.sources.salesforce_flow import flow_lineage

from .metadata import metadata_inputs, metadata_request

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
    "count_completed_ehr_authorization": {
        "output_fields": ["Account.EHR_Authorized__pc", "Account.Count_of_Completed_EHR_Auth__pc"],
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

_WORKBOOK_ROWS = {
    "FlowRecordUpdate.updateAccount1001_Positive": 14488,
    "FlowRecordUpdate.updateAccount1001_Negative": 14490,
    "FlowRecordUpdate.Copy_1_of_updateAccount1003_PositiveSF": 14495,
    "FlowRecordUpdate.updateAccount1003_NegativeSF": 14496,
    "FlowRecordUpdate.Update_Account_1007_Positive": 14503,
    "FlowRecordUpdate.Update_Account_1007_Negative": 14504,
    "FlowRecordUpdate.updateAccount1005": 14498,
    "FlowRecordUpdate.updateAccount2001": 14506,
    "FlowRecordUpdate.updateAccount2003": 14508,
    "FlowRecordUpdate.updateAccount2005": 14510,
    "FlowRecordUpdate.updateAccount2006": 14512,
    "FlowRecordUpdate.updateAccount2007": 14514,
    "FlowRecordUpdate.updateAccount2008": 14516,
    "FlowRecordUpdate.updateAccount2009": 14519,
    "FlowRecordUpdate.updateAccount2010": 14521,
    "FlowRecordUpdate.updateAccount2011": 14523,
    "FlowRecordUpdate.updateAccount2012": 14525,
    "FlowRecordUpdate.updateAccount2013": 14527,
}

_bundle = metadata_inputs()
_native = _bundle.flow["Metadata"]
_flow_artifact = next(item for item in _bundle.manifest.artifacts if item.role == "flow")
_request = metadata_request()
_evidence = flow_lineage(_native, _request)
ACCOUNT_FIELD_LINEAGE = {}
PROJECTION_LINEAGE = {}
for _field, _record in _evidence.items():
    _entry = {
        **_record.model_dump(mode="json"),
        "rule_id": f"{_bundle.manifest.flow_version_id}/{_field}",
        "entity_type": "AccountField",
        "source_flow": _bundle.manifest.flow_name,
        "flow_version_id": _bundle.manifest.flow_version_id,
        "source_file": _flow_artifact.path,
        "source_sha256": _flow_artifact.sha256,
        "metadata_manifest_sha256": _bundle.manifest_sha256,
        "contract_id": _bundle.contract.id,
        "contract_version": _bundle.contract.version,
        "provisional": _bundle.manifest.provisional,
        "workbook_rows": [
            _WORKBOOK_ROWS[source] for source in _record.source_entities if source in _WORKBOOK_ROWS
        ],
        "workbook_reference_role": "supplemental navigation; native metadata is authoritative",
    }
    ACCOUNT_FIELD_LINEAGE[_record.target_field] = _entry
    PROJECTION_LINEAGE[_field] = _entry
    BRANCH_LINEAGE.update({branch["rule_id"]: branch for branch in _entry["branches"]})
for _target, _entry in ROLLUP_FIELD_LINEAGE.items():
    PROJECTION_LINEAGE[_target.removeprefix("Account.")] = {
        **_entry,
        "rule_id": _entry["expression"],
        "target_field": _target,
        "description": _entry["expression"]
        .replace("_indicator", "")
        .replace("_", " ")
        .capitalize(),
        "source_entities": [_entry["source_entity"]],
        "branches": [{"rule_id": name, **BRANCH_LINEAGE[name]} for name in _entry["branches"]],
    }

FLOW_ENTITY_LINEAGE = {}
for _kind, _prefix in (
    ("decisions", "FlowDecision"),
    ("recordLookups", "FlowRecordLookup"),
    ("recordUpdates", "FlowRecordUpdate"),
    ("formulas", "FlowFormula"),
):
    for _index, _node in enumerate(_native.get(_kind) or []):
        _source = f"{_prefix}.{_node['name']}"
        _alias = _request.resource_aliases.get(_node["name"], _source)
        FLOW_ENTITY_LINEAGE[_alias] = {
            "source_entity": _source,
            "source_flow": _bundle.manifest.flow_name,
            "entity_type": _prefix,
            "source_path": f"/Metadata/{_kind}/{_index}",
            "flow_version_id": _bundle.manifest.flow_version_id,
        }
for _alias, _source, _description in (
    (
        "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
        "FlowRecordLookup.Get_Permission_1007",
        "Number of matching native permission candidates",
    ),
    (
        "CABOR_Completion_Date__c_is_deterministic",
        "FlowRecordLookup.Get_Permission_1007",
        "The selected native assignment has deterministic lookup evidence",
    ),
    (
        "FlowFormula_Age_At_Execution",
        "FlowFormula.formAgeCalculation",
        "Native formula evaluated at the explicit org-local execution DATE",
    ),
):
    PROJECTION_LINEAGE[_alias] = {
        "rule_id": _alias,
        "entity_type": _source.split(".", 1)[0],
        "description": _description,
        "source_entities": [_source],
        "source_flow": _bundle.manifest.flow_name,
        "flow_version_id": _bundle.manifest.flow_version_id,
        "metadata_manifest_sha256": _bundle.manifest_sha256,
    }

for _alias, _source in (
    ("Record.Id", "Survey_Result__c.Id"),
    ("Account.Id", "Account.Id"),
    ("Participant__c", "Survey_Result__c.Participant__c"),
    ("Survey_Index_Number__c", "Survey_Result__c.Survey_Index_Number__c"),
    ("Completion_Status_Timestamp__c", "Survey_Result__c.Completion_Status_Timestamp__c"),
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
    ("survey_completion_timestamp", "Completion_Status_Timestamp__c", "evidence"),
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

PROJECTION_LINEAGE["survey_completion_occurred_on_or_after_launch"] = {
    "rule_id": "survey_completion_occurred_on_or_after_launch",
    "entity_type": "BusinessCondition",
    "comparison_role": "scope",
    "description": "Survey completion calendar date is on or after launch (2024-12-16)",
    "source_entities": ["Survey_Result__c.Completion_Status_Timestamp__c"],
    "source_requirement": "User-specified post-launch scope for Account completion updates",
    "launch_date": "2024-12-16",
    "boundary": "inclusive",
    "timestamp_semantics": "Completion timestamp calendar date; normalize business timezone upstream",
    "null_policy": "Unknown completion timestamps retain NULL scope and are not Flow-validated",
}
