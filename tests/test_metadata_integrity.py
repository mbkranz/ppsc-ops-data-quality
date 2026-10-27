"""Definition receipts bind immutable source, executable code, DDL and lineage."""

import json
import shutil
from pathlib import Path

import pytest

from ppsc_ops_data_quality.account_to_survey_results import metadata
from ppsc_ops_data_quality.account_to_survey_results.metadata import (
    metadata_inputs,
    metadata_receipt,
)


def test_public_metadata_reads_are_independent_and_do_not_drive_execution():
    first, second = metadata_inputs(), metadata_inputs()
    first.flow["Metadata"]["recordUpdates"].clear()
    first.selection.resource_aliases.clear()
    first.lineage["ACCOUNT_FIELD_LINEAGE"].clear()
    first.schemas.clear()
    assert metadata_inputs() == second
    assert metadata_receipt().manifest_sha256 == second.manifest_sha256


@pytest.mark.parametrize("replace_manifest", [False, True])
@pytest.mark.parametrize(
    "artifact",
    [
        "account_to_survey_results/metadata/flow.json",
        "account_to_survey_results/metadata/lineage.json",
        "account_to_survey_results/flow.py",
        "account_to_survey_results/inputs/account.sql",
    ],
)
def test_changed_source_code_schema_or_lineage_rejects_receipt(
    tmp_path, monkeypatch, replace_manifest, artifact
):
    from hashlib import sha256

    root = Path(__file__).resolve().parents[1] / "src/ppsc_ops_data_quality"
    copied = tmp_path / "package"
    shutil.copytree(root, copied)
    monkeypatch.setattr(metadata, "files", lambda _: copied)
    metadata_receipt()
    target = copied / artifact
    target.write_bytes(target.read_bytes() + b"\n")
    if replace_manifest:
        path = copied / "account_to_survey_results/metadata/manifest.json"
        manifest = json.loads(path.read_bytes())
        selected = next(a for a in manifest["artifacts"] if a["path"] == artifact)
        selected["sha256"] = sha256(target.read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="changed after query construction|hash mismatch"):
        metadata_receipt()


def test_changed_implementation_version_rejects_receipt(monkeypatch):
    metadata_receipt()
    monkeypatch.setattr(metadata, "version", lambda _: "different-implementation")
    with pytest.raises(ValueError, match="changed after query construction"):
        metadata_receipt()


def test_artifact_paths_reject_escape_and_duplicate_declarations():
    from ppsc_ops_data_quality.account_to_survey_results.metadata import (
        Artifact,
        DefinitionManifest,
    )

    for path in ("../outside", "/absolute", "sub\\outside"):
        with pytest.raises(ValueError, match="relative package path"):
            Artifact(path=path, role="code", sha256="0" * 64)
    document = metadata_receipt().manifest.model_dump(mode="json")
    document["artifacts"].append(document["artifacts"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        DefinitionManifest.model_validate(document)
