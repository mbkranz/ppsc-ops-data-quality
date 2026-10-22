# Build, deploy and run operational validation

This closes the repository's packaging and job-entry-point gaps on PR #6. AWS
acceptance is a separate, still-open step: no deployment or live run has been
performed from this workspace.

## Reference review and decisions

Reviewed the actual repositories, rather than treating the older survey v2 branch
as `ppsc-survey-v2`:

| Reference | Reviewed revision | Reuse | Do not carry forward |
| --- | --- | --- | --- |
| [ppsc-survey-v2](https://github.com/mbkranz/ppsc-survey-v2/tree/f54ea3f70701360915ded4183207452c5b289469) | `f54ea3f` | Glue 5.0 hosting, standard IAM credentials, explicit job configuration | Exported get-job response fields, ten-worker default, legacy package ZIPs and independently pinned job dependencies |
| [ppsc-nioccs](https://github.com/mbkranz/ppsc-nioccs/tree/7cd088f708f83afe7e2b7b6cd226bc8b06fd9570) | `7cd088f` | STS account selection, environment assertion, staged artifacts, explicit deployment plan, separate build and deploy | Placeholder processing body; incomplete environment mapping; `scripts/deploy.py` references `config/glue.yaml`, absent from the reviewed tree, while committed job config lives under `glue/config/` |

Use Glue 5.0's CPython 3.11/Linux driver. Athena executes the SQL; the driver does
not create a Spark session or load the lake into a DataFrame. Python Shell 3.9 is
incompatible with this project's Python/GX requirements. Two G.1X workers are an
initial hosting choice, subject to measurement. This is not a Spark migration.

The installed `ppsc-dq validate` command and Glue script call the same packaged
`runtime.job.validate_athena`. Python suite builders remain authoritative. The
example script delegates to that command. Configuration, credentials, rendered
plans and validation evidence remain outside Git.

Poe owns uv, Git, AWS and release operations. Python assembles/verifies artifact
hashes and renders payloads; it does not wrap CLI invocations. DVC is not added:
this release is one small sequence with no shared intermediate build DAG. If a
real dependency graph emerges, DVC can track the same artifacts without changing
this runtime or deployment contract.

## Implemented and remaining work

| Area | Repository addition | Status / completion criterion |
| --- | --- | --- |
| Athena entry point | `ppsc-dq validate`, shared `runtime/job.py` | Implemented; placeholder bindings rejected before connection |
| Dependency packaging | `build-release`, `package_release.py`, manifest with source/lock/artifact/wheel hashes | Implemented; full wheel download/install is a Python 3.11 CI gate |
| Installed runtime | `smoke-release`, Python 3.11 CI | Install only bundled wheels with no index; dependency check plus installed preview/demo |
| Release publication | Manual exact-tag `release.yml` | Verify existing tag, check/build/smoke, upload bundle, publish GitHub release |
| Deployment | `plan-deployment`, `deploy` | STS account selection; explicit create/update; checksums reverified before upload |
| Glue execution | `validate_history.py`, `run-glue`, `glue-status` | Hash-check runtime configuration; verify deployed job matches plan; retain run ID |
| Discovery | `render-report-catalog`, `register-report-catalog` | Bind existing DDL; submit two separate statements; wait for both Athena executions |
| Source acceptance | Actual catalog columns, temporal semantics and settled event | **Open:** data owner confirms bindings, types, deletion and timezone conventions |
| AWS acceptance | Dev/prod settings, role, buckets, workgroup, network and catalog access | **Open:** cloud architect supplies verified environment values; run acceptance below |
| Scheduling | Trigger/schedule | **Open:** establish accepted run selection and cadence after the first successful dev run |

## Build and release

Requires uv, Git and Python 3.11. AWS operations additionally require AWS CLI v2,
`jq` and normal AWS credentials. Graphviz is required for the repository checks.

```bash
uv sync --locked --python 3.11
uv run --locked poe check
uv run --locked poe preview
uv run --locked poe demo
# Commit source changes first. Start with no existing build/release directory.
uv run --locked poe build-release
uv run --locked poe smoke-release
```

The builder exports production dependencies from `uv.lock` with hashes, downloads
binary CPython 3.11 wheels for Glue-compatible Linux platforms, and adds exactly
one project wheel. It creates `build/release/bundle/` containing:

- `dependencies.gluewheels.zip`: project plus all runtime dependencies;
- `validate_history.py`: the minimal driver;
- `requirements.txt`: the hashed dependency export;
- `manifest.json`: full Git revision, runtime, lock hash and all artifact/wheel hashes.

Every wheel must be available for the target. Missing/incompatible binaries fail
the build instead of falling back to compilation. The smoke environment has no
package-index access during installation. It verifies the packaged CLI, source
imports, native GX execution and report generation using synthetic data. It does
not reproduce Glue's preinstalled libraries, bootstrap or network environment.

The dependency ZIP uses AWS's documented `.gluewheels.zip` format with
`--additional-python-modules` and `--python-modules-installer-option=--no-index`.
See [AWS Python dependency packaging](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-python-libraries.html).

For publication, create an appropriate existing `v*` tag on the reviewed commit,
then dispatch **Glue release** with that tag. Deployment uses those downloaded
bundle files without rebuilding. Dev and prod receive the same bundle hash.
The deployment manifest's content hash is the S3 release directory; different
build bytes get a different directory even for the same source revision.

## Plan and deploy

Populate `glue/environments.local.toml` from the example. Each account must map
uniquely to dev or prod. The role must belong to that account. Use existing
artifact buckets and execution roles; this project does not provision them.

```bash
uv run poe plan-deployment --environment dev --output build/deployment-dev
# Review target.json, create-job.json/update-job.json and uploads.tsv.
uv run poe deploy --plan build/deployment-dev --operation create
# Existing job: use --operation update explicitly.
```

Planning reads STS, verifies the supplied bundle and writes local payloads. It
uploads nothing and changes no job. To render entirely offline, invoke
`python -m scripts.plan_deployment` with the same arguments plus `--account`,
`--config` and `--bundle`; this does not verify a live identity.

Deployment rechecks the active account and local checksums, uploads only the
manifest's files with the manifest last, and calls the chosen Glue API. No
catch-all create-on-update-error fallback is used. Release upload completion is
not equivalent to a successfully updated job: retain the command result and run
acceptance. Retry uses the same hash-addressed artifact paths. Updating a job
replaces the managed job settings; include any required VPC connections or
organization-specific security configuration in the renderer before acceptance.

## Configure, run and inspect

Populate `params.local.toml` from `params.example.toml` and independently verify:
source databases/physical types; SCD2 interval and deletion semantics; the
triggering Survey Result; BEFORE < execution < settled AFTER; rollup effective
point; and business timezone/Flow run date. An effective timestamp does not pin
an Iceberg physical version. Preserve explicit physical source pins upstream or
materialized run inputs when immutable data replay is required.

Upload the run configuration to a unique S3 object. Calculate its SHA256 locally
(`sha256sum params.local.toml`), then submit that exact hash:

```bash
aws s3 cp params.local.toml s3://YOUR_CONFIG_BUCKET/quality-runs/RUN_ID.toml
uv run poe run-glue --plan build/deployment-dev \
  --config-uri s3://YOUR_CONFIG_BUCKET/quality-runs/RUN_ID.toml \
  --config-sha256 YOUR_64_CHARACTER_SHA256
uv run poe glue-status --plan build/deployment-dev --run-id RETURNED_JOB_RUN_ID
```

`run-glue` compares the deployed script and dependency arguments with the planned
release before submission. Submission is asynchronous. Repeat status inspection
until terminal and inspect the reported CloudWatch log group on failure. Do not
interpret a returned job-run ID as success. Automatic job retries and bookmarks
are disabled. Each invocation creates a new report UUID; retries are distinct
runs rather than overwriting earlier evidence.

The driver checks configuration bytes before querying. It records config URI and
hash, source revision, manifest URI, Glue job and Glue run ID in report metadata.
It publishes native JSON, HTML/assets and one Parquet row per expectation. A
completed validation with failed expectations exits 1; execution/publishing errors
exit 2. Both are Glue FAILED, distinguished by native results and the manifest.
Only a successful validation exits 0. Startup, configuration or connection errors
before validation setup have CloudWatch evidence but may have no report manifest;
partial S3 publication has no completion marker. Do not treat its visible Parquet
objects as a completed run without checking the manifest.

## Register discovery tables

Use an existing report database. Render from the same runtime report prefix:

```bash
uv run poe render-report-catalog --config params.local.toml \
  --database quality_reports --first-run-date 2026-10-21 --output build/catalog-dev
uv run poe register-report-catalog --plan build/deployment-dev --catalog build/catalog-dev
# For each returned query ID, require SUCCEEDED:
aws athena get-query-execution --query-execution-id RETURNED_QUERY_ID \
  --query 'QueryExecution.Status'
```

DDL points only at the two Parquet prefixes. Partition projection removes the
need for a crawler or per-run partition updates. `IF NOT EXISTS` does not reconcile
an already incompatible table schema; inspect existing Glue table definitions
before declaring acceptance. HTML/JSON remain archived under `runs/`.

## Live acceptance and promotion

1. Cloud architect provides dev/prod account IDs, region, artifact/config/report
   locations, Glue execution role, Athena workgroup/staging location and report
   database. The deployment identity needs scoped artifact writes, Glue job
   create/update/start/inspect and PassRole for the declared execution role.
2. Execution role needs config/bundle reads, Athena execution, Glue catalog reads,
   lake/report/staging S3 access and applicable KMS/Lake Formation permissions.
   Verify endpoints/egress and CloudWatch logging in the actual execution network.
   Report catalog creation needs its own catalog/DDL permissions.
3. Build/install the Python 3.11 bundle in CI and review the synthetic results.
   Deploy dev and run a known settled event with an independently expected outcome.
4. Require Glue terminal state, the matching report completion manifest, both
   native validation results, usable Data Docs assets and discoverable Parquet.
   Verify unique `(run_id, validation_definition_name, expectation_index)` and
   counts against native results; verify source query and Glue/config provenance.
5. Exercise a known data failure and a configuration-hash failure in dev. Confirm
   Glue FAILED, the correct evidence/absence of completion marker, and no silent
   success after report publication errors.
6. Retain accepted run IDs and exact bundle manifest. Deploy the **same** bundle
   to prod with a separately reviewed prod plan and run configuration. Rollback
   renders a new plan from a previously accepted bundle and updates the job;
   existing evidence is retained. Resolve cadence and population selection before
   enabling any scheduled trigger.

Outstanding live inputs are deployment settings and verified data bindings, not
additional runtime abstractions. No AWS deploy/run result is claimed by local
checks or synthetic tests.
