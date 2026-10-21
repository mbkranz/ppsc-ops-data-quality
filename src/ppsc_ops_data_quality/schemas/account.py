"""Account validation input and timestamp-grain history schemas.

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

ACCOUNT_VALIDATION_INPUT = ibis.schema(
    {
        "Id": "string",  # row 3: Lookup()
        "PersonContactId": "string",  # row 70: Lookup(Contact)
        "IsPersonAccount": "boolean",  # row 71: Checkbox
        "Age_at_Time_of_Consent__pc": "decimal(3, 0)",  # row 407: Number(3, 0)
        "CABOR_Completion_Date__c": "timestamp",  # row 148: Date/Time
        "Earliest_Primary_Consent_Date_for_Report__c": "timestamp",  # row 160: Date/Time
        "Latest_Primary_Consent_Date_for_Report__c": "timestamp",  # row 184: Date/Time
        "EHR_Consent_Date_Time__c": "timestamp",  # row 254: Date/Time
        "EHR_Reconsent_Date_Time__c": "timestamp",  # row 255: Date/Time
        "Update_to_Primary_Consent_Completed__c": "timestamp",  # row 213: Date/Time
        "Basics_Date_Time__c": "timestamp",  # row 245: Date/Time
        "Overall_Health_Date_Time__c": "timestamp",  # row 202: Date/Time
        "Lifestyle_Date_Time__c": "timestamp",  # row 189: Date/Time
        "Personal_and_Family_History_Complete__c": "timestamp",  # row 205: Date/Time
        "HC_Access_Date_Time__c": "timestamp",  # row 171: Date/Time
        "Life_Functioning_Date_Time__c": "timestamp",  # row 188: Date/Time
        "First_Physical_Measurement_Date_Time__c": "timestamp",  # row 169: Date/Time
        "Last_Physical_Measurement_Date_Time__c": "timestamp",  # row 181: Date/Time
        "EH_Date_Time__c": "timestamp",  # row 157: Date/Time
        "Behavioral_Health_Completion__c": "timestamp",  # row 146: Date/Time
        "Environmental_Exposures_Date_Time__c": "timestamp",  # row 316: Date/Time
        "Social_Determinants_of_Health_Completion__c": "timestamp",  # row 212: Date/Time
        "EHR_Authorized__pc": "int64",  # row 442: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "Count_of_Completed_EHR_Auth__pc": "int64",  # row 465: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "Count_of_Completed_Primary_Consent__pc": "int64",  # row 466: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "Count_of_Completed_Reconsent__pc": "int64",  # row 467: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "PPI_2_Completion_Count__pc": "int64",  # row 468: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "PPI_3_Completion_Count__pc": "int64",  # row 469: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "EHR_Consent_Active__pc": "int64",  # row 443: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "EHR_Consent_Declined__pc": "int64",  # row 540: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "PP1_Basics_Survey_Complete__pc": "int64",  # row 541: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "Re_Consent_Declined__pc": "int64",  # row 542: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "Re_consent_Active__pc": "int64",  # row 543: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "Primary_Consent_Declined__pc": "int64",  # row 555: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "EHR_Consent_Ever__pc": "int64",  # row 562: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "Assent_Completion_Count__pc": "int64",  # row 594: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "Pediatric_Permission_Completion_Count__pc": "int64",  # row 595: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "X0_6_Peds_Permission_Count__pc": "int64",  # row 622: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "X0_6_Peds_Permission_Declined_Count__pc": "int64",  # row 623: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "X0_6_Peds_Permission_Revoked_Count__pc": "int64",  # row 624: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
        "EHR_Pediatric_Complete__pc": "int64",  # row 626: Roll-Up Summary (COUNT Survey Result); logical COUNT mapped to int64
    }
)

ACCOUNT_HISTORY_VALIDATION_INPUT = ibis.schema(
    {**ACCOUNT_VALIDATION_INPUT.fields, **HISTORY_METADATA.fields}
)

# snapshot() filters rows without adding, dropping or casting fields.
ACCOUNT_SNAPSHOT_VALIDATION_INPUT = ACCOUNT_HISTORY_VALIDATION_INPUT
