"""Provisional Survey_Result__c schemas derived from the pinned APMP handoff."""

from .inputs import provisional_schema

SURVEY_RESULT_VALIDATION_INPUT = provisional_schema("Survey_Result__c", include_history=False)
SURVEY_RESULT_HISTORY_VALIDATION_INPUT = provisional_schema(
    "Survey_Result__c", include_history=True
)
SURVEY_RESULT_SNAPSHOT_VALIDATION_INPUT = SURVEY_RESULT_HISTORY_VALIDATION_INPUT
