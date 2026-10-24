"""The provisional pinned QA2 evidence and explicit compatibility bindings."""

from functools import cache
from hashlib import sha256
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from open_data_contract_standard.model import OpenDataContractStandard
from ppsc_metadata.artifacts import MetadataBundle, MetadataReceipt, load_metadata_bundle
from ppsc_metadata.contracts import validate_contract
from ppsc_metadata.definitions import ProjectionDefinitionsRequest, add_projection_definitions
from ppsc_metadata.sources.salesforce_flow import FlowRequest, flow_lineage
from pydantic import Field

from ppsc_ops_data_quality.core.schemas.contracts import normalize_foreign_keys

COMPILER_SOURCE_REVISION = "1eedb2abcf5cac6471fb6cc45e5a40c007982854"
COMPILER_WHEEL_SHA256 = "fd0934ef5b8234554446358aa4471c8be1257d9e0fb8b6f9ae3ec408e4d502b8"

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


def _read_inputs() -> MetadataBundle:
    root = Path(str(files("ppsc_ops_data_quality")))
    bundle = load_metadata_bundle(root, root / "account_to_survey_results/metadata/manifest.json")
    relationships = normalize_foreign_keys(bundle.contract)
    # These are the application's explicit join bindings, checked against ODCS.
    for source, field, target in (
        ("Survey_Result__c", "Participant__c", "Contact.Id"),
        ("Contact", "AccountId", "Account.Id"),
        ("Account", "PersonContactId", "Contact.Id"),
    ):
        selected = [
            f"{key.target_object}.{key.target_fields[0]}"
            for key in relationships
            if key.source_object == source and key.source_fields == (field,)
        ]
        if selected != [target]:
            raise ValueError(
                f"ODCS relationship does not match join binding {source}.{field} -> {target}"
            )
    return bundle


class CompilationReceipt(MetadataReceipt):
    """Producer receipt plus the consumer configuration actually used to compile."""

    flow_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    compiler_source_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    compiler_wheel_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


@cache
def _compilation_inputs() -> tuple[str, str, str]:
    # Strings cannot be changed through a returned nested dict or ODCS model.
    return (
        _read_inputs().model_dump_json(by_alias=True, exclude_unset=True),
        FLOW_REQUEST.model_dump_json(),
        version("ppsc-metadata"),
    )


def metadata_inputs() -> MetadataBundle:
    """Return a fresh parse of the verified compilation snapshot."""
    return MetadataBundle.model_validate_json(_compilation_inputs()[0])


def metadata_request() -> FlowRequest:
    """Return the same request used by lineage and every compilation stage."""
    return FlowRequest.model_validate_json(_compilation_inputs()[1])


def metadata_receipt() -> CompilationReceipt:
    """Reverify installed artifacts before a run, including the compiled snapshot."""
    current = _read_inputs()
    _, request_json, compiler_version = _compilation_inputs()
    if (
        current.manifest_sha256 != metadata_inputs().manifest_sha256
        or FLOW_REQUEST.model_dump_json() != request_json
        or version("ppsc-metadata") != compiler_version
    ):
        raise ValueError("Metadata inputs changed after query construction")
    return CompilationReceipt(
        manifest=current.manifest,
        manifest_sha256=current.manifest_sha256,
        compiler_version=compiler_version,
        contract_id=current.contract.id,
        contract_version=current.contract.version,
        flow_request_sha256=sha256(request_json.encode("utf-8")).hexdigest(),
        compiler_source_revision=COMPILER_SOURCE_REVISION,
        compiler_wheel_sha256=COMPILER_WHEEL_SHA256,
    )


def expected_value_contract() -> OpenDataContractStandard:
    """Attach native source definitions with separate BEFORE and expected identities.

    The supplied authored profile stays intact. Derived object copies describe
    roles in this comparison; they do not certify org policy or physical bindings.
    Content-addressed source definitions resolve through the verified manifest.
    """
    bundle = metadata_inputs()
    request = metadata_request()
    document = bundle.contract.model_dump(mode="json", by_alias=True, exclude_unset=True)
    account = next(obj for obj in bundle.contract.schema_ if obj.name == "Account")
    for name in ("AccountBefore", "AccountExpected"):
        if any(obj["name"] == name for obj in document["schema"]):
            raise ValueError(f"Derived contract object already exists: {name}")
        obj = account.model_dump(mode="json", by_alias=True, exclude_unset=True)
        obj.update(id=name, name=name)
        if name == "AccountExpected":
            obj["properties"] = [
                prop for prop in obj["properties"] if prop["name"] in request.fields
            ]
            for prop in obj["properties"]:
                prop["physicalName"] = f"expected__{prop['name']}"
            obj.pop("relationships", None)
        document["schema"].append(obj)
    contract = validate_contract(document)
    artifact = next(item for item in bundle.manifest.artifacts if item.role == "flow")
    bindings = {f"Account.{field}": f"AccountBefore.{field}" for field in request.fields}
    bindings.update(
        {
            "Survey_Result__c.Participant__r.AccountId": "Contact.AccountId",
            "Survey_Result__c.Participant__r.Birthdate": "Contact.Birthdate",
            "Survey_Result__c.Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c": "AccountBefore.Earliest_Primary_Consent_Date_for_Report__c",
        }
    )
    return add_projection_definitions(
        contract,
        ProjectionDefinitionsRequest(
            source_url=f"urn:sha256:{artifact.sha256}",
            field_bindings=bindings,
            target_bindings={
                f"Account.{field}": f"AccountExpected.{field}" for field in request.fields
            },
        ),
        lineage=flow_lineage(bundle.flow["Metadata"], request),
    )
