# PPSC Ops Data Quality

Referential integrity checks for Survey Results and Accounts in the operational
Iceberg lake. The reviewed metadata defines the path as
`Survey_Result__c.Participant__c → Contact.Id → Contact.AccountId → Account.Id`.
SQL defines the selected populations; native Great Expectations (GX) runs checks
through Athena and PyAthena.

One `expect_*.sql` file defines one expectation. The repository keeps configuration,
Athena access, population selection, subject suites, and execution separate.
Live bindings and the remaining acceptance gates are documented in
[Acceptance](docs/acceptance.md); [Sources](docs/sources.md) separates reviewed
metadata from the authored integrity contract.

## Get started

Use Python 3.12 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --locked
uv run poe check
```

Compile the illustrative configuration without AWS credentials:

```sh
uv run poe validate \
  --config params.yaml \
  --as-of 2026-10-15 \
  --lake-as-of 2026-10-17T12:00:00Z \
  --dry-run
```

The command creates a unique directory under `build/runs/` with SQL, native suite
JSON, and run metadata. The example dates and bindings are illustrative; a
successful preview does not establish live validation.

## Author an expectation

Name the SQL file after its expectation, in lower snake case beginning with
`expect_`. For example:
`src/ppsc_ops_data_quality/gx/survey_result_to_account/expect_survey_result_account_to_exist.sql`:

```sql
-- A uniquely resolved Contact with a populated AccountId resolves to an Account.
-- Investigate Contact.AccountId and completed-delivery coverage.
SELECT * FROM batch
WHERE matching_contact_versions = 1
  AND missing_account_references = 0
  AND matching_account_versions = 0
```

Return failing rows; zero rows passes. The filename supplies the expectation name,
`expect_survey_result_account_to_exist`. The subject qualifies its stable rule ID,
`survey_result_to_account.expect_survey_result_account_to_exist`. These are named
project checks executed by native GX `UnexpectedRowsExpectation`, not new GX
Python classes.

Opening `--` comments supply the description and evidence in Data Docs. New files
in an existing subject run automatically, without Python registration. Shared
sources and population assumptions live on the suite; each expectation records its
name, rule ID, and SQL path. One trailing semicolon and local CTEs are supported.
Write ordinary SQL, including aliases and literal braces; there are no authored
format placeholders. Unknown populations, invalid filenames, writes, multiple
statements, and top-level limits fail the preview.

Use `batch` for the selected subject. Cross-table checks can use `account_state`,
`contact_state`, and `survey_result_state`; the loader binds their table nodes to
the same selected populations. Physical table names bypass that selection and
are rejected. Accepted business checks still need their own passing/failing
fixtures and evidence.

## Referential integrity expectations

The relationship batch counts eligible Accounts by exact ID, then Contacts by
exact ID, before joining Survey Results. This retains every survey row, including
identical duplicates, without multiplying surveys when a parent is duplicated.
No key is normalized or deduplicated to hide a finding.

| SQL filename (under `gx/survey_result_to_account/`) | Failure condition |
| --- | --- |
| `expect_survey_result_participant_reference_to_be_present.sql` | Missing or space-only Participant reference. |
| `expect_survey_result_participant_to_exist.sql` | Populated reference has no selected Contact. |
| `expect_survey_result_participant_to_be_unique.sql` | Reference matches multiple selected Contact versions. |
| `expect_survey_result_account_reference_to_be_present.sql` | One Contact resolves, but its AccountId is missing or space-only. |
| `expect_survey_result_account_to_exist.sql` | One Contact with a populated AccountId has no selected Account. |
| `expect_survey_result_account_to_be_unique.sql` | That AccountId matches multiple selected Account versions. |

The Account and Survey Result suites each also contain
`expect_column_values_to_not_be_null.sql`,
`expect_column_values_to_not_be_blank.sql`, and
`expect_column_values_to_be_unique.sql`, scoped to their `id` columns. Structural
column checks remain native GX expectations. There are 12 SQL files in total.

An Account may have zero or many Survey Results. This contract requires every
selected survey to resolve through one Contact to one Account; it does not require
every Account to have a survey. Account-hop checks wait for exactly one Contact,
so a missing/ambiguous participant is reported at its own hop rather than as a
second Account failure.

## Configure and inspect Athena

Copy `params.yaml` to the ignored `params.local.yaml`. Set the real region,
catalog, database, workgroup, and result location. Authentication uses an existing
AWS profile or role credential chain; access keys do not belong in the file.

Discovery needs connection settings but does not need table or column bindings:

```sh
uv run poe inspect --config params.local.yaml --discover
```

Set the Account, Contact, and Survey Result table names, then inspect their physical schema:

```sh
uv run poe inspect --config params.local.yaml \
  --lake-as-of 2026-10-17T12:00:00Z
```

Update column names and SQL types from that report. Inspection reads schema, DDL,
and optional snapshot metadata. Validation preflight rejects missing or mistyped
physical inputs before selecting the batch.

For an as-of run, confirm the lake uses `[valid_from, valid_to)` intervals and set
`interval_convention_confirmed: true`. Record how the chosen delivery was
confirmed complete in `load_completion_evidence`; a recent load timestamp alone
does not demonstrate completion.
Run metadata records that evidence as supplied or unresolved; supplying text does
not verify the delivery itself.

After the controlled tests in [Acceptance](docs/acceptance.md), validate a known
completed selection:

```sh
uv run poe validate \
  --config params.local.yaml \
  --as-of 2026-10-15 \
  --lake-as-of 2026-10-17T12:00:00Z
```

Replace those dates with the intended selection. To select current rows in a
physical snapshot, use `--current` instead of `--as-of`. Supply exactly one;
`--lake-as-of` is always required and must include a timezone. Use `--output PATH`
to choose a different output root.

## What a population means

| Selection | Meaning |
| --- | --- |
| `--as-of DATE` | Rows where `valid_from <= DATE` and `valid_to > DATE OR valid_to IS NULL`, under the confirmed interval convention. |
| `--current` | Rows marked `is_current = TRUE` within the selected physical snapshot. |
| `--lake-as-of TIMESTAMP` | One timezone-aware timestamp used for Iceberg time travel on every source table. This is separate from the effective date. |
| Relationship batch | Survey Result, Contact, and Account share the state selection. Counts distinguish missing/ambiguous references at each hop while retaining survey-row grain. |

Old unchanged records remain in the selected state. The queries do not select
only recently loaded rows or silently deduplicate parents. A shared snapshot
timestamp does not prove a coordinated multi-table delivery completed.

The initial suites check projected columns, required/nonblank/unique identifiers,
and Survey Result-to-Account reference integrity. Full history validation is deferred.

## Commands and results

| Command | Purpose |
| --- | --- |
| `uv run poe inspect` | Discover tables or inspect configured physical sources. |
| `uv run poe validate` | Preview or run the explicit pilot suites. |
| `uv run poe test` | Run synthetic local tests; additional pytest arguments are accepted. |
| `uv run poe check` | Run Ruff lint, Ruff format checks, and tests. |

Each invocation of `validate` uses a new directory beneath the selected output
root:

| Output | Contents |
| --- | --- |
| `run.json` | Mode, code/dependency versions, bindings, time selections, and delivery evidence. |
| `sql/` | Athena SQL for each selected batch. |
| `suites/` | Native GX suite JSON, including rule descriptions and source metadata. |
| `summary.json` | Per-rule findings and execution errors; preview mode is identified explicitly. |
| `results/` | Native GX validation results from live runs. |
| `data_docs/index.html` | Readable GX report from live runs. |

Exit code **0** means validation passed, or a dry-run preview succeeded;
**1** means data failed a rule; **2** means a configuration or execution error.
Errors take precedence when both errors and data failures occur. Diagnostic
samples are bounded; their length is not the total failure count.

Keep real outputs, Data Docs, and local configuration out of Git and public CI.

## Module layout and authoring

| Path | Responsibility |
| --- | --- |
| `config.py` | One YAML configuration and explicit physical bindings. |
| `athena.py` | Connection settings, inspection, and snapshot-bound sources. |
| `batches.py` | Shared SQL state selectors and relationship queries. |
| `gx/<subject>.py` | Columns and assumptions; shared construction lives in `gx/__init__.py`. |
| `gx/<subject>/expect_*.sql` | One failing-row SELECT per named expectation; rule IDs include the subject. |
| `run.py` | Explicit suite selection, execution, results, and Data Docs. |
| `tests/` | Synthetic DuckDB behavior and native GX/result checks. |
| [Sources](docs/sources.md) | Reviewed evidence, assumptions, and unresolved rule candidates. |

Python module paths are relative to `src/ppsc_ops_data_quality/`. Add a named query
function or SQL check where the operational question belongs. State the
population, row grain, null/duplicate behavior, and sources, then add meaningful
passing/failing fixtures. Accepted checks join the runner's explicit selection;
unresolved candidates stay outside it.

Poe owns operational commands. Add DVC only when there is a concrete deterministic
artifact build to manage.
