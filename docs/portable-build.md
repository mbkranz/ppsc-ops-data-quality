# Build from Linux or Windows

## Prepare the tooling environment

Use the same locked release tools on either operating system. The release
launcher and SDK helpers are tooling dependencies; they are not included in the
application wheel or Glue runtime bundle.

```text
uv sync --locked --only-group release --python 3.11.17
uv run --no-sync poe build-release
```

This uses the default `.venv`. An existing `.venv-release` can be selected with
`UV_PROJECT_ENVIRONMENT` before both commands. In PowerShell use
`$env:UV_PROJECT_ENVIRONMENT = ".venv-release"`; in Bash use
`export UV_PROJECT_ENVIRONMENT=.venv-release`.

A compatible Linux x86_64 producer (including WSL) builds and checks the installed
bundle locally. Compatibility includes glibc >=2.34, Python 3.11.17, uv 0.12.23 and pip 25.3.
Windows, macOS and other incompatible environments dispatch `prepare-release.yml`.
An Actions worker builds directly and cannot recursively dispatch.

```text
uv run --no-sync poe build-release --backend local
uv run --no-sync poe build-release --backend github --workflow-ref main
```

## Remote preparation

Commit and push source changes first. Remote preparation requires a clean
checkout and resolves that exact full Git SHA through GitHub. Set `GH_TOKEN`
(or `GITHUB_TOKEN`) with repository contents read and Actions read/write access,
or use an existing `gh auth login`. Authentication tokens are never receipts.

The launcher uses the workflow dispatch response's run ID, waits for that exact
run and reports its URL. Failure, cancellation, timeout, expired handoff or a
mismatched source revision fails the command. Timeout does not cancel the remote
run; inspect its recorded URL before retrying. `--timeout` changes the bounded
wait, and `--remote` selects the locally configured name of the canonical DVC store.

The Linux workflow checks out the requested SHA, prepares pinned tools, reproduces
the four release stages, runs installed offline smoke checks and pushes the graph
to the existing DVC remote. It returns only `dvc.lock` and a source revision marker
as an Actions artifact. Runtime bundles remain in DVC; there is no second artifact
inventory, automatic Git commit, tag, release publication or deployment.

The launcher checks the returned graph against `dvc.yaml`, retrieves the final
bundle in a temporary DVC checkout and checks local source/lock again before
copying results. Failed retrieval preserves the local lock and existing bundle.
Concurrent source/lock edits are rejected. Windows does not attempt to install
Linux wheels or reproduce the Linux stages.

## Review the generated lock, then publish

```text
git diff -- dvc.lock
```

Review and commit the generated lock with the same unchanged source/configuration,
then push that resulting revision. Publication retrieves the entire finalized
graph into an independent cache and performs its existing freshness/installed
checks. Deployment retrieves only the accepted final bundle. Preparation is not
the publication gate, and its source SHA is not a replacement for the final
committed release revision.

Local Linux builds may include uncommitted edits for development. Remote builds
cannot include them. Neither backend acquires real study data or deploys jobs.

## One-time workflow configuration

Install the preparation workflow on the repository default branch before dispatch;
`--workflow-ref` may select another installed branch version. The existing protected
`release` environment supplies `DVC_REMOTE_URL`, `AWS_ROLE_ARN`, `AWS_ACCOUNT_ID`
and `AWS_REGION`, with the corresponding OIDC trust and canonical DVC permissions.
Configure the matching canonical remote locally for verified final-bundle retrieval.
Existing environment approval and retention policies remain applicable.

Linux CI verifies actual release builds and offline installation. Windows CI verifies
the launcher, GitHub gates and actual local DVC handoff with synthetic bytes;
SDK tests use injected clients. Canonical S3/OIDC dispatch and managed Glue/Athena
acceptance require the configured environment and are separate from those checks.

## Live operations

Poe keeps the operational commands: `plan-deployment`, `deploy`, `run-glue`,
`glue-status` and `register-report-catalog`. Planning/application retain their
existing environment preparation. Run/status/catalog use explicit boto3 sessions
and `--profile` (default `data-migration-dev`), validate the plan account and keep
these operations outside DVC.

`run-glue` checks the live job against its planned fields before submission.
`run.json` and `runs/<run_id>.json` retain `job_name`, `status` and the existing `JobRunId` field.
A lost submission response records `status=unknown` and fails the command;
inspect AWS before retrying. Status receipts retain the existing `State`, `Error`, `Started`, `Completed` and `LogGroup` fields, plus the explicit outcome.
`glue-status` exits unsuccessfully for failed terminal states.

Catalog submission reads both statements before making requests and writes
`submission.json` in the rendered catalog directory. It retains each query ID,
including the first when the second fails. `submitted` means both requests were
accepted; inspect both Athena query IDs to establish DDL completion.

Installed smoke keeps fresh query/validation evidence under `build/release/smoke-checks/` and reports the selected directory in its receipt.
