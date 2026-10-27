"""Verify definition artifacts and detached provenance; never interpret a Flow."""

from functools import cache
from hashlib import sha256
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ppsc_ops_data_quality.core.configuration import parse_yaml


class DefinitionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Artifact(DefinitionModel):
    path: str = Field(min_length=1)
    role: Literal["flow", "source", "schema", "selection", "lineage", "code"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def safe_path(self) -> "Artifact":
        path = PurePosixPath(self.path)
        if path.is_absolute() or ".." in path.parts or "\\" in self.path or str(path) != self.path:
            raise ValueError("Definition artifact must be a relative package path")
        return self


class DefinitionManifest(DefinitionModel):
    version: Literal["ops-definitions/v2"]
    org: str = Field(min_length=1)
    flow_name: str = Field(min_length=1)
    flow_version_id: Literal["301SL00000dpJqKYAU"]
    source_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    producer_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    provisional: bool
    coverage: str = Field(min_length=1)
    artifacts: tuple[Artifact, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_artifacts(self) -> "DefinitionManifest":
        if len({item.path for item in self.artifacts}) != len(self.artifacts):
            raise ValueError("Duplicate definition artifact paths")
        for role in ("flow", "source", "selection", "lineage"):
            if sum(item.role == role for item in self.artifacts) != 1:
                raise ValueError(f"Expected exactly one {role} artifact")
        if not {"schema", "code"} <= {item.role for item in self.artifacts}:
            raise ValueError("Definition manifest must include schemas and executable builders")
        required = {
            "account_to_survey_results/flow.py": "code",
            "account_to_survey_results/queries.py": "code",
            "account_to_survey_results/input_schemas.py": "code",
            "account_to_survey_results/history.py": "code",
            "account_to_survey_results/lineage.py": "code",
            "account_to_survey_results/metadata.py": "code",
            "core/projection.py": "code",
            "core/configuration.py": "code",
            "core/schemas/ddl.py": "code",
            "core/queries/snapshot.py": "code",
            "core/comparison.py": "code",
            **{
                f"account_to_survey_results/inputs/{name}.sql": "schema"
                for name in ("account", "contact", "survey_results", "history")
            },
        }
        declared = {a.path: a.role for a in self.artifacts}
        if any(declared.get(path) != role for path, role in required.items()):
            raise ValueError("Definition manifest omits a required executable/schema artifact")
        return self


class FlowSelection(DefinitionModel):
    """Authoring receipt for the supported local builder, not executable instructions."""

    object_name: Literal["Account"]
    fields: tuple[str, ...] = Field(min_length=1)
    before_prefix: Literal["Participant__r.Account."]
    target_reference: Literal["$Record.Participant__r.AccountId"]
    path_type: Literal["AsyncAfterCommit"]
    resource_aliases: dict[str, str]
    formula_aliases: dict[str, str]

    @model_validator(mode="after")
    def unique_fields(self) -> "FlowSelection":
        if len(set(self.fields)) != len(self.fields) or any(not f.strip() for f in self.fields):
            raise ValueError("Selected fields must be nonempty and unique")
        return self


class DefinitionReceipt(DefinitionModel):
    manifest: DefinitionManifest
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selection_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    implementation_version: str = Field(min_length=1)


class MetadataInputs(DefinitionModel):
    manifest: DefinitionManifest
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selection: FlowSelection
    flow: dict[str, Any]
    lineage: dict[str, dict[str, Any]]
    schemas: dict[str, str]


def load_definition_inputs(root: Path) -> MetadataInputs:
    """Read a verified package snapshot. Native metadata is retained only as evidence."""
    manifest_path = root / "account_to_survey_results/metadata/manifest.json"
    raw = manifest_path.read_bytes()
    manifest = DefinitionManifest.model_validate_json(raw)
    payloads = {}
    schemas = {}
    for artifact in manifest.artifacts:
        path = (root / artifact.path).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Definition artifact escapes package root")
        content = path.read_bytes()
        if sha256(content).hexdigest() != artifact.sha256:
            raise ValueError(f"Definition artifact hash mismatch: {artifact.path}")
        if artifact.role == "schema":
            schemas[artifact.path] = content.decode("utf-8")
        elif artifact.role != "code":
            payloads[artifact.role] = content
    import json

    flow = json.loads(payloads["flow"])
    if flow.get("Id") != manifest.flow_version_id or flow.get("FullName") != manifest.flow_name:
        raise ValueError("Saved Flow identity does not match definition manifest")
    selection = FlowSelection.model_validate(parse_yaml(payloads["selection"].decode("utf-8")))
    lineage = json.loads(payloads["lineage"])
    if set(lineage["ACCOUNT_FIELD_LINEAGE"]) != {f"Account.{f}" for f in selection.fields}:
        raise ValueError("Detached lineage does not cover the selected fields")
    return MetadataInputs(
        manifest=manifest,
        manifest_sha256=sha256(raw).hexdigest(),
        selection=selection,
        flow=flow,
        lineage=lineage,
        schemas=schemas,
    )


@cache
def _snapshot() -> tuple[str, str]:
    root = Path(str(files("ppsc_ops_data_quality")))
    return load_definition_inputs(root).model_dump_json(), version("ppsc-ops-data-quality")


def metadata_inputs() -> MetadataInputs:
    """Return a fresh copy; caller mutation cannot alter the verified definition snapshot."""
    return MetadataInputs.model_validate_json(_snapshot()[0])


def metadata_request() -> FlowSelection:
    return metadata_inputs().selection


def metadata_receipt() -> DefinitionReceipt:
    """Reverify installed source, DDL and lineage before each run or suite serialization."""
    original = metadata_inputs()
    current = load_definition_inputs(Path(str(files("ppsc_ops_data_quality"))))
    if current != original or version("ppsc-ops-data-quality") != _snapshot()[1]:
        raise ValueError("Definition inputs changed after query construction")
    return DefinitionReceipt(
        manifest=current.manifest,
        manifest_sha256=current.manifest_sha256,
        selection_sha256=next(
            a.sha256 for a in current.manifest.artifacts if a.role == "selection"
        ),
        implementation_version=_snapshot()[1],
    )
