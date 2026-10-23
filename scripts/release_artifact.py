"""Verify final-only DVC retrieval against the selected clean Git checkout."""

import hashlib
import re
import subprocess
import tomllib
from pathlib import Path

import yaml
from packaging.specifiers import SpecifierSet

from scripts.glue_wheels import validate_archive

BUNDLE = Path("build/release/bundle/dependencies.gluewheels.zip")


def verify_release(revision: str, *, root: Path = Path(".")) -> Path:
    """Check exact source, committed lock identity and the embedded application."""
    root = root.resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Release revision must be a full Git SHA")
    current = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if current != revision:
        raise ValueError("Checkout differs from requested release revision")
    dirty = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"], text=True
    ).strip()
    if dirty:
        raise ValueError("Release checkout contains tracked or untracked changes")
    output = (root / BUNDLE).resolve()
    if not output.is_relative_to(root) or not output.is_file():
        raise ValueError("Missing final DVC artifact inside selected checkout")
    lock = yaml.safe_load((root / "dvc.lock").read_text())
    matches = [
        item for item in lock["stages"]["bundle"]["outs"] if item["path"] == BUNDLE.as_posix()
    ]
    if len(matches) != 1 or matches[0].get("hash") != "md5":
        raise ValueError("Declare exactly one final bundle in the selected DVC lock")
    with output.open("rb") as stream:
        actual = hashlib.file_digest(stream, "md5").hexdigest()
    if actual != matches[0]["md5"]:
        raise ValueError("Final bundle differs from the selected DVC lock")
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    wheel = validate_archive(output, application=(project["name"], project["version"]))
    if SpecifierSet(wheel.requires_python) != SpecifierSet(project["requires-python"]):
        raise ValueError("Embedded application Python constraint differs from project")
    return output
