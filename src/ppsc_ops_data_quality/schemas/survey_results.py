"""Survey_Result__c validation input and timestamp-grain history schemas.

Provenance: salesforce_schemas_combined_latest.xlsx, datamodel-Fields.
Inline row numbers identify the source field definitions. This is the complete
column contract consumed by these queries, not the entire Salesforce object.
All fields remain nullable so GX can detect missing source values.

Salesforce logical types are mapped explicitly below. Physical Athena types,
column casing, timestamp precision/time zone and history layout require catalog
verification. No automatic cast or schema enforcement is performed.
"""

import ibis

from .history import HISTORY_METADATA

SURVEY_RESULT_VALIDATION_INPUT = ibis.schema(
    {
        "Id": "string",  # row 1738: Lookup()
        "Participant__c": "string",  # row 1750: Master-Detail(Contact)
        "Survey_Index_Number__c": "string",  # row 1775: Text(255)
        "Completion_Status__c": "string",  # row 1751: Picklist
        "Consent_Status__c": "string",  # row 1752: Picklist
        "Consent_Revoked__c": "boolean",  # row 1763: Checkbox
        "Completion_Status_Timestamp__c": "timestamp",  # row 1760: Date/Time
        "Consent_Status_Timestamp__c": "timestamp",  # row 1764: Date/Time
        "California_Signature__c": "timestamp",  # row 1759: Date/Time
    }
)

SURVEY_RESULT_HISTORY_VALIDATION_INPUT = ibis.schema(
    {**SURVEY_RESULT_VALIDATION_INPUT.fields, **HISTORY_METADATA.fields}
)

# snapshot() filters rows without adding, dropping or casting fields.
SURVEY_RESULT_SNAPSHOT_VALIDATION_INPUT = SURVEY_RESULT_HISTORY_VALIDATION_INPUT
