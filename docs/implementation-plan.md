# PPSC Ops Data Quality Repository Initiation Plan

**Target repository:** [mbkranz/ppsc-ops-data-quality](https://github.com/mbkranz/ppsc-ops-data-quality)

**Prepared:** October 20, 2026

**Status:** Implementation plan

## 1. Objective and first deliverables

Initiate a small Python repository that runs understandable, repeatable data quality checks against the operational data lake through Athena. Use Ibis to construct reusable relational queries and native Great Expectations (GX) objects to author and execute validations.

The first implementation should produce two concrete deliverables:

1. **A working runtime demonstration:** Account and AccountContactRelation (ACR) state integrity, plus an ACR-to-Account relationship check, over one documented data selection. The run saves native GX results, readable Data Docs, compiled SQL, and enough configuration to explain the selected population.
2. **A demonstration of combined evidence:** reproduce one useful check from an existing Glue job or notebook, then use the Salesforce graph and native metadata to explain, confirm, or improve it. Retain the sources and the intended rule in the committed module.

The first deliverable can proceed while the source job or notebook for the second is being identified. Structural checks alone do not complete the combined-evidence demonstration.

### Starting point

The target GitHub repository exists, is public, and is empty as of October 20, 2026. There is no existing implementation or default-branch content to preserve.

The prior APMP data lake review identified Account, AccountContactRelation, and EventLogFile as documented objects. Begin with Account and ACR. Add Contact or Survey Result only after their physical tables and the chosen use case are confirmed. The current [APMP project directory](https://github.com/mbkranz/ppsc-salesforce/tree/dev/projects/apmp-data-lake) still contains an overview and resource catalog alongside empty Python, parameter, and DVC files; it does not provide the deployed bindings needed by this runner.

Treat the previous Athena/GX sample as a reference. Move only the useful functions and behavioral cases into this package; the Ibis version becomes the maintained query implementation.

## 2. Design decisions

| Decision | Initial implementation |
| --- | --- |
| Package and environment | One installable package, Python 3.12, one `pyproject.toml`, one `uv.lock`. |
| Operational commands | A few visible Poe tasks that call Python entry points, pytest, and Ruff. |
| Configuration | One YAML format: tracked `params.yaml` with placeholders; an ignored local copy selected with `--config`. |
| Physical access | One Athena module for connection settings, inspection, and snapshot-bound source expressions. |
| Relational logic | Ordinary Ibis functions in `batches.py`. |
| Expectations | Native GX suite builders in `gx/`, organized by subject or relationship. |
| Runtime | One explicit runner with a visible list of query/suite pairs. |
| Reports | Native GX results and Data Docs, plus a small console summary and `summary.json`. |
| Authoring evidence | Sources are read when authoring or updating rules. Routine validation imports the committed modules. |
| Extension | Add a named function or subject module when a real check needs it. |

The runtime handoff is:

**Ibis expression → Athena SQL string → GX query asset → whole-query batch → native GX suite.**

Ibis supports Athena and SQL compilation. GX query assets accept SQL strings. GX continues to use the PyAthena SQLAlchemy connection; introducing Ibis does not establish GX/Athena compatibility. The live integration gate remains required. [Ibis Athena documentation](https://ibis-project.org/backends/athena), [GX SQL data documentation](https://docs.greatexpectations.io/docs/core/connect_to_data/sql_data/), [GX compatibility reference](https://docs.greatexpectations.io/docs/help/compatibility_reference/).

### Initial file organization

| Path | Purpose |
| --- | --- |
| `pyproject.toml` | Package definition, dependencies, development group, and Poe task-file reference. |
| `uv.lock` | The resolved dependency combination used by local tests and live acceptance. |
| `.python-version` | Python 3.12. |
| `poe_tasks.yaml` | `inspect`, `validate`, `test`, and `check`. |
| `params.yaml` | Non-sensitive connection placeholders, physical bindings, and output defaults. |
| `.gitignore` | Exclude `.venv/`, `build/`, local configuration, caches, and credentials. |
| `README.md` | Purpose, installation, configuration, commands, batch meanings, and interpreting results. |
| `AGENTS.md` | Short repository-wide coding and scope guidelines. |
| `.github/workflows/ci.yml` | Locked installation, Ruff, and local tests using synthetic data. |
| `src/ppsc_ops_data_quality/__init__.py` | Package marker; no initialization side effects. |
| `src/ppsc_ops_data_quality/config.py` | Load one YAML file and validate the few required settings. |
| `src/ppsc_ops_data_quality/athena.py` | PyAthena/SQLAlchemy settings, catalog inspection, and physical source construction. Also owns the inspection CLI. |
| `src/ppsc_ops_data_quality/batches.py` | Ibis state selection, relationship match counts, and later history expressions. |
| `src/ppsc_ops_data_quality/run.py` | Parse run options, build assets/suites, execute validations, and save outputs. |
| `src/ppsc_ops_data_quality/gx/__init__.py` | Package marker. |
| `src/ppsc_ops_data_quality/gx/account.py` | Account state suite. |
| `src/ppsc_ops_data_quality/gx/account_contact_relation.py` | ACR state suite. |
| `src/ppsc_ops_data_quality/gx/account_contact_relation_to_account.py` | ACR-to-Account relationship suite. |
| `tests/conftest.py` | Small synthetic Account and ACR fixtures. |
| `tests/test_batches.py` | Selected row identities, boundaries, nulls, and parent-match counts. |
| `tests/test_gx.py` | Native suite behavior, serialization, and result/error reporting. |
| `docs/sources.md` | Selected graph bundle, native metadata, feature document, and source jobs/notebooks with revisions and pointers. |
| `docs/implementation-plan.md` | This plan, if retained as repository documentation. |
| `.agents/skills/author-data-quality-checks/SKILL.md` | Short evidence-to-module authoring instructions and a reference to one worked example. |

Add `gx/history.py` and `tests/test_history.py` when history checks are implemented for both objects. That is one real reuse case, not a reason to introduce an expectation factory.

Use this initial organization directly. Do not create empty Contact, Survey Result, backend, adapter, or plugin packages.

### Dependencies

Runtime dependencies should be limited to GX, `ibis-framework[athena]`, `PyAthena[SQLAlchemy]`, SQLAlchemy where imported directly, and PyYAML. The development group adds the Ibis DuckDB extra, pytest, Ruff, and Poe.

The earlier local Ibis probe used 12.0.0. Resolve GX, Ibis, PyAthena, and SQLAlchemy together and record the actual combination in `uv.lock`. A successful Ibis compilation probe is not acceptance of the entire runtime.

Use the standard library for CLI parsing, paths, timestamps, JSON output, and simple configuration checks. Add other dependencies only for an implemented requirement.

## 3. Module contracts

### Configuration

`config.py` loads exactly one selected YAML file. Validate only what the selected operation needs: discovery requires connection settings; inspection of named tables also requires table names; validation and dry-run compilation require the mapped columns and declared types used to construct Ibis expressions. Inspection supplies the physical schema needed to finish those bindings. A small typed structure is sufficient; no configuration inheritance or backend-selection system is needed.

Keep connection settings and table bindings together:

- Region, catalog, database, workgroup, and result S3 location.
- Actual table names for Account and ACR.
- Physical column names and verified types for the columns used by the pilot.
- Local output root.

Support aliases from verified physical columns to the names used by the query functions when necessary. Inspect physical types before aliasing or casting; do not cast incorrect types into compliance with a structural expectation.

Use AWS's existing profile or role credential chain. The local configuration supplies connection settings, not access keys.

Run selection belongs in CLI options and the saved run record:

- Exactly one of `--as-of` or `--current`.
- `--lake-as-of`, interpreted as a timezone-aware physical snapshot timestamp.
- `--include-history` when that capability is implemented.
- `--dry-run`.
- `--config` and `--output`.

For the first live demonstration, supply the two time selections explicitly. A subsequent convenience default may resolve `lake_as_of` once at run start and record it. It must never change between queries in one run.

### Athena source construction

`athena.py` owns a small set of ordinary functions:

| Function | Responsibility |
| --- | --- |
| `sqlalchemy_url(config)` | Build the GX connection URL using the configured PyAthena REST dialect and existing credential chain. |
| `inspect_tables(config)` | Inspect table existence, physical columns/types, DDL, and available Iceberg snapshot metadata. |
| `source_table(binding, lake_as_of)` | Construct a typed Ibis source expression with the explicit physical table and snapshot selection. |

The inspection command may optionally discover tables before bindings are known. Default to schema and table metadata; row previews are optional diagnostics.

Keep Athena-specific `FOR TIMESTAMP AS OF` or `FOR VERSION AS OF` syntax in this module. A SQL-defined Ibis source with an explicit schema can then feed the reusable relational functions. Verify that source construction and compilation do not execute validation data queries.

The dry-run path must work without AWS credentials using supplied schemas. It must preserve the source snapshot clauses in the emitted SQL. Do not silently remove pinning to make offline compilation succeed.

The same `lake_as_of` timestamp selects a physical snapshot independently for each table. It does not prove that the tables belong to a completed coordinated delivery. Record table snapshot IDs when readily available; selecting or managing a lake-wide release is outside the pilot.

[Athena time/version travel](https://docs.aws.amazon.com/athena/latest/ug/querying-iceberg-time-travel-and-version-travel-queries.html), [Ibis SQL-defined relations](https://ibis-project.org/how-to/extending/sql), [PyAthena SQLAlchemy](https://pyathena.dev/v4.1.0/api/sqlalchemy.html).

### Batch construction

`batches.py` accepts Ibis tables and explicit parameters. It performs no credential discovery, connection creation, graph retrieval, or GX execution.

Initial functions:

```python
def state_at(table, effective_date): ...


def current_state(table): ...


def account_reference_counts(acr_state, account_state): ...
```

Make the composition visible in `run.py`:

```python
account_state = state_at(account_history, effective_date)
acr_state = state_at(acr_history, effective_date)

relationship_state = account_reference_counts(
    acr_state,
    account_state,
)
```

The relationship function groups the selected Account rows by ID, counts matches, and left joins the counts to the selected ACR rows. Its output includes each ACR row's identity, reference, and `matching_account_versions`.

Retain descriptive Athena SQL where it is already short and clear. Use Ibis when composition or reuse makes the expression easier to maintain.

### Native GX modules

Each subject module initially exposes:

```python
def build_suite() -> gx.ExpectationSuite: ...
```

A suite should not need an AWS configuration merely to be constructed. Let batch selection establish the population and keep the initial SQL expectations scoped to `{batch}`.

If a later check truly needs an additional physical relation, make the dependency explicit in its query construction. GX batch filtering does not automatically scope an independently named table.

Use native expectations for ordinary column and table checks. Use `UnexpectedRowsExpectation` for the selected relational or conditional failures. Zero returned rows means success by default. [GX SQL expectations](https://docs.greatexpectations.io/docs/core/customize_expectations/use_sql_to_define_a_custom_expectation/).

### Runner

`run.py` owns a direct sequence:

1. Load configuration and resolve one run selection.
2. Construct physical sources and the named Ibis batch expressions.
3. Compile each expression to Athena SQL.
4. Build the explicitly imported native suites.
5. In dry-run mode, save SQL, suite JSON, and the declared run selection, then stop before connecting to AWS.
6. In live mode, verify the selected physical schema, create an ephemeral GX context and SQL datasource, and disable temporary table creation.
7. Create one query asset and whole-query batch definition for each selected query/suite pair.
8. Run the validations and retain data failures separately from execution errors.
9. Save results and build Data Docs.

Use a small explicit list such as `[(name, expression, suite), ...]`. No dynamic module scanning, registration decorators, custom execution engine, or general workflow runner is needed.

Normal execution can use the in-memory native suites. Save GX-serialized JSON and test the round trip; serializing and immediately reloading every suite during every run adds no required behavior.

## 4. Batch and rule contracts

### Populations

| Population | Required selection | Purpose |
| --- | --- | --- |
| State at a date | `valid_from <= d AND (valid_to > d OR valid_to IS NULL)` | Full state under the confirmed half-open temporal convention. |
| Current state | `is_current = TRUE` | Current records in the selected physical snapshot. |
| Version history | All relevant versions in the selected physical snapshot | Version keys, intervals, flags, and overlaps. |
| Relationship | Child and parent states selected at the same effective date, or both selected as current | Reference existence and ambiguity. |

Confirm the interval convention and physical date/timestamp types before interpreting live results. If the deployed table uses a different convention, change the expression and its boundary fixtures together.

Do not add a recent `valid_from` or `loaded_at` filter to a complete-state batch. Unchanged records can have old timestamps and still belong in the selected state.

Start with minimal business filtering. Add test, participant, deletion, withdrawal, record-type, or activity filters only when the selected rule's applicability requires them. Apply child scope and eligible-parent scope deliberately; filtering both sides identically is not automatically correct.

Do not silently deduplicate, choose a single parent, or select a latest version to make integrity failures disappear.

### Initial suites

| Suite | Initial rules |
| --- | --- |
| Account | Required projected batch columns; non-null and nonblank identifier; unique identifier in the selected state. A nonempty-population check only where the pilot contract requires it. |
| AccountContactRelation | The corresponding projected batch structure and selected-state identifier checks. |
| ACR to Account | Each applicable child has a permitted reference and resolves to exactly one selected Account version. Explicitly distinguish missing/blank keys, missing parents, and ambiguous matches. |

The runner's common preflight checks physical table existence, required columns, and types against the configured bindings. Report a mismatch as a preflight error before validation. GX structural assertions describe the selected batch schema; passing a projection check does not prove that the physical input has the expected type. This keeps the initial suite builders independent of connection configuration.

Report relationship violations at child-row grain. A parent count of two is one ambiguous-match finding for a selected child, not two child failures.

### History follow-up

Implement history checks after the first working state/relationship demonstration:

- Valid identifiers and effective interval bounds.
- Current flag consistent with the confirmed open-ended interval convention, including explicit null handling.
- Unique version key only after that key is confirmed. `(id, valid_from)` is a candidate, not a universal assumption about date-grained data.
- No overlapping effective versions for the same identifier.

Check overlaps against all relevant earlier intervals, including open-ended intervals. Comparing only adjacent start times can miss nested overlaps. Recent-ID investigations must retain the necessary predecessor history.

Do not require gapless histories or exactly one current version for every historical ID until deletion and restoration behavior is established.

### Time and provenance

Keep three separate facts:

1. Graph org and revision used to author a rule.
2. SCD2 effective date used to select record versions.
3. Physical Iceberg timestamp or table snapshot IDs used to reproduce the data read.

Use a known completed delivery for the first demonstration and document how completion was established. Neither `MAX(valid_from)` nor `MAX(loaded_at)` is a load-completion test when unchanged rows can be skipped.

## 5. Implementation sequence

### Step 1 — Bootstrap the repository

Because the repository is empty, create a minimal initial main commit so the implementation branch has a base. Then use one draft implementation PR with small, ordered commits.

Add the package skeleton, locked environment, configuration placeholders, short README/AGENTS guidance, and the four Poe commands. Add files when their implementation is ready; avoid placeholder modules for later work.

**Completion criterion:** a fresh checkout installs with `uv sync --locked`, imports the package, and runs the local checks.

The repository is public. Commit code, synthetic fixtures, and non-sensitive example configuration. Real validation rows, Data Docs, and local connection settings stay outside Git and public CI artifacts.

### Step 2 — Prove GX against Athena

Use a small explicit SQL query first so integration and Ibis compilation are separate questions.

1. Confirm the actual Account and ACR table bindings and relevant types.
2. Create the generic GX SQL datasource using `awsathena+rest` and `create_temp_table=False`.
3. Run a native expectation against a table/query asset.
4. Run an `UnexpectedRowsExpectation`.
5. Demonstrate a passing case, an intentional data failure, and a distinguishable query execution error using controlled read-only queries.

**Completion criterion:** real GX results are produced through the configured Athena workgroup and the exact dependency versions are recorded.

Timebox initial integration troubleshooting to roughly 60–90 minutes. If the unexpected-row path alone fails, permit one bounded query-asset/zero-row-count fallback and verify both counts and diagnostics. Record the limitation. If basic datasource execution fails, capture a minimal reproduction and continue the offline work without claiming live acceptance.

### Step 3 — Add the Ibis batch functions

Implement the two state selectors and the parent-match query. Supply the same functions with DuckDB fixture tables in local tests and with Athena-bound sources when compiling live queries.

Compile to the Athena dialect at asset creation. Preserve source snapshot clauses and save readable SQL.

**Completion criterion:** expected selected IDs and parent-match counts are correct for the meaningful fixtures; the compiled query works through the GX/Athena path accepted in Step 2.

Use reference SQL only for a bounded comparison with the prototype. Maintain one implementation of each new query.

### Step 4 — Complete the first runtime demonstration

Add the three initial native suite modules and the explicit runner list. Complete dry-run output, native result saving, error classification, console summary, and Data Docs.

Use one completed data selection and make the interpretation of findings clear.

**Completion criterion:** one command validates Account, ACR, and their relationship; someone can inspect affected counts, examples, the selected population, and the compiled SQL.

This is the first useful runtime milestone. It need not wait for full history validation, graph publication, or additional lake objects.

### Step 5 — Demonstrate combined operational and graph evidence

Identify one valuable existing Glue job or notebook early in the work. Record its repository, path, revision, parameters, and the transformations that establish its population.

Read the relevant graph subset and underlying native metadata. Reproduce the operational check, then use the graph to confirm its relationship, explain its behavior, or identify a justified improvement.

Add the result to the subject or relationship module that owns the operational question. Add a new module only if it introduces a distinct subject.

**Completion criterion:** one committed check has a precise rule statement, an explanation of how both the operational source and graph/native-metadata evidence contribute, meaningful fixtures, and guidance on what to investigate when it fails. Select a check for which both sources provide useful evidence; other checks need only their relevant sources.

If sources disagree, document the unresolved candidate in `docs/sources.md` and leave it out of the runner's selected suites.

### Step 6 — Add history checks when the temporal contract is confirmed

Add the shared `gx/history.py` builder and the necessary Ibis history expressions. Reuse them for both objects and expose them through `--include-history`.

**Completion criterion:** the selected version-key, interval, flag, and overlap rules pass their behavioral fixtures and execute against the confirmed Athena schema.

Keep this step from delaying the first useful demonstration. Schedule production execution and broader coverage only after the initial findings determine the next operational priority.

## 6. Authoring instructions and rule evidence

The repository skill should be approximately one page, with the implemented pilot module serving as its worked example.

Its workflow is:

1. Read the requested operational question and the existing job/notebook, including upstream filters and joins.
2. Retrieve only relevant graph nodes, edges, expressions, and source pointers; inspect the native source when interpreting behavior.
3. Verify physical table/column bindings and the intended data selection.
4. State the population, failing condition, row grain, null behavior, duplicate behavior, and timing assumptions.
5. Write ordinary Ibis query functions and native GX expectations in the appropriate subject module.
6. Add meaningful passing/failing fixtures and preserve source references and rationale.
7. Add accepted rules to the explicit suite selection. Keep unresolved candidates outside it.

Graph interpretation must respect the existing [lineage guide](https://github.com/mbkranz/ppsc-salesforce/blob/dev/docs/salesforce/lineage.md). In particular, retrieve incident-edge evidence when necessary, deliberately follow association links, and do not treat illustrative `athena_sql` or Flow assignments as proven persistent business invariants.

Keep metadata compact. Each rule needs:

- A stable `rule_id` and clear native GX `description`.
- A short rationale and violation grain.
- Source references with revision and code location or metadata pointer.
- Graph org/revision and relevant IDs where graph evidence contributes.
- Material assumptions and the expected investigation when it fails.

Keep run-specific physical bindings and time selections in `run.json`, rather than duplicating them across every rule.

`meta.status = "candidate"` is descriptive metadata and must never serve as execution control.

## 7. Commands and outputs

Poe tasks should call the package entry points directly. Use Python for the SDK and validation work; use Poe for the visible command interface.

Illustrative commands after implementation:

```bash
uv sync --locked

uv run poe inspect --config params.local.yaml

uv run poe validate \
  --config params.yaml \
  --as-of 2026-10-15 \
  --lake-as-of 2026-10-17T12:00:00Z \
  --dry-run

uv run poe validate \
  --config params.local.yaml \
  --as-of 2026-10-15 \
  --lake-as-of 2026-10-17T12:00:00Z

uv run poe check
```

The dates above are examples. Replace them with a verified completed selection. Example configuration can compile illustrative SQL in dry-run mode; live mode must reject unresolved placeholders.

Save each run beneath an ignored output directory:

| Output | Contents |
| --- | --- |
| `run.json` | Run ID, code revision, dependency versions, effective-date/current selection, physical snapshot selection, non-secret bindings, and load-completion evidence or its unresolved status. |
| `sql/` | The SQL used for each named asset. |
| `suites/` | Native GX-serialized suites. |
| `results/` | Native GX validation results. |
| `summary.json` | Per-rule status, failure count where available, and execution errors. |
| `data_docs/index.html` | GX's readable report for the saved validation results. |

For dry-run output, omit validation results and Data Docs, and clearly identify the output as a preview.

Use exit code `0` for successful validation, `1` for data failures, and `2` for configuration or execution errors. An execution error takes precedence if a run also contains data failures. Record exceptions reported inside GX results as errors as well as exceptions raised by the runner.

Keep diagnostic samples bounded. A displayed sample of 200 rows must not be mistaken for the total failure count.

## 8. Verification and completion

### Meaningful local verification

| Area | What to assert |
| --- | --- |
| State selection | Old unchanged versions remain eligible; replacement boundaries select the intended version; malformed inputs remain visible to the relevant history checks. |
| Relationship | Missing, blank, and null references behave as authored; missing and duplicate parents remain visible; joins preserve child-row grain. |
| History | Confirmed version keys, inconsistent flags, closed and open-ended overlaps, nested intervals, and necessary predecessor history. |
| GX behavior | Native suites retain descriptions and rule metadata through JSON round trips; data failures and execution errors remain distinct. |
| Counts | One controlled case with more than 200 failures verifies total count separately from displayed samples. |
| Dry run | No AWS credentials or network calls are required; source snapshot clauses survive compilation. |

Use DuckDB for Ibis behavioral fixtures. A small supported local GX fixture, such as SQLite, can verify native result and serialization behavior without adding a second production backend. That does not substitute for the live Athena gate.

CI should run Ruff and the meaningful local tests from the locked environment. Do not add a broad backend matrix or live AWS credentials to the first GitHub Actions workflow.

### Definition of done

The repository initiation is complete when:

- A fresh checkout installs and runs local checks with the lockfile.
- The documented inspection and dry-run commands work.
- The configured live Athena path has a recorded acceptance result.
- Account, ACR, and their relationship validate over a declared population.
- Counts, examples, and execution errors are understandable.
- Native GX results, Data Docs, SQL, suites, and run selection are saved.
- At least one useful existing operational check has an implementation or explanation supported by both the source job/notebook and graph/native-metadata evidence, with traceable references to each.
- The README and short authoring instructions explain how to add the next check.

If AWS access or a source notebook is still unavailable, complete the local implementation and mark only the corresponding live/evidence milestone as pending.

## 9. Scope boundaries and remaining inputs

### Keep the initial implementation small

Defer a general rule DSL, registry, graph-to-rule compiler, custom GX execution engine, automatic suite discovery, new shared-components package, and a broad backend abstraction.

Keep graph production and publication in `ppsc-salesforce`. The validation runtime does not need that repository as an installed dependency or need to fetch a graph on every run.

Add DVC when there is a concrete deterministic build/artifact DAG to manage. The initial validation run against declared external data selections does not require adding an empty DVC workflow.

Use README and ordinary Markdown documentation now; Quarto can organize a growing documentation set later. Native GX Data Docs are sufficient for the first validation report.

### Inputs to resolve during implementation

| Input | Why it is needed |
| --- | --- |
| Actual Glue catalog/database/table names, physical columns/types, workgroup, and result location | Establish the real Athena bindings. |
| Credential/profile or role access | Complete live acceptance. |
| Confirmed effective-date convention, version identity, and deletion behavior | Interpret state and history checks correctly. |
| One known completed delivery and suitable physical snapshot selection | Avoid treating inconsistent or partial loads as data-rule failures. |
| Repository/path/revision of one useful Glue job or notebook | Complete the combined-evidence demonstration. |
| Selected Salesforce graph bundle, org, and revision | Retain the exact evidence used to author or explain the rule. |

These inputs do not prevent repository scaffolding, fixture development, offline query compilation, or native GX suite authoring.

### Primary references

- [Target repository](https://github.com/mbkranz/ppsc-ops-data-quality)
- [APMP data lake project](https://github.com/mbkranz/ppsc-salesforce/tree/dev/projects/apmp-data-lake)
- [Salesforce lineage interpretation guide](https://github.com/mbkranz/ppsc-salesforce/blob/dev/docs/salesforce/lineage.md)
- [Ibis Athena backend](https://ibis-project.org/backends/athena)
- [Ibis unbound expressions](https://ibis-project.org/how-to/extending/unbound_expression)
- [Ibis SQL-defined relations](https://ibis-project.org/how-to/extending/sql)
- [GX SQL data sources, assets, and batches](https://docs.greatexpectations.io/docs/core/connect_to_data/sql_data/)
- [GX SQL unexpected-row expectations](https://docs.greatexpectations.io/docs/core/customize_expectations/use_sql_to_define_a_custom_expectation/)
- [GX compatibility reference](https://docs.greatexpectations.io/docs/help/compatibility_reference/)
- [PyAthena SQLAlchemy integration](https://pyathena.dev/v4.1.0/api/sqlalchemy.html)
- [Athena Iceberg time/version travel](https://docs.aws.amazon.com/athena/latest/ug/querying-iceberg-time-travel-and-version-travel-queries.html)
