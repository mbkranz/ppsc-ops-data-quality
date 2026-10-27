"""Exercise native Poe/DVC publication against isolated Git and DVC stores."""

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def git(root, *arguments):
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


def test_reproducible_build_and_verified_fresh_publication(tmp_path):
    source = Path(__file__).resolve().parents[1]
    root = tmp_path / "snapshot"
    root.mkdir()
    # Include pending implementation files as well as committed files when run locally.
    files = git(source, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    for name in files:
        path = source / name
        if path.is_file():
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    env = os.environ.copy()
    env["PATH"] = str(source / ".venv-release/bin") + os.pathsep + env["PATH"]
    producer = source / ".venv-release"
    if not producer.exists():
        producer = Path(sys.executable).parent.parent
    env["UV_PYTHON"] = "3.11.17"
    env["VIRTUAL_ENV"] = str(producer)
    env["UV_PROJECT_ENVIRONMENT"] = str(producer)
    for key in list(env):
        if key.startswith("AWS_"):
            env.pop(key)
    env["AWS_EC2_METADATA_DISABLED"] = "true"
    compatibility = subprocess.run(
        [
            str(producer / "bin/python"),
            "-c",
            "from scripts.build_release import compatible_producer; raise SystemExit(0 if compatible_producer() else 1)",
        ],
        cwd=source,
        env=env,
        text=True,
        capture_output=True,
    )
    if compatibility.returncode:
        pytest.skip(
            "Release integration requires the prepared Linux tools: Python 3.11.17, uv 0.12.23, pip 25.3"
        )

    def run(*command, cwd=root, success=True):
        result = subprocess.run(
            command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if success:
            assert result.returncode == 0, result.stdout
        else:
            assert result.returncode != 0, result.stdout
        return result.stdout

    def dvc(*args, cwd=root, success=True):
        return run(str(source / ".venv-release/bin/dvc"), *args, cwd=cwd, success=success)

    run("poe", "build-release", "--backend", "local")
    wheel = next((root / "build/release/project").glob("*.whl"))
    original = wheel.read_bytes()
    stale = root / "build/lib/ppsc_ops_data_quality/deleted.py"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("# stale build output must not enter the wheel\n")
    dvc("repro", "wheel", "--force", "--no-run-cache")
    assert hashlib.sha256(wheel.read_bytes()).digest() == hashlib.sha256(original).digest()
    dvc("status", "wheel", "--quiet")

    # AWS target changes cannot invalidate the environment-independent producer.
    target = root / "glue/job.yaml"
    before = target.read_text()
    target.write_text(before + "\n# binding-only change\n")
    dvc("status", "wheel", "--quiet")
    target.write_text(before)
    for name in ["README.md", "src/ppsc_ops_data_quality/__init__.py"]:
        path = root / name
        before = path.read_text()
        path.write_text(before + "\n# producer change\n")
        dvc("status", "wheel", "--quiet", success=False)
        path.write_text(before)
    dvc("status", "wheel", "--quiet")
    # Machine-local bytecode cannot become part of a portable source identity.
    compiled = root / "src/__pycache__/producer-host.pyc"
    compiled.parent.mkdir(parents=True, exist_ok=True)
    compiled.write_bytes(b"host-specific bytecode")
    dvc("status", "wheel", "--quiet")
    # Publication-only task edits must not invalidate the application wheel.
    taskfile = root / "poe_tasks.yaml"
    task_before = taskfile.read_bytes()
    taskfile.write_bytes(task_before + b"\n# publication-only change\n")
    dvc("status", "wheel", "--quiet")
    taskfile.write_bytes(task_before)

    # A real version/lock edit exports identical runtime requirements and reuses downloads.
    metadata = root / "pyproject.toml"
    lockfile = root / "uv.lock"
    metadata_before, lock_before = metadata.read_bytes(), lockfile.read_bytes()
    download_before = (root / "build/release/dependencies").stat().st_mtime_ns
    metadata.write_text(metadata.read_text().replace('version = "0.1.0"', 'version = "0.1.1"'))
    # A new lock may need registry metadata for other supported Python/platform splits.
    run("uv", "lock")
    dvc("repro", "dvc.yaml")
    assert (root / "build/release/dependencies").stat().st_mtime_ns == download_before
    metadata.write_bytes(metadata_before)
    lockfile.write_bytes(lock_before)
    dvc("repro", "dvc.yaml")
    assert wheel.read_bytes() == original

    # Exercise the producer with its parent directory present and the sole ZIP removed.
    archive = root / "build/release/bundle/dependencies.gluewheels.zip"
    archive_before = archive.read_bytes()
    archive.unlink()
    dvc("repro", "--single-item", "--force", "--no-run-cache", "bundle")
    assert archive.read_bytes() == archive_before
    git(root, "add", ".")
    git(root, "commit", "-m", "Prepared exact snapshot")
    revision = git(root, "rev-parse", "HEAD")
    origin = tmp_path / "origin.git"
    git(root, "clone", "--bare", str(root), str(origin))
    git(root, "remote", "add", "origin", str(origin))
    remote = tmp_path / "dvc-remote"
    dvc("remote", "add", "--local", "release", str(remote))
    dvc("remote", "modify", "--local", "release", "verify", "true")

    dvc("status", "dvc.yaml", "--quiet")
    dvc("push", "dvc.yaml", "-r", "release")
    retrieved = tmp_path / "retrieved"
    git(root, "clone", "--no-local", "--quiet", str(origin), str(retrieved))
    git(retrieved, "checkout", "--detach", revision)
    dvc("cache", "dir", "--local", ".dvc/verification-cache", cwd=retrieved)
    dvc("remote", "add", "--local", "release", str(remote), cwd=retrieved)
    dvc("remote", "modify", "--local", "release", "verify", "true", cwd=retrieved)
    dvc("pull", "dvc.yaml", "-r", "release", cwd=retrieved)
    dvc("status", "dvc.yaml", "--quiet", cwd=retrieved)
    assert next((retrieved / "build/release/project").glob("*.whl")).read_bytes() == original
    run("poe", "publish-release")
    final = tmp_path / "final-only"
    git(root, "clone", "--no-local", "--quiet", str(origin), str(final))
    dvc("remote", "add", "--local", "release", str(remote), cwd=final)
    dvc("remote", "modify", "--local", "release", "verify", "true", cwd=final)
    dvc("pull", "bundle", "-r", "release", cwd=final)
    run(
        str(source / ".venv-release/bin/python"),
        "-c",
        f"from scripts.release_artifact import verify_release; verify_release({revision!r})",
        cwd=final,
    )
    assert not (final / "build/release/project").exists()
    assert not (final / "build/release/dependencies").exists()
    assert not (final / "build/benchmark").exists()

    # A separate clean cache must reject corruption in the canonical store.
    obj = next(
        path
        for path in remote.rglob("*")
        if path.is_file()
        and path.read_bytes()
        == (root / "build/release/bundle/dependencies.gluewheels.zip").read_bytes()
    )
    obj.chmod(0o644)
    obj.write_bytes(b"corrupt" + original[7:])
    fresh = tmp_path / "corrupt-retrieval"
    git(root, "clone", "--quiet", str(origin), str(fresh))
    dvc("remote", "add", "--local", "release", str(remote), cwd=fresh)
    dvc("remote", "modify", "--local", "release", "verify", "true", cwd=fresh)
    dvc("pull", "bundle", "-r", "release", cwd=fresh, success=False)
