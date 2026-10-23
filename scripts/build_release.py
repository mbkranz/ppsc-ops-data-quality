"""Build locally on the supported Linux producer or prepare an exact commit in Actions."""

import argparse
import io
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Literal
from zipfile import ZipFile

import requests
import yaml
from github import Auth, Github
from github.Repository import Repository
from github.WorkflowRun import WorkflowRun
from packaging.version import Version
from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.github_release import REPOSITORY, github_token
from scripts.verify_release_checkout import verify_checkout

WORKFLOW = "prepare-release.yml"
LOCK_ARTIFACT = "prepared-release-lock"
FINAL_STAGE = "bundle"
SMOKE_TASKS = ("smoke-release",)


class BuildRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: Literal["auto", "local", "github"] = "auto"
    workflow_ref: str = Field(default="main", min_length=1)
    remote: str = Field(default="release", pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    timeout: int = Field(default=3600, ge=1, le=86400)


class BuildResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: Literal["local", "github"]
    status: Literal["complete"] = "complete"
    lock: str = "dvc.lock"
    revision: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    run_id: int | None = Field(default=None, gt=0)
    run_url: str | None = None

    @model_validator(mode="after")
    def validate_remote_evidence(self):
        evidence = (self.revision, self.run_id, self.run_url)
        if self.backend == "github" and any(value is None for value in evidence):
            raise ValueError("A completed remote build requires its source revision and exact run")
        if self.backend == "local" and any(value is not None for value in evidence):
            raise ValueError("Local builds do not claim remote run evidence")
        return self


def compatible_producer() -> bool:
    """The OS alone does not establish producer compatibility."""
    if platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"}:
        return False
    libc, version = platform.libc_ver()
    if libc != "glibc" or not version or Version(version) < Version("2.34"):
        return False
    if sys.version_info[:3] != (3, 11, 17):
        return False
    try:
        import pip

        version = subprocess.check_output(["uv", "--version"], text=True).split()[1]
        return version == "0.12.23" and pip.__version__ == "25.3"
    except (ImportError, FileNotFoundError, subprocess.CalledProcessError, IndexError):
        return False


def select_backend(
    request: BuildRequest, *, compatible: bool, in_actions: bool
) -> Literal["local", "github"]:
    if request.backend == "local" or in_actions:
        if not compatible:
            raise ValueError(
                "Local build requires Linux x86_64, Python 3.11.17, uv 0.12.23 and pip 25.3"
            )
        if in_actions and request.backend == "github":
            raise ValueError("Actions must build directly; recursive dispatch is disabled")
        return "local"
    return "github" if request.backend == "github" or not compatible else "local"


def build_local(*, root: Path) -> BuildResult:
    if not compatible_producer():
        raise ValueError("Run local preparation in the pinned Linux producer environment")
    subprocess.run(["dvc", "repro", "dvc.yaml"], cwd=root, check=True)
    for task in SMOKE_TASKS:
        subprocess.run(["poe", task], cwd=root, check=True)
    return BuildResult(backend="local")


def wait_for_build(run: WorkflowRun, *, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    print(f"Preparing release: {run.html_url}", flush=True)
    while True:
        run.update()
        if run.status == "completed":
            if run.conclusion != "success":
                raise ValueError(f"Release preparation ended in {run.conclusion}: {run.html_url}")
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                f"Preparation is still running; inspect {run.html_url} before retrying"
            )
        time.sleep(min(5, remaining))


def read_handoff(data: bytes, *, revision: str) -> bytes:
    """Read two named files without extracting arbitrary archive paths."""
    with ZipFile(io.BytesIO(data)) as archive:
        if sorted(archive.namelist()) != ["dvc.lock", "source-revision.txt"]:
            raise ValueError("Expected only dvc.lock and source-revision.txt in build handoff")
        if any(item.file_size > 1024 * 1024 for item in archive.infolist()):
            raise ValueError("Build handoff exceeds the lockfile size limit")
        if archive.read("source-revision.txt").decode().strip() != revision:
            raise ValueError("Build handoff belongs to another source revision")
        lock = archive.read("dvc.lock")
    document = yaml.safe_load(lock)
    if not isinstance(document, dict) or FINAL_STAGE not in document.get("stages", {}):
        raise ValueError("Build handoff has no final release stage")
    return lock


def restore_build(
    lock: bytes, *, root: Path, revision: str, original_lock: bytes, remote: str
) -> None:
    """Retain a reviewable lock only after successful, verified final-artifact retrieval."""
    verify_checkout(revision, root=root)
    path = root / "dvc.lock"
    if path.read_bytes() != original_lock:
        raise ValueError("Local lock changed while the remote build was running")
    definition = yaml.safe_load((root / "dvc.yaml").read_text(encoding="utf-8"))
    document = yaml.safe_load(lock)
    if set(document["stages"]) != set(definition["stages"]):
        raise ValueError("Returned lock must describe exactly the declared release graph")
    for name, stage in definition["stages"].items():
        declared = [next(iter(item)) if isinstance(item, dict) else item for item in stage["outs"]]
        if [item["path"] for item in document["stages"][name]["outs"]] != declared:
            raise ValueError("Returned lock output differs from the declared release graph")
    # Stage retrieval in a separate directory: a failed transfer cannot replace local outputs.
    with tempfile.TemporaryDirectory(prefix="ppsc-release-") as temporary:
        destination = Path(temporary)
        (destination / ".dvc").mkdir()
        for name in ("config", "config.local"):
            source = root / ".dvc" / name
            if source.exists():
                shutil.copy2(source, destination / ".dvc" / name)
        shutil.copy2(root / "dvc.yaml", destination / "dvc.yaml")
        (destination / "dvc.lock").write_bytes(lock)
        transfer_env = {**os.environ, "DVC_NO_ANALYTICS": "1"}
        subprocess.run(
            ["dvc", "config", "core.no_scm", "true"], cwd=destination, check=True, env=transfer_env
        )
        subprocess.run(
            ["dvc", "remote", "modify", "--local", remote, "verify", "true"],
            cwd=destination,
            check=True,
            env=transfer_env,
        )
        subprocess.run(
            ["dvc", "pull", FINAL_STAGE, "-r", remote],
            cwd=destination,
            check=True,
            env=transfer_env,
        )
        verify_checkout(revision, root=root)
        if path.read_bytes() != original_lock:
            raise ValueError("Local lock changed during artifact retrieval")
        outputs = document["stages"][FINAL_STAGE]["outs"]
        for output in outputs:
            relative = Path(output["path"])
            if relative.is_absolute() or ".." in relative.parts or "\\" in output["path"]:
                raise ValueError("Final artifact path must stay inside the checkout")
            source, target = destination / relative, root / relative
            if not target.resolve().is_relative_to(root.resolve()):
                raise ValueError("Final artifact destination escapes the checkout")
            target.parent.mkdir(parents=True, exist_ok=True)
            if os.name == "nt" and target.exists():
                subprocess.run(["dvc", "unprotect", relative.as_posix()], cwd=root, check=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                staged = Path(stream.name)
            try:
                shutil.copy2(source, staged)
                staged.replace(target)
            finally:
                staged.unlink(missing_ok=True)
        path.write_bytes(lock)


def build_github(
    request: BuildRequest, *, root: Path, repository: Repository, http: requests.Session
) -> BuildResult:
    revision = verify_checkout(root=root)
    original_lock = (root / "dvc.lock").read_bytes()
    # Resolving through GitHub requires this exact source commit to have been pushed.
    if repository.get_commit(revision).sha != revision:
        raise ValueError("Push the selected source commit before remote preparation")
    run = repository.get_workflow(WORKFLOW).create_dispatch(
        ref=request.workflow_ref, inputs={"revision": revision}, throw=True, return_run_details=True
    )
    wait_for_build(run, timeout=request.timeout)
    artifacts = [
        item for item in run.get_artifacts() if item.name == LOCK_ARTIFACT and not item.expired
    ]
    if len(artifacts) != 1 or artifacts[0].size_in_bytes > 1024 * 1024:
        raise ValueError("Expected one unexpired lock handoff from the selected run")
    response = http.get(artifacts[0].archive_download_url, timeout=60)
    response.raise_for_status()
    lock = read_handoff(response.content, revision=revision)
    restore_build(
        lock, root=root, revision=revision, original_lock=original_lock, remote=request.remote
    )
    return BuildResult(backend="github", revision=revision, run_id=run.id, run_url=run.html_url)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["auto", "local", "github"], default="auto")
    parser.add_argument("--workflow-ref", default="main")
    parser.add_argument("--remote", default="release")
    parser.add_argument("--timeout", type=int, default=3600)
    request = BuildRequest(**vars(parser.parse_args()))
    backend = select_backend(
        request,
        compatible=compatible_producer(),
        in_actions=os.environ.get("GITHUB_ACTIONS") == "true",
    )
    root = Path.cwd()
    if backend == "local":
        result = build_local(root=root)
    else:
        token = github_token()
        with Github(auth=Auth.Token(token)) as github, requests.Session() as http:
            http.headers.update(
                {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            )
            result = build_github(
                request, root=root, repository=github.get_repo(REPOSITORY), http=http
            )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
