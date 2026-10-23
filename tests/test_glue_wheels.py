"""Wheel metadata, target compatibility and recursive extra closure checks."""

from io import BytesIO
from zipfile import ZipFile

import pytest

from scripts.glue_wheels import validate_archive, validate_wheels


def wheel(name, *, version="1.0", requirements=(), tag="py3-none-any", metadata_name=None):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        metadata = f"Metadata-Version: 2.1\nName: {metadata_name or name}\nVersion: {version}\nRequires-Python: >=3.11\n"
        metadata += "".join(f"Requires-Dist: {value}\n" for value in requirements)
        archive.writestr(f"{name}-{version}.dist-info/METADATA", metadata)
    return {f"{name}-{version}-{tag}.whl": buffer.getvalue()}


def test_selected_extras_require_their_recursive_dependency_closure():
    wheels = wheel(
        "application",
        requirements=[
            "dependency[feature]>=1; extra == 'runtime'",
            "windows-only; sys_platform == 'win32'",
        ],
    )
    validate_wheels(wheels, application=("application", "1.0"))
    with pytest.raises(ValueError, match="Missing compatible"):
        validate_wheels(wheels, application=("application", "1.0"), extras=("runtime",))
    wheels |= wheel("dependency", requirements=["child>=2; extra == 'feature'"])
    with pytest.raises(ValueError, match="child"):
        validate_wheels(wheels, application=("application", "1.0"), extras=("runtime",))
    wheels |= wheel("child", version="2.0")
    validate_wheels(wheels, application=("application", "1.0"), extras=("runtime",))


@pytest.mark.parametrize("bad", ["duplicate", "platform", "identity", "version", "source"])
def test_invalid_wheel_inputs_are_rejected(bad):
    wheels = wheel("application")
    if bad == "duplicate":
        wheels |= wheel("application", version="2.0")
    elif bad == "platform":
        wheels = wheel("application", tag="cp312-cp312-win_amd64")
    elif bad == "identity":
        wheels = wheel("application", metadata_name="different")
    elif bad == "version":
        wheels = wheel("application", version="2.0")
    else:
        wheels["dependency.tar.gz"] = b"source archive"
    with pytest.raises(ValueError):
        validate_wheels(wheels, application=("application", "1.0"))


def test_archive_rejects_duplicate_entries(tmp_path):
    path = tmp_path / "runtime.gluewheels.zip"
    filename, content = next(iter(wheel("application").items()))
    with ZipFile(path, "w") as archive:
        archive.writestr(filename, content)
        with pytest.warns(UserWarning, match="Duplicate"):
            archive.writestr(filename, content)
    with pytest.raises(ValueError, match="duplicate entries"):
        validate_archive(path, application=("application", "1.0"))
