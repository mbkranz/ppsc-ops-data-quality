"""Assemble already built wheels and driver into one hashed Glue release."""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_bundle(bundle: Path, *, expected_manifest_sha256=None):
    """Verify the exact runtime files before planning or uploading a release."""
    manifest_path = bundle / "manifest.json"
    if expected_manifest_sha256 and sha256(manifest_path) != expected_manifest_sha256:
        raise ValueError("Release manifest changed after deployment planning")
    manifest = json.loads(manifest_path.read_text())
    if manifest["schema_version"] != 1 or manifest["runtime"] != {
        "glue_version": "5.0",
        "python_version": "3.11",
        "architecture": "x86_64",
    }:
        raise ValueError("Unsupported release runtime or manifest schema")
    if not re.fullmatch(r"[0-9a-f]{40}", manifest["revision"]):
        raise ValueError("Release revision must be a full Git SHA")
    if set(manifest["files"]) != {
        "dependencies.gluewheels.zip",
        "requirements.txt",
        "validate_history.py",
    }:
        raise ValueError("Release manifest must declare exactly the runtime artifacts")
    for filename, expected in manifest["files"].items():
        if sha256(bundle / filename) != expected:
            raise ValueError(f"Release artifact checksum mismatch: {filename}")
    return manifest


def package_release(directory: Path, revision: str):
    """Package downloaded CPython 3.11/Linux wheels; perform no CLI or AWS calls."""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Release revision must be a full Git commit SHA")
    wheels = sorted((directory / "wheels").glob("*.whl"))
    project = list((directory / "project").glob("ppsc_ops_data_quality-*.whl"))
    if not wheels or len(project) != 1:
        raise ValueError("Release requires dependencies and exactly one project wheel")
    if any(path.name.startswith("ppsc_ops_data_quality-") for path in wheels):
        raise ValueError("Project wheel must appear only once")
    output = directory / "bundle"
    output.mkdir(parents=True, exist_ok=False)
    archive = output / "dependencies.gluewheels.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
        for path in sorted([*wheels, *project]):
            # Fixed timestamps/order keep the archive stable for identical inputs.
            entry = ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            bundle.writestr(entry, path.read_bytes())
    shutil.copyfile("glue/scripts/validate_history.py", output / "validate_history.py")
    shutil.copyfile(directory / "requirements.txt", output / "requirements.txt")
    manifest = {
        "schema_version": 1,
        "revision": revision,
        "runtime": {"glue_version": "5.0", "python_version": "3.11", "architecture": "x86_64"},
        "lock_sha256": sha256(Path("uv.lock")),
        "files": {path.name: sha256(path) for path in sorted(output.iterdir())},
        "wheels": {path.name: sha256(path) for path in sorted([*wheels, *project])},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("build/release"))
    parser.add_argument("--revision")
    parser.add_argument("--verify-plan", type=Path)
    args = parser.parse_args()
    if args.verify_plan:
        target = json.loads((args.verify_plan / "target.json").read_text())
        verify_bundle(Path(target["bundle"]), expected_manifest_sha256=target["manifest_sha256"])
    else:
        package_release(args.directory, args.revision or "")
