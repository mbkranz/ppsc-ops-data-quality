"""Hash the reviewed definition files into a fresh candidate manifest; never validate live data."""

import argparse
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ppsc_ops_data_quality.account_to_survey_results.metadata import DefinitionManifest


class CaptureReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_count: int = Field(ge=1)


def capture_definitions(*, root: Path, output: Path) -> CaptureReceipt:
    """Refresh digests only; selected sources, coverage and provenance stay authored."""
    root = root.resolve()
    template = DefinitionManifest.model_validate_json(
        (root / "account_to_survey_results/metadata/manifest.json").read_bytes()
    )
    artifacts = []
    for artifact in template.artifacts:
        path = (root / artifact.path).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Definition artifact escapes package root")
        artifacts.append(
            artifact.model_copy(update={"sha256": sha256(path.read_bytes()).hexdigest()})
        )
    manifest = DefinitionManifest.model_validate(
        {
            **template.model_dump(),
            "artifacts": artifacts,
        }
    )
    content = (manifest.model_dump_json(indent=2) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(content)
    return CaptureReceipt(
        path=output, sha256=sha256(content).hexdigest(), artifact_count=len(artifacts)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("src/ppsc_ops_data_quality"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(capture_definitions(root=args.root, output=args.output).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
