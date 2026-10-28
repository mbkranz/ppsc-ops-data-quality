"""Explicit lake bindings and provisional domain schema profiles.

Physical types are authored once in definitions/*.sql. Native evidence remains separate.
"""

import json
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
from pathlib import Path

import ibis
from sqlglot import exp, parse_one

from ppsc_ops_data_quality.sources.apmp import logical_schema
from ppsc_ops_data_quality.sources.athena import athena_schema

BINDINGS = {
    "account": {
        "columns": {
            "age_at_time_of_consent__pc": "Age_at_Time_of_Consent__pc",
            "assent_completion_count__pc": "Assent_Completion_Count__pc",
            "basics_date_time__c": "Basics_Date_Time__c",
            "behavioral_health_completion__c": "Behavioral_Health_Completion__c",
            "cabor_completion_date__c": "CABOR_Completion_Date__c",
            "count_of_completed_ehr_auth__pc": "Count_of_Completed_EHR_Auth__pc",
            "count_of_completed_primary_consent__pc": "Count_of_Completed_Primary_Consent__pc",
            "count_of_completed_reconsent__pc": "Count_of_Completed_Reconsent__pc",
            "earliest_primary_consent_date_for_report__c": "Earliest_Primary_Consent_Date_for_Report__c",
            "eh_date_time__c": "EH_Date_Time__c",
            "ehr_authorized__pc": "EHR_Authorized__pc",
            "ehr_consent_active__pc": "EHR_Consent_Active__pc",
            "ehr_consent_date_time__c": "EHR_Consent_Date_Time__c",
            "ehr_consent_declined__pc": "EHR_Consent_Declined__pc",
            "ehr_consent_ever__pc": "EHR_Consent_Ever__pc",
            "ehr_pediatric_complete__pc": "EHR_Pediatric_Complete__pc",
            "ehr_reconsent_date_time__c": "EHR_Reconsent_Date_Time__c",
            "environmental_exposures_date_time__c": "Environmental_Exposures_Date_Time__c",
            "first_physical_measurement_date_time__c": "First_Physical_Measurement_Date_Time__c",
            "hc_access_date_time__c": "HC_Access_Date_Time__c",
            "id": "Id",
            "is_current": "is_current",
            "ispersonaccount": "IsPersonAccount",
            "last_physical_measurement_date_time__c": "Last_Physical_Measurement_Date_Time__c",
            "latest_primary_consent_date_for_report__c": "Latest_Primary_Consent_Date_for_Report__c",
            "life_functioning_date_time__c": "Life_Functioning_Date_Time__c",
            "lifestyle_date_time__c": "Lifestyle_Date_Time__c",
            "loaded_at": "loaded_at",
            "overall_health_date_time__c": "Overall_Health_Date_Time__c",
            "pediatric_permission_completion_count__pc": "Pediatric_Permission_Completion_Count__pc",
            "personal_and_family_history_complete__c": "Personal_and_Family_History_Complete__c",
            "personcontactid": "PersonContactId",
            "pp1_basics_survey_complete__pc": "PP1_Basics_Survey_Complete__pc",
            "ppi_2_completion_count__pc": "PPI_2_Completion_Count__pc",
            "ppi_3_completion_count__pc": "PPI_3_Completion_Count__pc",
            "primary_consent_declined__pc": "Primary_Consent_Declined__pc",
            "re_consent_active__pc": "Re_consent_Active__pc",
            "re_consent_declined__pc": "Re_Consent_Declined__pc",
            "social_determinants_of_health_completion__c": "Social_Determinants_of_Health_Completion__c",
            "update_to_primary_consent_completed__c": "Update_to_Primary_Consent_Completed__c",
            "valid_from": "valid_from",
            "valid_to": "valid_to",
            "x0_6_peds_permission_count__pc": "X0_6_Peds_Permission_Count__pc",
            "x0_6_peds_permission_declined_count__pc": "X0_6_Peds_Permission_Declined_Count__pc",
            "x0_6_peds_permission_revoked_count__pc": "X0_6_Peds_Permission_Revoked_Count__pc",
        },
        "grain": "one version per Id and valid_from",
        "history_boundaries": ["valid_from", "valid_to"],
        "history_fields": ["valid_from", "valid_to", "is_current", "loaded_at"],
        "keys": ["Id"],
        "kind": "table",
        "native_object": "Account",
        "partition_columns": [],
        "provisional": True,
        "relation": "account_history",
    },
    "contact": {
        "columns": {
            "accountid": "AccountId",
            "birthdate": "Birthdate",
            "id": "Id",
            "is_current": "is_current",
            "loaded_at": "loaded_at",
            "valid_from": "valid_from",
            "valid_to": "valid_to",
        },
        "grain": "one version per Id and valid_from",
        "history_boundaries": ["valid_from", "valid_to"],
        "history_fields": ["valid_from", "valid_to", "is_current", "loaded_at"],
        "keys": ["Id"],
        "kind": "table",
        "native_object": "Contact",
        "partition_columns": [],
        "provisional": True,
        "relation": "contact_history",
    },
    "survey_result": {
        "columns": {
            "california_signature__c": "California_Signature__c",
            "completion_status__c": "Completion_Status__c",
            "completion_status_timestamp__c": "Completion_Status_Timestamp__c",
            "consent_revoked__c": "Consent_Revoked__c",
            "consent_status__c": "Consent_Status__c",
            "consent_status_timestamp__c": "Consent_Status_Timestamp__c",
            "id": "Id",
            "is_current": "is_current",
            "loaded_at": "loaded_at",
            "participant__c": "Participant__c",
            "survey_index_number__c": "Survey_Index_Number__c",
            "valid_from": "valid_from",
            "valid_to": "valid_to",
        },
        "grain": "one version per Id and valid_from",
        "history_boundaries": ["valid_from", "valid_to"],
        "history_fields": ["valid_from", "valid_to", "is_current", "loaded_at"],
        "keys": ["Id"],
        "kind": "table",
        "native_object": "Survey_Result__c",
        "partition_columns": [],
        "provisional": True,
        "relation": "survey_results_history",
    },
}

RELATIONSHIPS = [
    {
        "source_fields": ["PersonContactId"],
        "source_object": "Account",
        "target_fields": ["Id"],
        "target_object": "Contact",
    },
    {
        "source_fields": ["AccountId"],
        "source_object": "Contact",
        "target_fields": ["Id"],
        "target_object": "Account",
    },
    {
        "source_fields": ["Participant__c"],
        "source_object": "Survey_Result__c",
        "target_fields": ["Id"],
        "target_object": "Contact",
    },
]


def load_inputs(directory: Path) -> dict:
    """Read selected native evidence and Ops definitions once."""
    definitions = directory.parent / "definitions"
    payloads = {
        name: (directory / f"{name}.json").read_bytes()
        for name in ("flow", "source_catalog", "rollups")
        if (directory / f"{name}.json").exists()
    }
    ddl_bytes = {name: (definitions / f"{name}.sql").read_bytes() for name in BINDINGS}
    descriptions = (definitions / "descriptions.json").read_bytes()
    tables = {}
    for name, binding in BINDINGS.items():
        ddl = ddl_bytes[name].decode()
        schema = athena_schema(ddl)
        if set(schema.names) != set(binding["columns"]):
            raise ValueError(f"Schema/mapping fields disagree: {name}")
        statement = parse_one(ddl, read="athena")
        columns = list(statement.this.expressions)
        for partition in statement.find_all(exp.PartitionedByProperty):
            if isinstance(partition.this, exp.Schema):
                columns.extend(
                    c for c in partition.this.expressions if isinstance(c, exp.ColumnDef)
                )
        types = {column.name: column.args["kind"].sql(dialect="athena") for column in columns}
        boundaries = [
            schema[physical]
            for physical, logical in binding["columns"].items()
            if logical in binding["history_boundaries"]
        ]
        grain = (
            "timestamp"
            if boundaries and all(t.is_timestamp() for t in boundaries)
            else "date"
            if boundaries and all(t.is_date() for t in boundaries)
            else "unestablished"
        )
        tables[name] = {
            **deepcopy(binding),
            "columns": dict(binding["columns"]),
            "catalog": "fixture_catalog",
            "database": "fixture_lake",
            "fields": [(field, str(dtype)) for field, dtype in schema.items()],
            "physical_types": types,
            "history_grain": grain,
        }
    selected = {
        **payloads,
        **{f"definitions/{name}.sql": value for name, value in ddl_bytes.items()},
        "definitions/descriptions.json": descriptions,
        "bindings": json.dumps(
            {"tables": BINDINGS, "relationships": RELATIONSHIPS}, sort_keys=True
        ).encode(),
    }
    digest = sha256(
        b"".join(name.encode() + b"\0" + data for name, data in sorted(selected.items()))
    ).hexdigest()
    inputs = {
        name: json.loads(payloads[name]) if name in payloads else {}
        for name in ("flow", "source_catalog", "rollups")
    }
    native = inputs["source_catalog"].get("fields", [])
    mapped = {
        (table["native_object"], field)
        for table in tables.values()
        for field in table["columns"].values()
        if field not in table["history_fields"]
    }
    available = {
        (
            field.get("EntityDefinition.QualifiedApiName"),
            field.get("FieldDefinition.QualifiedApiName"),
        )
        for field in native
    }
    missing = sorted(f"{obj}.{field}" for obj, field in mapped - available)
    return {
        **inputs,
        "tables": tables,
        "relationships": deepcopy(RELATIONSHIPS),
        "source_org": "qa2",
        "source_revision": "1eedb2abcf5cac6471fb6cc45e5a40c007982854",
        "definition_sha256": sha256(
            b"".join(value for _, value in sorted(selected.items()))
        ).hexdigest(),
        "inputs_sha256": digest,
        "flow_sha256": sha256(payloads.get("flow", b"")).hexdigest(),
        "source_catalog_sha256": sha256(payloads.get("source_catalog", b"")).hexdigest(),
        "source_coverage": {"complete": not missing, "missing_fields": missing},
        "descriptions": json.loads(descriptions),
    }


def _inputs():
    return load_inputs(
        Path(str(files("ppsc_ops_data_quality"))) / "account_to_survey_results/metadata"
    )


def provisional_schema(native_object: str, *, include_history: bool) -> ibis.Schema:
    inputs = _inputs()
    selected = [
        (name, table)
        for name, table in inputs["tables"].items()
        if table["native_object"] == native_object
    ]
    if len(selected) != 1:
        raise ValueError(f"Select one lake dataset for {native_object}")
    name, binding = selected[0]
    schema = logical_schema(inputs, name)
    return (
        schema
        if include_history
        else ibis.schema(
            {
                field: dtype
                for field, dtype in schema.items()
                if field not in binding["history_fields"]
            }
        )
    )


ACCOUNT_VALIDATION_INPUT = provisional_schema("Account", include_history=False)
ACCOUNT_HISTORY_VALIDATION_INPUT = provisional_schema("Account", include_history=True)
ACCOUNT_SNAPSHOT_VALIDATION_INPUT = ACCOUNT_HISTORY_VALIDATION_INPUT
CONTACT_VALIDATION_INPUT = provisional_schema("Contact", include_history=False)
CONTACT_HISTORY_VALIDATION_INPUT = provisional_schema("Contact", include_history=True)
CONTACT_SNAPSHOT_VALIDATION_INPUT = CONTACT_HISTORY_VALIDATION_INPUT
SURVEY_RESULT_VALIDATION_INPUT = provisional_schema("Survey_Result__c", include_history=False)
SURVEY_RESULT_HISTORY_VALIDATION_INPUT = provisional_schema(
    "Survey_Result__c", include_history=True
)
SURVEY_RESULT_SNAPSHOT_VALIDATION_INPUT = SURVEY_RESULT_HISTORY_VALIDATION_INPUT
HISTORY_METADATA = ibis.schema(
    {name: ACCOUNT_HISTORY_VALIDATION_INPUT[name] for name in BINDINGS["account"]["history_fields"]}
)
