"""Contact validation input and timestamp-grain history schemas.

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

CONTACT_VALIDATION_INPUT = ibis.schema(
    {
        "Id": "string",  # row 755: Lookup()
        "AccountId": "string",  # row 758: Lookup(Account)
        "Birthdate": "date",  # row 801: Date
    }
)

CONTACT_HISTORY_VALIDATION_INPUT = ibis.schema(
    {**CONTACT_VALIDATION_INPUT.fields, **HISTORY_METADATA.fields}
)

# snapshot() filters rows without adding, dropping or casting fields.
CONTACT_SNAPSHOT_VALIDATION_INPUT = CONTACT_HISTORY_VALIDATION_INPUT
