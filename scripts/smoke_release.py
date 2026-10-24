"""Check the installed Linux bundle, CLI and synthetic reports without indexes."""

import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import Literal
from zipfile import ZipFile

from pydantic import BaseModel, ConfigDict

from scripts.build_release import compatible_producer
from scripts.glue_wheels import validate_archive


class SmokeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: Literal["passed"] = "passed"
    distribution: str
    environment: Path
    evidence: Path


def smoke_release(*, root: Path) -> SmokeResult:
    if not compatible_producer():
        raise ValueError("Run bundle installation checks on the pinned Linux producer")
    bundle = root / "build/release/bundle/dependencies.gluewheels.zip"
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    validate_archive(bundle, application=(project["name"], project["version"]))
    for name in ("smoke-wheels", "invalid-run"):
        path = root / "build/release" / name
        if path.exists():
            shutil.rmtree(path)
    wheels = root / "build/release/smoke-wheels"
    with ZipFile(bundle) as archive:
        archive.extractall(wheels)
    environment = root / "build/release/smoke-env"
    python, cli = environment / "bin/python", environment / "bin/ppsc-dq"

    def run(*command: str) -> None:
        subprocess.run(command, cwd=root, check=True)

    run("uv", "venv", "--python", "3.11.17", "--clear", str(environment))
    run(
        "uv",
        "pip",
        "install",
        "--python",
        str(python),
        "--no-index",
        "--find-links",
        str(wheels),
        "ppsc-ops-data-quality",
    )
    run("uv", "pip", "check", "--python", str(python))
    run(
        str(python),
        "-I",
        "-c",
        "from pathlib import Path; import sys, ppsc_ops_data_quality; assert Path(ppsc_ops_data_quality.__file__).is_relative_to(Path(sys.prefix))",
    )
    run(
        str(python),
        "-I",
        "-c",
        "from ppsc_ops_data_quality.account_to_survey_results.metadata import metadata_receipt; "
        "import sys; receipt = metadata_receipt(); "
        "assert receipt.compiler_version == '0.2.0'; "
        "assert receipt.manifest.flow_version_id == '301SL00000dpJqKYAU'; "
        "assert receipt.manifest.provisional; assert 'salesforce' not in sys.modules",
    )
    run(str(cli), "--help")
    invalid = root / "build/release/invalid.yaml"
    invalid.write_text("unexpected: true\n", encoding="utf-8")
    invalid_run = root / "build/release/invalid-run"
    result = subprocess.run(
        [str(cli), "validate", "--config", str(invalid), "--run-dir", str(invalid_run)], cwd=root
    )
    if result.returncode != 2 or invalid_run.exists():
        raise ValueError(
            "Invalid configuration must fail with code 2 before creating a run directory"
        )
    checks = root / "build/release/smoke-checks"
    checks.mkdir(parents=True, exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix="run-", dir=checks))
    for action, destination in (("compile", "queries"), ("synthetic", "validation")):
        run(
            str(python),
            "-I",
            str(root / "scripts/check_validation.py"),
            action,
            "--output",
            str(evidence / destination),
        )
    return SmokeResult(
        distribution="ppsc-ops-data-quality", environment=environment, evidence=evidence
    )


if __name__ == "__main__":
    print(smoke_release(root=Path.cwd()).model_dump_json())
