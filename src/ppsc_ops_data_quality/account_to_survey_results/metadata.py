"""The provisional pinned QA2 evidence and explicit compatibility bindings."""

from functools import cache
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from ppsc_metadata.artifacts import MetadataBundle, MetadataReceipt, load_metadata_bundle
from ppsc_metadata.contracts import internal_reference, property_references
from ppsc_metadata.sources.salesforce_flow import FlowRequest

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
    references = property_references(bundle.contract)
    # These are the application's explicit join bindings, checked against ODCS.
    for source, field, target in (
        ("Survey_Result__c", "Participant__c", "Contact.Id"),
        ("Contact", "AccountId", "Account.Id"),
        ("Account", "PersonContactId", "Contact.Id"),
    ):
        obj = next(obj for obj in bundle.contract.schema_ if obj.name == source)
        prop = next(prop for prop in obj.properties if prop.name == field)
        selected = [
            references.get(internal_reference(relationship.to))
            for relationship in prop.relationships or []
            if isinstance(relationship.to, str)
        ]
        if selected != [target]:
            raise ValueError(
                f"ODCS relationship does not match join binding {source}.{field} -> {target}"
            )
    return bundle


@cache
def metadata_inputs() -> MetadataBundle:
    return _read_inputs()


def metadata_receipt() -> MetadataReceipt:
    """Reverify installed artifacts before a run, including the compiled snapshot."""
    current = _read_inputs()
    if current.manifest_sha256 != metadata_inputs().manifest_sha256:
        raise ValueError("Metadata inputs changed after query construction")
    return MetadataReceipt(
        manifest=current.manifest,
        manifest_sha256=current.manifest_sha256,
        compiler_version=version("ppsc-metadata"),
        contract_id=current.contract.id,
        contract_version=current.contract.version,
    )
