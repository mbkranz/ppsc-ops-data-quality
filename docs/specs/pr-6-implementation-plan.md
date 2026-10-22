# PR #6 implementation plan

Status: planned; implementation has not started.

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

- [ ] Replace the flat domain files with
  `account_to_survey_results/{queries,gx,lineage,schemas}.py`.
- [ ] Move derivations and comparison builders into `queries.py`, native suite
  builders into `gx.py`, and provenance mappings into `lineage.py`. Preserve
  existing function behavior and query parameters.
- [ ] Extract compiler and annotation mechanics from `to_sqlglot()` into
  `core/queries/sql.py`. Preserve tuple normalization, copied metadata,
  projection comments, and query-level provenance.
- [ ] Give the compiler an optional keyword-only `projection_lineage` mapping.
  Omitting it compiles without domain annotations.
- [ ] Thread the mapping through `query_asset_sql()`,
  `query_batch_definition()`, Athena `prepare_validation()`, and view
  rendering/publishing functions.
- [ ] Have domain orchestration explicitly supply `PROJECTION_LINEAGE`. Keep
  run/batch metadata separate from field lineage.
- [ ] Update annotation tests to supply lineage explicitly. Retain generic query
  tests without lineage.
- [ ] Update imports in runtime, tests, examples, diagrams, and documentation.
  Remove replaced flat modules without retaining duplicate implementations.

### Acceptance

- Account comparisons retain their annotations; unrelated queries receive no
  Account metadata.
- AST copy/dump/load, unknown projections, and metadata-mutation isolation remain
  covered.
- Compilation has one implementation, and shared helpers import no domain code.

## 2. Separate schemas, pure queries, and data access

### Tasks

- [ ] Move reusable Account, Contact, Survey Result, and history schemas into
  `core/schemas`.
- [ ] Move pure SCD2 snapshot selection and unbound history-relation construction
  into `core/queries`.
- [ ] Move `bind_history_tables()`, which accesses a backend catalog, into the
  runtime data-access module.
- [ ] Move inferred comparison schemas into the domain package's `schemas.py`.
- [ ] Move validation-report schemas alongside reporting.
- [ ] Update schema exports and consumers. Domain schema inference may depend on
  query construction; query builders must not import their inferred schemas.
- [ ] Keep `core` initializers free of domain and runtime imports.
- [ ] Preserve the distinction between validation-input profiles and independently
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

- [ ] Create a development-only script with reusable synthetic fixtures and
  compilation/validation checks. Keep observed fixture values independently
  authored.
- [ ] Preserve assertions that baseline suites contain 27 Flow and 24 rollup
  expectations. Synthetic validation with count checks evaluates 28 and 25.
- [ ] Preserve synthetic evidence checks: 53 expectation rows, two validation
  summaries, unique expectation identities, native results, registered suites,
  comparison SQL, Data Docs, and the run manifest.
- [ ] Remove the diagram generator's dependency on `demo.comparisons()`.
  Ordinary diagrams use inferred comparison schemas. Optional expression graphs
  use the existing builders with explicit illustrative bindings and remain
  unmodified native Ibis graphs.
- [ ] Run installed-package checks with the smoke environment's interpreter,
  isolated from checkout imports. Exercise the installed CLI separately,
  including help and invalid-configuration handling.
- [ ] Update `smoke-release`, both GitHub workflows, existing tests, and relevant
  documentation before removing production preview/demo commands and `demo.py`.
- [ ] Remove package `__main__.py`. Retain `ppsc-dq validate` as the packaged
  callable.
- [ ] Make profile-aware Glue submission/status tasks the documented development
  workflow. Keep account/environment checks and allow explicit profile overrides.
- [ ] Keep named local profiles out of Glue runtime configuration; Glue uses its
  execution role.
- [ ] Retain DuckDB support for synthetic verification. Dependency slimming is
  outside this refactor.
- [ ] Update AGENTS verification commands together with their replacements so
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

- [ ] Use the reviewed `ppsc-survey` v2 organization for Glue argument handling,
  resource loading, and validation orchestration.
- [ ] Put Glue arguments/bootstrap in `runtime/glue.py`; keep the deployed driver
  thin.
- [ ] Put runtime configuration retrieval and checksum verification in
  `runtime/resources.py`, preserving injectable clients.
- [ ] Move shared local/Glue orchestration into `runtime/validation.py`.
- [ ] Keep Athena and DuckDB preparation separate and retain the engine-independent
  native GX runner.
- [ ] Supply domain query builders, suite builders, and lineage explicitly at
  orchestration.
- [ ] Preserve registered-suite serialization, exact Query Asset SQL evidence,
  partial-result retention, connection cleanup, and exit behavior: 0 for success,
  1 for completed validation with failed expectations, and 2 for execution or
  configuration errors at the hosting entry point.
- [ ] Keep Python suite builders authoritative when adapting resource loading;
  introduce no Spark initialization for Athena execution.

### Acceptance

- Success, data failure, execution error, publication error, configuration-hash
  mismatch, and cleanup scenarios pass through the revised interfaces.
- Local and Glue entry points use the same validation orchestration.
- Release/configuration provenance and earlier completed results survive errors.

## 5. Migrate configuration and evaluate the release graph

### YAML and operational tasks

- [ ] Add YAML support as an explicit dependency rather than relying on a
  transitive installation.
- [ ] Migrate runtime and environment configuration together using one loading
  implementation while preserving their separate responsibilities.
- [ ] Move configurable Glue settings into a YAML job template. Keep verified live
  settings in ignored local files.
- [ ] Preserve typed dates, datetimes, timezone awareness, quoted account IDs, and
  duplicate-key rejection.
- [ ] Update deployment planning, report-catalog rendering, Glue temporary
  configuration filenames, ignore patterns, tests, and examples together.
- [ ] Keep Poe responsible for operational commands and profile selection.
  Preserve account/environment checks, explicit create/update operations,
  configuration hashes, and bundle verification.
- [ ] Do not make the YAML migration depend on a DVC decision.

### DVC evaluation

Evaluate these candidate stages:

| Candidate stage | Explicit inputs | Outputs |
| --- | --- | --- |
| Requirements export | Project metadata, lockfile, export tooling | Hashed requirements |
| Dependency acquisition | Requirements, target Python/platform, downloader version | Verified dependency wheels |
| Project wheel | Source, build metadata, lockfile, build tooling | Project wheel |
| Release assembly | Both wheel sets, driver, requirements, lockfile, explicit revision | Bundle and manifest |

- [ ] Verify repeat-build hashes and invalidation after source, lockfile, driver,
  or target changes.
- [ ] Make Git revision an explicit input; cached outputs must not silently retain
  another revision.
- [ ] Give stages distinct output ownership and account for existing
  fresh-directory requirements.
- [ ] Document toolchain assumptions affecting wheel/archive reproducibility.
- [ ] Assess whether stage reuse provides practical value beyond the current
  locked build sequence.
- [ ] Keep smoke execution as a verification gate. Keep STS lookup, deployment,
  Glue submission, catalog registration, live configuration, and live results
  outside cached build stages.
- [ ] Record evidence and an adopt/defer recommendation before adding DVC.

### Acceptance

- YAML configuration produces equivalent runtime inputs and valid Glue SDK
  payloads.
- Integrity, account mismatch, environment mismatch, and role-account checks
  continue to pass.
- Live bindings remain ignored.
- The DVC evaluation has a documented recommendation supported by build evidence.

## 6. Record the expectation-classification TODO

### Tasks

- [ ] Inventory expectation classes, check IDs, row conditions, and lineage fields.
- [ ] Document independent dimensions for check purpose and provenance kind.
- [ ] Include structural, referential, and expected-versus-observed examples.
- [ ] Identify classifications derivable from existing lineage and actual metadata
  gaps.
- [ ] Defer taxonomy implementation and report-schema changes to a separate work
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
