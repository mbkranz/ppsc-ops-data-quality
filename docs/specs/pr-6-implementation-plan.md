# PR #6 implementation plan

Status: implemented and verified locally; live AWS acceptance remains open.

Prepared: 2026-10-22.

Source: [PR #6 review comments](https://github.com/mbkranz/ppsc-ops-data-quality/pull/6),
reviewed against commit `c589b1a477a468bef41ca0dafb89655b75295b7e`.

## Direction and agreed decisions

Organize validation code by domain, keep reusable definitions and query primitives
in `core`, and make AWS the normal development workflow. Use composable Ibis
expressions, native GX suite builders, and an explicit runner.

- Retain the name `core`. It contains domain-independent definitions and query
  primitives and imports neither validation domains nor runtime orchestration.
- Use the `data-migration-dev` profile for local AWS development operations.
  Retain synthetic fixtures and credential-free verification in CI.
- Follow the modular runtime in the `ppsc-survey` v2 branch, rather than the
  monolithic script in the separately named `ppsc-survey-v2` repository.
- Move configuration to YAML and simplify Poe independently of DVC adoption.
  Evaluate DVC against a demonstrated deterministic build DAG before adding it.
- Keep credentials, live configuration, and record-level outputs outside Git.
- Preserve duplicate matches, missing parents, assigned NULLs, unchanged prior
  values, existing temporal semantics, and the launch-date row conditions.
- Python suite builders remain authoritative. Serialize the actual registered
  suite immediately before each validation.
- Authored SQL-file execution remains deferred under the existing
  [runtime metadata/comment TODO](../../src/ppsc_ops_data_quality/runtime/TODO.md).

Reference designs reviewed:

- [ppsc-salesforce](https://github.com/mbkranz/ppsc-salesforce/tree/e33ffbce97383ead61f4d16f16cc816723e7b907):
  YAML parameters, thin operational tasks, and deterministic artifact stages.
- [ppsc-survey v2](https://github.com/mbkranz/ppsc-survey/tree/9fd741c049163c8e31368edce7ed9b832344a139):
  separate Glue arguments, resource loading, validation orchestration, and YAML
  job templates. Adapt these responsibilities to Ibis/Athena; retain this
  project's authoritative Python suite builders.

## Dependency findings incorporated into the plan

| Point to tighten | Current dependencies | Required change |
| --- | --- | --- |
| Shared code imports domain logic | GX query registration, Athena preparation, and view publishing reach Account lineage through the domain's `to_sqlglot()`. | Extract compilation and annotation mechanics and pass lineage explicitly through callers. |
| Preview/demo retirement | CLI tests, diagram generation, CI and release workflows, and installed-release smoke checks use preview/demo or their fixtures. | Replace every consumer before deleting production commands and fixture code. |
| DVC evaluation | Requirements export feeds dependency acquisition; the project wheel builds separately; both feed release assembly. Deployment consumes the manifest and hashes. | Evaluate the actual build graph, including revision and toolchain inputs; keep deployment and live runs in Poe. |

## 1. Create the domain package and make lineage explicit

### Tasks

- [x] Replace the flat domain files with
  `account_to_survey_results/{queries,gx,lineage,schemas}.py`.
- [x] Move derivations and comparison builders into `queries.py`, native suite
  builders into `gx.py`, and provenance mappings into `lineage.py`. Preserve
  existing function behavior and query parameters.
- [x] Extract compiler and annotation mechanics from `to_sqlglot()` into
  `core/queries/sql.py`. Preserve tuple normalization, copied metadata,
  projection comments, and query-level provenance.
- [x] Give the compiler an optional keyword-only `projection_lineage` mapping.
  Omitting it compiles without domain annotations.
- [x] Thread the mapping through `query_asset_sql()`,
  `query_batch_definition()`, Athena `prepare_validation()`, and view
  rendering/publishing functions.
- [x] Have domain orchestration explicitly supply `PROJECTION_LINEAGE`. Keep
  run/batch metadata separate from field lineage.
- [x] Update annotation tests to supply lineage explicitly. Retain generic query
  tests without lineage.
- [x] Update imports in runtime, tests, examples, diagrams, and documentation.
  Remove replaced flat modules without retaining duplicate implementations.

### Acceptance

- Account comparisons retain their annotations; unrelated queries receive no
  Account metadata.
- AST copy/dump/load, unknown projections, and metadata-mutation isolation remain
  covered.
- Compilation has one implementation, and shared helpers import no domain code.

## 2. Separate schemas, pure queries, and data access

### Tasks

- [x] Move reusable Account, Contact, Survey Result, and history schemas into
  `core/schemas`.
- [x] Move pure SCD2 snapshot selection and unbound history-relation construction
  into `core/queries`.
- [x] Move `bind_history_tables()`, which accesses a backend catalog, into the
  runtime data-access module.
- [x] Move inferred comparison schemas into the domain package's `schemas.py`.
- [x] Move validation-report schemas alongside reporting.
- [x] Update schema exports and consumers. Domain schema inference may depend on
  query construction; query builders must not import their inferred schemas.
- [x] Keep `core` initializers free of domain and runtime imports.
- [x] Preserve the distinction between validation-input profiles and independently
  verified deployed catalog schemas.

### Acceptance

- Existing source types, snapshot behavior, comparison schemas, and report-DDL
  alignment remain equivalent.
- Importing core definitions performs no data access or domain initialization.
- Schema inference does not create a circular import with query construction.

## 3. Replace preview/demo consumers and simplify entry points

### Consumer migration

| Current consumer | Replacement |
| --- | --- |
| CLI preview tests | Development check compiling Athena comparisons and serializing native suites. |
| CLI demo tests | Synthetic DuckDB integration check using production query builders, adapters, runner, and reporting. |
| Diagram generator and tests | Inferred comparison schemas for ordinary diagrams; existing query builders with explicit illustrative bindings for optional native expression graphs. |
| CI and release workflows | Named compilation and synthetic-validation Poe checks. |
| Installed-release smoke task | The same development checks executed against the installed wheel. |
| README, runtime/report docs, and AGENTS instructions | Updated operational commands and replacement verification commands. |

### Tasks

- [x] Create a development-only script with reusable synthetic fixtures and
  compilation/validation checks. Keep observed fixture values independently
  authored.
- [x] Preserve assertions that baseline suites contain 27 Flow and 24 rollup
  expectations. Synthetic validation with count checks evaluates 28 and 25.
- [x] Preserve synthetic evidence checks: 53 expectation rows, two validation
  summaries, unique expectation identities, native results, registered suites,
  comparison SQL, Data Docs, and the run manifest.
- [x] Remove the diagram generator's dependency on `demo.comparisons()`.
  Ordinary diagrams use inferred comparison schemas. Optional expression graphs
  use the existing builders with explicit illustrative bindings and remain
  unmodified native Ibis graphs.
- [x] Run installed-package checks with the smoke environment's interpreter,
  isolated from checkout imports. Exercise the installed CLI separately,
  including help and invalid-configuration handling.
- [x] Update `smoke-release`, both GitHub workflows, existing tests, and relevant
  documentation before removing production preview/demo commands and `demo.py`.
- [x] Remove package `__main__.py`. Retain `ppsc-dq validate` as the packaged
  callable.
- [x] Make profile-aware Glue submission/status tasks the documented development
  workflow. Keep account/environment checks and allow explicit profile overrides.
- [x] Keep named local profiles out of Glue runtime configuration; Glue uses its
  execution role.
- [x] Retain DuckDB support for synthetic verification. Dependency slimming is
  outside this refactor.
- [x] Update AGENTS verification commands together with their replacements so
  repository instructions continue to name working credential-free checks.

### Acceptance

- Synthetic checks run without AWS credentials.
- Release smoke checks prove installation and execution of the wheel rather than
  accidentally importing checkout code.
- Diagram generation has no synthetic-fixture dependency.
- The documented AWS workflow records the submitted Glue run ID and inspects
  terminal status; submission alone is not treated as successful validation.

## 4. Refactor runtime around explicit inputs

### Tasks

- [x] Use the reviewed `ppsc-survey` v2 organization for Glue argument handling,
  resource loading, and validation orchestration.
- [x] Put Glue arguments/bootstrap in `runtime/glue.py`; keep the deployed driver
  thin.
- [x] Put runtime configuration retrieval and checksum verification in
  `runtime/resources.py`, preserving injectable clients.
- [x] Move shared local/Glue orchestration into `runtime/validation.py`.
- [x] Keep Athena and DuckDB preparation separate and retain the engine-independent
  native GX runner.
- [x] Supply domain query builders, suite builders, and lineage explicitly at
  orchestration.
- [x] Preserve registered-suite serialization, exact Query Asset SQL evidence,
  partial-result retention, connection cleanup, and exit behavior: 0 for success,
  1 for completed validation with failed expectations, and 2 for execution or
  configuration errors at the hosting entry point.
- [x] Keep Python suite builders authoritative when adapting resource loading;
  introduce no Spark initialization for Athena execution.

### Acceptance

- Success, data failure, execution error, publication error, configuration-hash
  mismatch, and cleanup scenarios pass through the revised interfaces.
- Local and Glue entry points use the same validation orchestration.
- Release/configuration provenance and earlier completed results survive errors.

## 5. Migrate configuration and evaluate the release graph

### YAML and operational tasks

- [x] Add YAML support as an explicit dependency rather than relying on a
  transitive installation.
- [x] Migrate runtime and environment configuration together using one loading
  implementation while preserving their separate responsibilities.
- [x] Move configurable Glue settings into a YAML job template. Keep verified live
  settings in ignored local files.
- [x] Preserve typed dates, datetimes, timezone awareness, quoted account IDs, and
  duplicate-key rejection.
- [x] Update deployment planning, report-catalog rendering, Glue temporary
  configuration filenames, ignore patterns, tests, and examples together.
- [x] Keep Poe responsible for operational commands and profile selection.
  Preserve account/environment checks, explicit create/update operations,
  configuration hashes, and bundle verification.
- [x] Do not make the YAML migration depend on a DVC decision.

### DVC evaluation

Evaluate these candidate stages:

| Candidate stage | Explicit inputs | Outputs |
| --- | --- | --- |
| Requirements export | Project metadata, lockfile, export tooling | Hashed requirements |
| Dependency acquisition | Requirements, target Python/platform, downloader version | Verified dependency wheels |
| Project wheel | Source, build metadata, lockfile, build tooling | Project wheel |
| Release assembly | Both wheel sets, driver, requirements, lockfile, explicit revision | Bundle and manifest |

- [x] Verify repeat-build hashes and invalidation after source, lockfile, driver,
  or target changes.
- [x] Make Git revision an explicit input; cached outputs must not silently retain
  another revision.
- [x] Give stages distinct output ownership and account for existing
  fresh-directory requirements.
- [x] Document toolchain assumptions affecting wheel/archive reproducibility.
- [x] Assess whether stage reuse provides practical value beyond the current
  locked build sequence.
- [x] Keep smoke execution as a verification gate. Keep STS lookup, deployment,
  Glue submission, catalog registration, live configuration, and live results
  outside cached build stages.
- [x] Record evidence and an adopt/defer recommendation before adding DVC.

### Acceptance

- YAML configuration produces equivalent runtime inputs and valid Glue SDK
  payloads.
- Integrity, account mismatch, environment mismatch, and role-account checks
  continue to pass.
- Live bindings remain ignored.
- The DVC evaluation has a documented recommendation supported by build evidence.

## 6. Record the expectation-classification TODO

### Tasks

- [x] Inventory expectation classes, check IDs, row conditions, and lineage fields.
- [x] Document independent dimensions for check purpose and provenance kind.
- [x] Include structural, referential, and expected-versus-observed examples.
- [x] Identify classifications derivable from existing lineage and actual metadata
  gaps.
- [x] Defer taxonomy implementation and report-schema changes to a separate work
  item.

### Acceptance

The TODO describes concrete future work without duplicating provenance or
changing suite behavior.

## Implementation order and verification

1. Establish a fresh-install baseline and verify the installed entry point.
2. Complete the domain/core moves and explicit lineage flow in steps 1 and 2.
3. Replace preview/demo consumers before retiring commands in step 3.
4. Complete the YAML migration from step 5.
5. Refactor runtime responsibilities in step 4.
6. Finish the AWS operational workflow and documentation from step 3.
7. Finish the DVC evaluation from step 5.
8. Add step 6's classification TODO during the domain move.

Before retiring existing tasks, run `uv run poe check`, `uv run poe preview`,
and `uv run poe demo`. After migration, run their documented replacement checks,
diagram generation, and installed-release smoke verification. Preserve behavioral
test coverage rather than adding tests that merely mirror file moves.

Live acceptance is a separate gate using `data-migration-dev`: verify actual
catalog types and temporal semantics, execute a settled event through Glue,
inspect terminal status, and verify the matching report manifest, native results,
Data Docs, and Parquet discovery rows. Synthetic results do not establish live
Athena/Glue acceptance.

### Baseline limitations observed during planning

- The installed `ppsc-dq` launcher referenced the removed
  `ppsc_ops_data_quality.run` module. A fresh installation and installed-package
  smoke check are required before relying on that environment.
- The required check, preview, and demo commands were attempted, but the latest
  attempts stopped during dependency resolution because the locked DuckDB wheel
  was unavailable in the local cache and network access was restricted.
- No live AWS acceptance result is claimed by this plan.

## Implementation outcome (2026-10-22)

Implemented the domain/core package move and explicit lineage flow, development-only
compilation/synthetic checks, isolated installed-wheel smoke checks, YAML runtime
and deployment configuration, templated Glue hosting, and the shared modular runtime.
Applied the **PPSC agent design reference** and its `design-python-contracts` skill:
structured runtime requests, verified resources and completed validation outcomes
use Pydantic; computations and GX/SDK execution remain explicit functions with native
expressions/frames. Reference examples were reused without adding another engine.

Reviewed the pinned `ppsc-survey` v2 `runtime/{glue,resources,validation}.py` modules.
The Athena implementation follows those responsibilities, with authoritative Python
suite builders and no Spark initialization. [Release graph evaluation](../release-build-evaluation.md)
records actual repeat/invalidation evidence and the decision to defer DVC.
[Expectation classification TODO](expectation-classification-todo.md) inventories
all 53 optional-count checks, their scope and lineage without changing the taxonomy.

Verification: 97 tests pass on Python 3.11 and 3.12. Added regression coverage
exercises real Poe tasks with a fake AWS CLI and configurable YAML job settings. Checks
cover exact scopes, temporal/NULL/duplicate behavior, SQL annotations, resource
hashes/cleanup, native report retention and account/environment integrity.
The complete CPython 3.11 wheel bundle built and installed without index access.
Its isolated development checks validated 53 expectations, 53 expectation rows,
two summaries and the native JSON/suite/SQL/Data Docs/manifest artifacts.

The operational rehearsal caught a Poe environment-expansion issue; profile flags
are now supplied explicitly to each AWS CLI invocation. Default and overridden
profiles, create/update, hash-pinned submission, retained run ID/status, terminal
failure and pre-write account mismatch were verified against the fake CLI.

No live AWS deployment, Athena query, Glue execution or S3 publication was performed.
This workspace has no AWS CLI or verified ignored dev/prod settings. Complete the
separate live gate with `data-migration-dev` after the cloud/data owners supply
bindings and access. Local synthetic success does not close that gate.
