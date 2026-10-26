"""The provisional pinned QA2 evidence and explicit compatibility bindings."""

import json
from functools import cache
from hashlib import sha256
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from ppsc_metadata.artifacts import MetadataBundle, MetadataReceipt, load_metadata_bundle
from ppsc_metadata.sources.salesforce_flow import FlowRequest, flow_lineage
from pydantic import Field

from ppsc_ops_data_quality.sources.apmp import lake_bindings

COMPILER_SOURCE_REVISION = "7f4f3108ea0910ebd3649c770242f69e0301917c"
COMPILER_SOURCE_SHA256 = "a74bb14dd0640a500d3050b32d22ae2c7a08c2f188107df8c98d8f7e11e5124a"
COMPILER_WHEEL_SHA256 = "c26afb47820ecabc654f4f73b098af3e96062329815d09304e8f5c3686074ecf"

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


def _compiler_root() -> Path:
    import ppsc_metadata

    return Path(ppsc_metadata.__file__).resolve().parent


def _compiler_source_sha256() -> str:
    """Fingerprint the installed source files selected by the frozen wheel."""
    root = _compiler_root()
    hashes = {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*.py"))
    }
    if not hashes:
        raise ValueError("Installed compiler source files are unavailable for verification")
    return sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _verify_compiler_source() -> None:
    if _compiler_source_sha256() != COMPILER_SOURCE_SHA256:
        raise ValueError(
            "Installed compiler source fingerprint differs from the frozen wheel selection"
        )


def _read_inputs() -> MetadataBundle:
    root = Path(str(files("ppsc_ops_data_quality"))) / "account_to_survey_results/metadata"
    bundle = load_metadata_bundle(root, root / "manifest.json")
    relationships = lake_bindings(bundle).relationships
    # These are the application's explicit ordered join bindings, checked against APMP.
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
                f"APMP relationship does not match join binding {source}.{field} -> {target}"
            )
    return bundle


class CompilationReceipt(MetadataReceipt):
    """Producer receipt plus the consumer configuration actually used to compile."""

    flow_request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    compiler_source_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    compiler_wheel_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    compiler_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


@cache
def _compilation_inputs() -> tuple[str, str, str]:
    _verify_compiler_source()
    # Strings cannot be changed through returned nested mappings or source models.
    return (
        _read_inputs().model_dump_json(by_alias=True, exclude_unset=True),
        FLOW_REQUEST.model_dump_json(),
        version("ppsc-metadata"),
    )


def metadata_inputs() -> MetadataBundle:
    """Return a fresh parse of the verified compilation snapshot."""
    _verify_compiler_source()
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
        definition_id=current.manifest.definition_id,
        flow_request_sha256=sha256(request_json.encode("utf-8")).hexdigest(),
        compiler_source_revision=COMPILER_SOURCE_REVISION,
        compiler_wheel_sha256=COMPILER_WHEEL_SHA256,
        compiler_source_sha256=COMPILER_SOURCE_SHA256,
    )


def expected_value_provenance() -> dict:
    """Describe native source/BEFORE/expected/observed roles without a contract DSL."""
    bundle = metadata_inputs()
    request = metadata_request()
    artifact = next(item for item in bundle.manifest.artifacts if item.role == "flow")
    return {
        "version": "expected-values/v2",
        "definition_id": bundle.manifest.definition_id,
        "manifest_sha256": bundle.manifest_sha256,
        "source": {"path": artifact.path, "sha256": artifact.sha256},
        "fields": {
            field: {
                **evidence.model_dump(mode="json"),
                "before": f"AccountBefore.{field}",
                "expected": f"expected__{field}",
                "observed": f"observed__{field}",
            }
            for field, evidence in flow_lineage(bundle.flow["Metadata"], request).items()
        },
    }
