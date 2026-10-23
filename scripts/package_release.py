"""Assemble already built/downloaded wheels into the sole DVC bundle output."""

import argparse
import hashlib
import tomllib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from scripts.glue_wheels import validate_wheels


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def package_release(directory: Path) -> Path:
    """Validate the complete runtime closure; never copy Git files or invoke a CLI."""
    project = tomllib.loads(Path("pyproject.toml").read_text())["project"]
    files = [
        *sorted((directory / "dependencies").iterdir()),
        *sorted((directory / "project").iterdir()),
    ]
    if any(not path.is_file() or path.suffix != ".whl" for path in files):
        raise ValueError("Release inputs must contain only wheels")
    names = [path.name for path in files]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate wheel filenames")
    content = {path.name: path.read_bytes() for path in files}
    validate_wheels(content, application=(project["name"], project["version"]))
    output = directory / "bundle/dependencies.gluewheels.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in sorted(content.items()):
            entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, data)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("build/release"))
    args = parser.parse_args()
    print(package_release(args.directory))
