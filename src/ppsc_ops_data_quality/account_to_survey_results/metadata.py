"""The workflow's selected native files, query request and ordinary run provenance."""

import json
from functools import cache
from hashlib import sha256
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from salesforce.entities.flows.queries import FlowRequest, flow_lineage

from .inputs import load_inputs

FLOW_FIELDS = (
    "Age_at_Time_of_Consent__pc",
    "CABOR_Completion_Date__c",
    "Earliest_Primary_Consent_Date_for_Report__c",
    "Latest_Primary_Consent_Date_for_Report__c",
    "EHR_Consent_Date_Time__c",
    "EHR_Reconsent_Date_Time__c",
    "Update_to_Primary_Consent_Completed__c",
    "Basics_Date_Time__c",
    "Overall_Health_Date_Time__c",
    "Lifestyle_Date_Time__c",
    "Personal_and_Family_History_Complete__c",
    "HC_Access_Date_Time__c",
    "Life_Functioning_Date_Time__c",
    "First_Physical_Measurement_Date_Time__c",
    "Last_Physical_Measurement_Date_Time__c",
    "EH_Date_Time__c",
    "Behavioral_Health_Completion__c",
    "Environmental_Exposures_Date_Time__c",
    "Social_Determinants_of_Health_Completion__c",
)

# Output aliases preserve existing comparison/suite identities. These mappings
# bind source identities; decisions, filters and assignments come from metadata.
FLOW_REQUEST = FlowRequest(
    object_name="Account",
    fields=FLOW_FIELDS,
    before_prefix="Participant__r.Account.",
    target_reference="$Record.Participant__r.AccountId",
    resource_aliases={
        "getEarliestPrimaryConsent": "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent",
        "getEarliestEgetEarliestEHRConsentHRConsent": "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent",
        "getFirstPhysicalMeasurement": "FlowRecordLookup.First_Remote_Physical_Measurement",
        "Get_Permission_1007": "FlowRecordLookup.Pediatric_Permission_For_Assent",
    },
    formula_aliases={"formAgeCalculation": "FlowFormula_Age_At_Execution"},
)


def _input_directory() -> Path:
    return Path(str(files("ppsc_ops_data_quality"))) / "account_to_survey_results/metadata"


def _read_inputs() -> dict:
    inputs = load_inputs(_input_directory())
    flow = inputs["flow"]
    if flow.get("Id") != "301SL00000dpJqKYAU" or not isinstance(flow.get("Metadata"), dict):
        raise ValueError("Selected native Flow identity does not match this workflow")
    for source, field, target in (
        ("Survey_Result__c", "Participant__c", "Contact.Id"),
        ("Contact", "AccountId", "Account.Id"),
        ("Account", "PersonContactId", "Contact.Id"),
    ):
        selected = [
            f"{rel['target_object']}.{rel['target_fields'][0]}"
            for rel in inputs["relationships"]
            if rel["source_object"] == source
            and rel["source_fields"] == [field]
            and len(rel["target_fields"]) == 1
        ]
        if selected != [target]:
            raise ValueError(f"Lake relationship does not match {source}.{field} -> {target}")
    return inputs


@cache
def _compilation_inputs() -> tuple[str, str, str, str]:
    # Cache immutable serialized values and return fresh parsed data to callers.
    inputs = _read_inputs()
    return (
        json.dumps(inputs, sort_keys=True),
        FLOW_REQUEST.model_dump_json(),
        version("ppsc-salesforce"),
        inputs["inputs_sha256"],
    )


def metadata_inputs() -> dict:
    return json.loads(_compilation_inputs()[0])


def metadata_request() -> FlowRequest:
    return FlowRequest.model_validate_json(_compilation_inputs()[1])


def metadata_receipt() -> dict:
    snapshot, request, compiler_version, digest = _compilation_inputs()
    if (
        load_inputs(_input_directory())["inputs_sha256"] != digest
        or FLOW_REQUEST.model_dump_json() != request
        or version("ppsc-salesforce") != compiler_version
    ):
        raise ValueError("Selected inputs or query request changed after compilation")
    inputs = json.loads(snapshot)
    return {
        "org": inputs["source_org"],
        "source_revision": inputs["source_revision"],
        "flow_name": inputs["flow"]["FullName"],
        "flow_version_id": inputs["flow"]["Id"],
        "definition_sha256": inputs["definition_sha256"],
        "source_coverage": inputs["source_coverage"],
        "inputs_sha256": digest,
        "flow_sha256": inputs["flow_sha256"],
        "compiler_version": compiler_version,
        "flow_request_sha256": sha256(request.encode()).hexdigest(),
        "provisional": any(table["provisional"] for table in inputs["tables"].values()),
    }


def expected_value_provenance() -> dict:
    inputs, request = metadata_inputs(), metadata_request()
    return {
        **metadata_receipt(),
        "source_file": "flow.json",
        "fields": {
            field: {
                **record,
                "before": f"AccountBefore.{field}",
                "expected": f"expected__{field}",
                "observed": f"observed__{field}",
            }
            for field, record in flow_lineage(
                inputs["flow"]["Metadata"],
                request,
                source={**metadata_receipt(), "source_file": "flow.json"},
            ).items()
        },
    }


def _field_identity(field: dict) -> tuple[str, str, str]:
    def first(*names):
        return next((field[name] for name in names if field.get(name) is not None), None)

    obj = first("EntityDefinition.QualifiedApiName", "objectName")
    name = first(
        "EntityParticle.QualifiedApiName", "QualifiedApiName", "FieldDefinition.QualifiedApiName"
    )
    if not isinstance(obj, str) or not obj or not isinstance(name, str) or not name:
        raise ValueError("Native field evidence requires object and field identity")
    parent = field.get("FieldDefinition.QualifiedApiName")
    component = first("EntityParticle.IsComponent", "IsComponent") is True
    component = component or (isinstance(parent, str) and parent != name)
    identity = f"{obj}.{parent}.{name}" if component and parent else f"{obj}.{name}"
    return obj, name, identity


def field_definitions(inputs: dict | None = None) -> dict[str, dict]:
    """Keep original field evidence even where its type cannot be compiled."""
    from salesforce.core.provenance import source_metadata
    from salesforce.entities.field_definitions.schemas import UnsupportedFieldError, to_sqlglot

    inputs = metadata_inputs() if inputs is None else inputs
    result = {}
    catalog = inputs["source_catalog"]
    digest = inputs.get("source_catalog_sha256")
    for index, field in enumerate(catalog.get("fields", [])):
        _, _, identity = _field_identity(field)
        if identity in result:
            raise ValueError(f"Ambiguous native field evidence: {identity}")
        source = {
            "org": inputs["source_org"],
            "source_file": "source_catalog.json",
            "source_paths": [f"/fields/{index}"],
            "source_sha256": digest,
        }
        try:
            result[identity] = to_sqlglot(field, source=source).meta["ppsc"]
        except UnsupportedFieldError as error:
            result[identity] = source_metadata(
                field,
                source=source,
                target_field=identity,
                source_entities=["FieldDefinition." + identity],
                description="Native field " + identity,
                translation_status="unsupported",
                reason=str(error),
            )
    return result


def source_schema(inputs: dict, object_name: str, fields: tuple[str, ...]):
    """Convert selected supported source definitions using native Ibis conversion.

    This is a source schema, not an assertion about the physical lake profile.
    Original annotated ColumnDefs remain available through field_definitions().
    """
    import ibis
    from salesforce.entities.field_definitions.schemas import to_sqlglot
    from sqlglot import exp

    if not fields or len(set(fields)) != len(fields):
        raise ValueError("Select nonempty distinct native field names")
    selected = {}
    for field in inputs["source_catalog"].get("fields", []):
        obj, name, _ = _field_identity(field)
        if obj == object_name:
            if name in fields:
                if name in selected:
                    raise ValueError(f"Ambiguous native source field: {object_name}.{name}")
                selected[name] = field
    if set(selected) != set(fields):
        raise ValueError(f"Missing selected native source fields: {object_name}")
    columns = [to_sqlglot(selected[name]) for name in fields]
    return ibis.Schema.from_sqlglot(exp.Schema(expressions=columns))
