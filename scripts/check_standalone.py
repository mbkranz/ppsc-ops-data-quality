"""Build and exercise an installed wheel in an isolated producer-free environment."""

import argparse
import importlib.util
import json
import runpy
import subprocess
from datetime import UTC, datetime
from hashlib import sha256
from importlib.metadata import distribution
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StandaloneReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["standalone-check/v1"] = "standalone-check/v1"
    wheel: Path
    wheel_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    installed_package: Path
    producer_packages_present: Literal[False] = False
    compile: dict[str, Any]
    synthetic: dict[str, Any]


def installed_checks(*, output: Path, wheel: Path) -> None:
    import ppsc_ops_data_quality

    location = Path(ppsc_ops_data_quality.__file__).resolve()
    installed = distribution("ppsc-ops-data-quality")
    origin = json.loads(installed.read_text("direct_url.json") or "{}")
    # uv can install additional dependencies in an overlay outside sys.prefix.
    # Check the actual installed distribution and wheel origin, not that layout.
    if (
        origin.get("url") != wheel.resolve().as_uri()
        or installed.locate_file("ppsc_ops_data_quality/__init__.py").resolve() != location
        or location.is_relative_to(Path(__file__).resolve().parents[1] / "src")
    ):
        raise ValueError("Standalone check imported the source checkout instead of the wheel")
    for name in ("salesforce", "ppsc_metadata", "open_data_contract_standard"):
        if importlib.util.find_spec(name) is not None:
            raise ValueError(f"Standalone environment contains a producer: {name}")
    checks = runpy.run_path(str(Path(__file__).with_name("check_validation.py")))
    compiled = checks["compile_comparisons"](output / "queries")
    validation = checks["validate_synthetic"](output / "validation")
    checks["verify_synthetic_evidence"](output / "validation")
    if not validation["success"]:
        raise ValueError("Standalone synthetic validation failed")
    receipt = StandaloneReceipt(
        wheel=wheel,
        wheel_sha256=sha256(wheel.read_bytes()).hexdigest(),
        installed_package=location,
        compile=compiled,
        synthetic=validation,
    )
    (output / "standalone.json").write_text(receipt.model_dump_json(indent=2) + "\n")
    print(receipt.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--installed", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--wheel", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = (
        args.output
        or Path("build/checks") / ("standalone-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    ).resolve()
    if args.installed:
        installed_checks(output=output, wheel=args.wheel)
        return
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(output / "wheel")], cwd=root, check=True
    )
    (wheel,) = (output / "wheel").glob("*.whl")
    subprocess.run(
        [
            "uv",
            "run",
            "--isolated",
            "--no-project",
            "--refresh-package",
            "ppsc-ops-data-quality",
            "--with",
            str(wheel),
            "python",
            "-I",
            str(Path(__file__).resolve()),
            "--installed",
            "--output",
            str(output),
            "--wheel",
            str(wheel),
        ],
        cwd=output,
        check=True,
    )


if __name__ == "__main__":
    main()
