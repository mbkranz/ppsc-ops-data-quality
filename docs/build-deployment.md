# Build, deploy and run operational validation

## Ownership

uv owns locked tools; DVC owns only deterministic release outputs; Git owns the
unchanged Glue driver, job template, source and finalized locks. Poe exposes
operational commands. Python validates artifacts, renders native payloads and
calls the AWS SDK. Live Athena/GX validation, report publication, STS, deployment,
submission and catalog operations are uncached.

The common CLI/Glue runner, Ibis queries, native GX suites, inclusive
`Completion_Status_Timestamp__c >= 2024-12-16` Flow conditions, missing/prelaunch
profiling, rollup definitions and report formats are unchanged. Glue 5.0 uses a
CPython 3.11/Linux x86_64 driver; Athena executes SQL without initializing Spark.
Exit codes remain 0 for success, 1 for quality failure and 2 for execution or
publication errors. Every invocation creates fresh run evidence.

## Prepare a candidate

Use Linux x86_64, Python **3.11.17**, uv **0.12.23**, locked pip **25.3** and
Hatchling **1.27.0**. Backend dependencies are locked; wheel builds disable
isolation and set `SOURCE_DATE_EPOCH=315532800`. Prepare each environment once:

```bash
uv sync --locked
uv run --no-sync poe check
uv run --no-sync poe check-queries
uv run --no-sync poe check-synthetic
UV_PROJECT_ENVIRONMENT=.venv-release uv sync --locked --only-group release
UV_PROJECT_ENVIRONMENT=.venv-release uv run --no-sync poe build-release
UV_PROJECT_ENVIRONMENT=.venv-release uv run --no-sync poe smoke-release
UV_PROJECT_ENVIRONMENT=.venv-release uv run --no-sync dvc status dvc.yaml --quiet
```

The release graph has four exclusive outputs:

| Stage | Output | Purpose |
| --- | --- | --- |
| `requirements` | `build/release/requirements/requirements.txt` | Hashed locked runtime export excluding development/release tools |
| `dependencies` | `build/release/dependencies/` | Binary-only, hash-checked CPython 3.11 Linux wheels |
| `wheel` | `build/release/project/` | Application wheel |
| `bundle` | `build/release/bundle/dependencies.gluewheels.zip` | Deterministic ZIP containing the application once and its complete wheel closure |

The archive producer validates metadata, target tags and dependency closure,
rejects duplicates/source archives and tolerates an existing output parent.
Deleting only the archive is recoverable. The driver stays in Git and is uploaded
from the selected checkout; it is not copied into a cached build directory.
There is no build manifest, revision-dependent producer or runtime
`release_manifest_uri` argument. Runtime configuration checksums and report
completion manifests remain separate contracts.

The installed smoke uses an isolated interpreter, index-free wheel installation,
dependency checking, installed CLI help/error handling and the synthetic 28 Flow
plus 25 rollup expectations, 53 expectation rows and two validation summaries.
It does not establish managed Glue bootstrap/network compatibility.

## Publish an exact release

Configure the approved remote locally; no bucket or account is invented:

```bash
UV_PROJECT_ENVIRONMENT=.venv-release uv run --no-sync dvc remote add --local release s3://APPROVED_BUCKET/dvc-store/
UV_PROJECT_ENVIRONMENT=.venv-release uv run --no-sync dvc remote modify --local release verify true
```

After tests/smoke and the local freshness gate pass, commit source, configuration,
`uv.lock` and the actual `dvc.lock`, push that exact commit, then push all release
outputs with `UV_PROJECT_ENVIRONMENT=.venv-release uv run --no-sync poe publish-release`.
The task transfers artifacts; it does not create a GitHub release.

Dispatch **Publish prepared release** (`release.yml`) from protected `main`, with
that full `revision` and a matching versioned `release` tag. The workflow uses one
fresh checkout and independent empty cache, enables remote verification, pulls
`dvc.yaml`, checks local `dvc status dvc.yaml --quiet`, runs installed smoke and
checks that locks did not change. It then records commit status `release-artifacts`
and creates the GitHub release at that SHA. Publication contains no `dvc repro`
and fails instead of rebuilding missing/stale artifacts. Protect release tags
and restrict publishers/status writers; a tag by itself is mutable.

The GitHub `release` environment needs approved `DVC_REMOTE_URL`, `AWS_ROLE_ARN`,
`AWS_ACCOUNT_ID`, `AWS_REGION`, OIDC trust and artifact retention. Keep historical
objects until rollback retention is established. A local-remote retrieval test
is not evidence that the canonical S3 remote is populated.

## Retrieve, plan and deploy

Check out the published tag as a detached checkout, resolve its full SHA and
prepare the deployment tools. Verify the GitHub release was published and that
its commit passed `release-artifacts`. Restore only the final archive:

```bash
git checkout --detach vX.Y.Z
revision=$(git rev-parse HEAD)
uv sync --locked --group release
uv run --no-sync dvc remote modify --local release verify true
uv run --no-sync dvc pull bundle -r release
uv run --no-sync poe plan-deployment --revision "$revision" --environment dev --output build/deployment-dev
uv run --no-sync poe deploy --plan build/deployment-dev --operation create
# Use --operation update explicitly for an existing job.
```

Do not run a whole-graph status check after final-only retrieval: its intermediates
are intentionally absent. The planner checks the exact clean checkout, final
bundle MD5 against the selected DVC lock, embedded application/version/Python
metadata, environment/account/role and both native Glue SDK payloads. It reads
`glue/job.yaml` and `glue/scripts/validate_history.py` directly. The plan records
revision, lock digest, runtime tuple and actual driver/archive SHA256 and size.
It performs no AWS writes. A direct planner call with `--account` is an offline
rendering operation; the public task independently checks the release gate and STS.

Populate ignored `glue/environments.local.yaml` from the example. Quote account
IDs. Explicit environment selection permits several environments in one account
while always asserting STS identity and same-account execution roles. Local tasks
default to `--profile data-migration-dev`; overrides remain available. Glue uses
its execution role. Include required VPC/security/job settings in the Git template.

Deployment rechecks identity and local bytes, inspects all immutable destinations,
then conditionally uploads both driver and archive below `releases/<full-sha>/`
before calling the chosen create/update API. Identical bytes are reusable;
conflicting bytes and denied service reads fail. SDK errors propagate. The
compact `deployment.json` receipt retains staged artifacts and activation outcome.
Early identity/local-input failures can occur before a receipt exists.
Rollback checks out an earlier retained release and applies its earlier Git job
settings and retrieved archive without building.

## Run and inspect

Create a versioned runtime YAML from `params.example.yaml`. Confirm actual catalog
columns/types, SCD2 intervals, deletion history, BEFORE < event < settled AFTER,
rollup effective point and timezone/date semantics. Independent source tables
sharing a timestamp do not thereby form an atomic snapshot.

```bash
aws --profile data-migration-dev s3 cp params.local.yaml s3://CONFIG_BUCKET/quality-runs/RUN_ID.yaml
uv run --no-sync poe run-glue --plan build/deployment-dev \
  --config-uri s3://CONFIG_BUCKET/quality-runs/RUN_ID.yaml --config-sha256 EXACT_SHA256
uv run --no-sync poe glue-status --plan build/deployment-dev --run-id RETURNED_JOB_RUN_ID
```

`run-glue` compares deployed command/default arguments with the plan before
submission. Poll status until terminal; run IDs/status files stay under the plan.
The runner preserves exact configuration URI/hash, release revision, source/query
identifiers and Glue execution identity. Reports retain gzip native GX JSON,
complete Data Docs assets, compiled SQL, registered suites and Snappy Parquet with
one row per expectation plus separate validation summaries. Partial publication
has no completion marker; a visible Parquet object is not a completed run.

## Register discovery and accept

```bash
uv run --no-sync poe render-report-catalog --config params.local.yaml \
  --database quality_reports --first-run-date 2026-10-21 --output build/catalog-dev
uv run --no-sync poe register-report-catalog --plan build/deployment-dev --catalog build/catalog-dev
```

Inspect both Athena DDL executions and existing table schemas. Verify terminal
Glue success, expected quality-failure/error behavior, matching native results,
53 synthetic expectation rows/two summaries, complete Data Docs assets and
report completion manifests. Promote the same archive/driver hashes to prod after
dev acceptance. Retain failed-run evidence; retries get fresh run IDs.

Canonical S3 retrieval, environment/role/workgroup/network/catalog bindings,
platform-matched container verification and managed Glue acceptance remain
operational prerequisites. Local synthetic results do not close them.
