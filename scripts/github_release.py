"""Verify GitHub release evidence using explicit SDK calls."""

import argparse
import os
import subprocess
from pathlib import Path
from typing import Literal

from github import Auth, Github
from github.Repository import Repository
from pydantic import BaseModel, ConfigDict, Field

from scripts.verify_release_checkout import verify_checkout, verify_revision

REPOSITORY = "mbkranz/ppsc-ops-data-quality"


class ReleaseCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    release: str | None = Field(default=None, pattern=r"^v[0-9][A-Za-z0-9.+-]*$")


class ReleaseEvidence(ReleaseCheck):
    context: Literal["release-artifacts"] = "release-artifacts"
    state: Literal["success"] = "success"


def github_token() -> str:
    """Use an explicit token or the existing GitHub CLI login; never print it."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise ValueError("Set GH_TOKEN or authenticate with gh auth login") from exc
    if not token.strip():
        raise ValueError("GitHub token is empty")
    return token


def verify_github_release(request: ReleaseCheck, *, repository: Repository) -> ReleaseEvidence:
    """Require evidence for this exact commit, and its published tag when supplied."""
    if request.release:
        release = repository.get_release(request.release)
        if release.draft or release.tag_name != request.release:
            raise ValueError("Release is not published")
        if repository.get_commit(request.release).sha != request.revision:
            raise ValueError("Published release tag differs from the selected commit")
    statuses = repository.get_commit(request.revision).get_combined_status().statuses
    if not any(
        item.context == "release-artifacts" and item.state == "success" for item in statuses
    ):
        raise ValueError("Commit has not passed independent release-artifacts verification")
    return ReleaseEvidence(**request.model_dump())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision")
    parser.add_argument("--release")
    args = parser.parse_args()
    if not args.revision and not args.release:
        parser.error("Supply --revision or --release")
    revision = (
        verify_revision(args.release)
        if args.release
        else verify_checkout(args.revision, root=Path("."))
    )
    if args.revision and revision != args.revision:
        raise ValueError("Release differs from the requested revision")
    request = ReleaseCheck(revision=revision, release=args.release)
    with Github(auth=Auth.Token(github_token())) as github:
        print(
            verify_github_release(request, repository=github.get_repo(REPOSITORY)).model_dump_json()
        )


if __name__ == "__main__":
    main()
