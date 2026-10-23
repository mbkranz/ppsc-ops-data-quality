"""Validate the frozen CPython 3.11/Linux wheel closure without installing it."""

from collections.abc import Mapping
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import compatible_tags, cpython_tags
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version
from pydantic import BaseModel, ConfigDict

PLATFORMS = [
    *(f"manylinux_2_{minor}_x86_64" for minor in range(34, 4, -1)),
    "manylinux2014_x86_64",
    "manylinux2010_x86_64",
    "manylinux1_x86_64",
]
TAGS = set(cpython_tags((3, 11), ["cp311"], PLATFORMS)) | set(
    compatible_tags((3, 11), "cp311", PLATFORMS)
)


class WheelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    filename: str
    distribution: str
    version: str
    requires_python: str
    requirements: list[str]


def read_wheel(filename: str, content: bytes) -> WheelInfo:
    """Check filename tags and embedded identity/requirements for the target runtime."""
    if Path(filename).name != filename or not filename.endswith(".whl"):
        raise ValueError(f"Expected a wheel filename: {filename}")
    name, version, _, tags = parse_wheel_filename(filename)
    if not tags & TAGS:
        raise ValueError(f"Incompatible CPython 3.11/Linux wheel: {filename}")
    with ZipFile(BytesIO(content)) as archive:
        files = [item for item in archive.namelist() if item.endswith(".dist-info/METADATA")]
        if len(files) != 1:
            raise ValueError(f"Expected one METADATA file: {filename}")
        metadata = BytesParser().parsebytes(archive.read(files[0]))
    if (
        canonicalize_name(metadata.get("Name", "")) != name
        or Version(metadata.get("Version", "0")) != version
    ):
        raise ValueError(f"Wheel metadata identity differs from filename: {filename}")
    python = metadata.get("Requires-Python", "")
    if python and "3.11.17" not in SpecifierSet(python):
        raise ValueError(f"Wheel does not support Python 3.11: {filename}")
    return WheelInfo(
        filename=filename,
        distribution=name,
        version=str(version),
        requires_python=python,
        requirements=metadata.get_all("Requires-Dist", []),
    )


def validate_wheels(
    wheels: Mapping[str, bytes], *, application: tuple[str, str], extras: tuple[str, ...] = ()
) -> WheelInfo:
    """Reject duplicate distributions and missing/incompatible runtime requirements."""
    distributions = {}
    for filename, content in wheels.items():
        wheel = read_wheel(filename, content)
        if wheel.distribution in distributions:
            raise ValueError(f"Duplicate wheel distribution: {wheel.distribution}")
        distributions[wheel.distribution] = wheel
    name, version = application
    project = distributions.get(canonicalize_name(name))
    if project is None or Version(project.version) != Version(version):
        raise ValueError("Archive application identity differs from project")
    environment = default_environment() | {
        "python_version": "3.11",
        "python_full_version": "3.11.17",
        "sys_platform": "linux",
        "platform_system": "Linux",
        "platform_machine": "x86_64",
        "os_name": "posix",
        "implementation_name": "cpython",
        "platform_python_implementation": "CPython",
    }
    pending = [(project, frozenset(extras))]
    visited = set()
    while pending:
        wheel, selected = pending.pop()
        key = (wheel.distribution, selected)
        if key in visited:
            continue
        visited.add(key)
        for value in wheel.requirements:
            requirement = Requirement(value)
            if requirement.marker and not any(
                requirement.marker.evaluate(environment | {"extra": extra})
                for extra in {"", *selected}
            ):
                continue
            dependency = distributions.get(canonicalize_name(requirement.name))
            if dependency is None or Version(dependency.version) not in requirement.specifier:
                raise ValueError(f"Missing compatible wheel for {wheel.distribution}: {value}")
            pending.append((dependency, frozenset(requirement.extras)))
    return project


def validate_archive(
    path: Path, *, application: tuple[str, str], extras: tuple[str, ...] = ()
) -> WheelInfo:
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Archive contains duplicate entries")
        return validate_wheels(
            {name: archive.read(name) for name in names}, application=application, extras=extras
        )
