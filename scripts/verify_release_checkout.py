"""Assertions for exact release snapshots; orchestration remains in Poe/CI."""

import argparse
import re
import subprocess
import tomllib
from pathlib import Path

from packaging.version import Version


def _git(*args: str, root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def verify_checkout(expected_sha: str | None = None, *, root=Path(".")) -> str:
    root = Path(root)
    revision = _git("rev-parse", "HEAD", root=root)
    if expected_sha is not None and revision != expected_sha:
        raise ValueError("Checkout does not match the requested release commit")
    if _git("status", "--porcelain", "--untracked-files=all", root=root):
        raise ValueError("Release checkout contains tracked or untracked changes")
    return revision


def release_tag(tag: str, root: Path) -> str:
    """Use a versioned tag, never a branch or an option-like revision."""
    if not re.fullmatch(r"v[0-9]+(?:\.[0-9]+)+(?:[a-zA-Z0-9.+-]*)", tag):
        raise ValueError("Release must be a versioned tag such as v0.2.0")
    version = Version(tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"])
    if Version(tag[1:]) != version:
        raise ValueError("Release tag differs from the application version")
    return tag


def verify_revision(release: str, *, root=Path(".")) -> str:
    root = Path(root)
    release_tag(release, root)
    revision = _git("rev-parse", "--verify", f"refs/tags/{release}^{{commit}}", root=root)
    return verify_checkout(revision, root=root)


def verify_publication(tag: str, *, root=Path(".")) -> str:
    root = Path(root)
    release_tag(tag, root)
    revision = verify_checkout(root=root)
    local = subprocess.run(
        ["git", "-C", str(root), "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"]
    )
    if local.returncode == 0:
        if _git("rev-parse", f"refs/tags/{tag}^{{commit}}", root=root) != revision:
            raise ValueError("Existing local tag targets another commit")
    # Revision verification is the only Git subprocess responsibility here.
    refs = _git(
        "ls-remote", "--tags", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}", root=root
    )
    remote_tags = dict(line.split(maxsplit=1)[::-1] for line in refs.splitlines())
    remote_revision = remote_tags.get(f"refs/tags/{tag}^{{}}", remote_tags.get(f"refs/tags/{tag}"))
    if remote_revision and remote_revision != revision:
        raise ValueError("Existing remote release tag targets another commit")
    return revision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--release")
    group.add_argument("--publish-tag")
    args = parser.parse_args()
    if args.release:
        print(verify_revision(args.release))
    else:
        print(verify_publication(args.publish_tag))


if __name__ == "__main__":
    main()
