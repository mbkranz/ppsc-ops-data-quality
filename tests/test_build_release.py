"""Portable routing and exact-run handoff; no GitHub or AWS calls."""

import io
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
import yaml

from scripts import build_release as builds


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "checkout with spaces"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "core.autocrlf", "false")
    (root / "dvc.lock").write_bytes(b"old lock\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "Source")
    return root


def handoff(revision, *, lock=None, extra=None):
    data = io.BytesIO()
    with ZipFile(data, "w") as archive:
        archive.writestr("dvc.lock", lock or yaml.safe_dump({"stages": {builds.FINAL_STAGE: {}}}))
        archive.writestr("source-revision.txt", revision + "\n")
        if extra:
            archive.writestr(extra, "unrelated")
    return data.getvalue()


@pytest.mark.parametrize(
    ("backend", "compatible", "expected"),
    [
        ("auto", True, "local"),
        ("auto", False, "github"),
        ("github", True, "github"),
        ("github", False, "github"),
        ("local", True, "local"),
    ],
)
def test_backend_selection(backend, compatible, expected):
    assert (
        builds.select_backend(
            builds.BuildRequest(backend=backend), compatible=compatible, in_actions=False
        )
        == expected
    )


def test_local_rejects_incompatible_host_and_actions_never_redispatches():
    with pytest.raises(ValueError, match="Local build requires"):
        builds.select_backend(
            builds.BuildRequest(backend="local"), compatible=False, in_actions=False
        )
    with pytest.raises(ValueError, match="recursive dispatch"):
        builds.select_backend(
            builds.BuildRequest(backend="github"), compatible=True, in_actions=True
        )
    with pytest.raises(ValueError, match="Local build requires"):
        builds.select_backend(builds.BuildRequest(), compatible=False, in_actions=True)
    assert builds.select_backend(builds.BuildRequest(), compatible=True, in_actions=True) == "local"


@pytest.mark.parametrize(
    ("system", "machine"), [("Windows", "AMD64"), ("Darwin", "arm64"), ("Linux", "aarch64")]
)
def test_unsupported_hosts_do_not_probe_or_build(system, machine, monkeypatch):
    monkeypatch.setattr(builds.platform, "system", lambda: system)
    monkeypatch.setattr(builds.platform, "machine", lambda: machine)
    probe = Mock(side_effect=AssertionError("must not execute tools"))
    monkeypatch.setattr(builds.subprocess, "check_output", probe)
    assert not builds.compatible_producer()
    probe.assert_not_called()


def test_exact_dispatched_run_is_used_for_handoff(checkout, monkeypatch):
    revision = git(checkout, "rev-parse", "HEAD")
    artifact = SimpleNamespace(
        name=builds.LOCK_ARTIFACT,
        expired=False,
        size_in_bytes=100,
        archive_download_url="https://api.github.com/exact-artifact",
    )
    run = Mock(
        id=42,
        html_url="https://github.com/example/run/42",
        status="completed",
        conclusion="success",
    )
    run.get_artifacts.return_value = [artifact]
    repository = Mock()
    repository.get_commit.return_value.sha = revision
    repository.get_workflow.return_value.create_dispatch.return_value = run
    http = Mock()
    http.get.return_value.content = handoff(revision)
    restore = Mock()
    monkeypatch.setattr(builds, "restore_build", restore)
    result = builds.build_github(
        builds.BuildRequest(), root=checkout, repository=repository, http=http
    )
    assert result.run_id == 42 and result.revision == revision
    repository.get_workflow.return_value.create_dispatch.assert_called_once_with(
        ref="main",
        inputs={"revision": revision},
        throw=True,
        return_run_details=True,
    )
    http.get.assert_called_once_with(artifact.archive_download_url, timeout=60)
    assert restore.call_args.kwargs["original_lock"] == b"old lock\n"


@pytest.mark.parametrize("dirty", ["untracked.txt", "dvc.lock"])
def test_dirty_checkout_never_dispatches(checkout, dirty):
    (checkout / dirty).write_text("changed")
    repository = Mock()
    with pytest.raises(ValueError, match="tracked or untracked"):
        builds.build_github(
            builds.BuildRequest(), root=checkout, repository=repository, http=Mock()
        )
    repository.get_workflow.assert_not_called()


def test_unpushed_revision_never_dispatches(checkout):
    repository = Mock()
    repository.get_commit.side_effect = ValueError("commit is not pushed")
    with pytest.raises(ValueError, match="not pushed"):
        builds.build_github(
            builds.BuildRequest(), root=checkout, repository=repository, http=Mock()
        )
    repository.get_workflow.assert_not_called()


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "timed_out"])
def test_failed_remote_run_is_not_accepted(conclusion):
    run = Mock(status="completed", conclusion=conclusion, html_url="https://github.com/run/42")
    with pytest.raises(ValueError, match=conclusion):
        builds.wait_for_build(run, timeout=1)


def test_remote_timeout_preserves_run_link(monkeypatch):
    clock = iter([0, 2])
    monkeypatch.setattr(builds.time, "monotonic", lambda: next(clock))
    with pytest.raises(TimeoutError, match="https://github.com/run/42"):
        builds.wait_for_build(
            Mock(status="queued", html_url="https://github.com/run/42"), timeout=1
        )


def test_handoff_rejects_another_commit_and_unexpected_archive_paths():
    with pytest.raises(ValueError, match="another source"):
        builds.read_handoff(handoff("a" * 40), revision="b" * 40)
    with pytest.raises(ValueError, match="Expected only"):
        builds.read_handoff(handoff("a" * 40, extra="../escape"), revision="a" * 40)


@pytest.mark.parametrize("corrupt", [False, True])
def test_real_dvc_handoff_restores_final_bytes_or_preserves_local_state(
    checkout, tmp_path, corrupt, monkeypatch
):
    producer = Path(__file__).resolve().parents[1] / ".venv-release"
    binary = producer / ("Scripts" if os.name == "nt" else "bin")
    python = binary / ("python.exe" if os.name == "nt" else "python")
    if not python.exists():
        python = Path(sys.executable)
        binary = python.parent
    monkeypatch.setenv("PATH", str(binary) + os.pathsep + os.environ["PATH"])
    (checkout / "dvc.lock").unlink()

    def dvc(*args):
        subprocess.run(
            [str(python), "-m", "dvc", *args], cwd=checkout, check=True, capture_output=True
        )

    (checkout / ".gitignore").write_text("build/\n")
    dvc("init")
    definition = {
        "stages": {
            builds.FINAL_STAGE: {
                "cmd": "python producer.py",
                "deps": ["producer.py"],
                "outs": ["build/runtime.zip"],
            }
        }
    }
    (checkout / "dvc.yaml").write_text(yaml.safe_dump(definition))
    producer = checkout / "producer.py"
    producer.write_text(
        "from pathlib import Path\np=Path('build/runtime.zip'); p.parent.mkdir(exist_ok=True); p.write_bytes(b'old')\n"
    )
    dvc("repro")
    old_lock = (checkout / "dvc.lock").read_bytes()
    producer.write_text(producer.read_text().replace("b'old'", "b'new'"))
    git(checkout, "add", ".")
    git(checkout, "commit", "-m", "Source awaiting Linux build")
    revision = git(checkout, "rev-parse", "HEAD")
    dvc("repro")
    new_lock = (checkout / "dvc.lock").read_bytes()
    remote = tmp_path / "remote"
    dvc("remote", "add", "--local", "release", str(remote))
    dvc("push", "-r", "release")
    (checkout / "dvc.lock").write_bytes(old_lock)
    output = checkout / "build/runtime.zip"
    output.unlink()
    output.write_bytes(b"old")
    dvc("cache", "dir", "--local", str(tmp_path / "empty-retrieval-cache"))
    if corrupt:
        obj = next(path for path in remote.rglob("*") if path.is_file())
        obj.chmod(0o644)
        obj.write_bytes(b"corrupt")
        with pytest.raises(subprocess.CalledProcessError):
            builds.restore_build(
                new_lock, root=checkout, revision=revision, original_lock=old_lock, remote="release"
            )
        assert (checkout / "dvc.lock").read_bytes() == old_lock
        assert output.read_bytes() == b"old"
    else:
        builds.restore_build(
            new_lock, root=checkout, revision=revision, original_lock=old_lock, remote="release"
        )
        assert (checkout / "dvc.lock").read_bytes() == new_lock
        assert output.read_bytes() == b"new"


def test_local_change_during_build_is_preserved(checkout):
    revision = git(checkout, "rev-parse", "HEAD")
    (checkout / "dvc.lock").write_bytes(b"user edit")
    with pytest.raises(ValueError, match="tracked or untracked"):
        builds.restore_build(
            b"remote lock",
            root=checkout,
            revision=revision,
            original_lock=b"old lock\n",
            remote="release",
        )
    assert (checkout / "dvc.lock").read_bytes() == b"user edit"
