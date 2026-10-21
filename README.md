# PPSC Ops Data Quality

Repeatable data quality checks for Account, AccountContactRelation (ACR), and their
relationship in the operational Iceberg lake. Readable SQL defines the selected data;
native Great Expectations (GX) suites validate it through Athena and PyAthena.

The repository keeps one explicit runner and one module per subject. Graphs,
metadata, and existing jobs inform rule authoring; routine runs use committed code.
Live Athena acceptance and the combined operational/graph evidence milestone are
tracked in [Acceptance](docs/acceptance.md).
The [implementation plan](docs/implementation-plan.md) records the reviewed tool patterns and this branch’s design.

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

## Add a SQL integrity check

Create one file under the existing subject, for example
`src/ppsc_ops_data_quality/gx/account_contact_relation_to_account/parent.exists.sql`:

```sql
-- A populated Account reference must resolve in the selected Account state.
-- Investigate parent coverage, load completeness, and effective timing.
SELECT * FROM {batch}
WHERE account_id IS NOT NULL
  AND TRIM(account_id) <> ''
  AND matching_account_versions = 0
```

The file defines one check. Return failing rows; zero rows passes. The filename
becomes the stable rule ID (`account_contact_relation_to_account.parent.exists`).
Comments supply the explanation in Data Docs. Adding a file to an existing subject
needs no Python edit or registration. Keep provenance and assumptions in its
comments; accepted source evidence belongs in `docs/sources.md`.

Each subject keeps its Python module for native structural validation, and adds a
sibling directory of SQL files. All nine existing identity/reference checks use
this format. The loader uses native `UnexpectedRowsExpectation` for full counts
and bounded diagnostic samples. A trailing semicolon and CTEs are supported.

Use `{batch}` for the subject population. Cross-table checks can also join
`account_state` and `account_contact_relation_state` directly:

```sql
-- Find populated ACR references absent from the selected Account state.
SELECT child.*
FROM account_contact_relation_state AS child
WHERE child.account_id IS NOT NULL AND TRIM(child.account_id) <> ''
  AND NOT EXISTS (
    SELECT 1 FROM account_state AS parent WHERE parent.id = child.account_id
  )
```

The runner supplies both relations using the same effective selection and pinned
physical snapshot. Do not name physical tables in checks: that bypasses population
selection. Unknown relations, multiple statements, and writes fail the preview.
This validates the authoring contract, not a SQL security sandbox; author only
trusted queries. Never use `LIMIT` to cap a check's total findings.

Run the documented dry run to inspect the generated batch SQL and suite JSON,
then `uv run poe check`. Tests establish the nine initial checks with synthetic
passing/failing rows. A new rule still needs fixtures for its own contract.

## Configure and inspect Athena

Copy `params.yaml` to the ignored `params.local.yaml`. Set the real region,
catalog, database, workgroup, and result location. Authentication uses an existing
AWS profile or role credential chain; access keys do not belong in the file.

Discovery needs connection settings but does not need table or column bindings:

```sh
uv run poe inspect --config params.local.yaml --discover
```

Set the Account and ACR table names, then inspect their physical schema:

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
| Relationship batch | ACR and Account use the same state selection. Parent-match counts distinguish missing and ambiguous references while preserving child-row grain. |

Old unchanged records remain in the selected state. The queries do not select
only recently loaded rows or silently deduplicate parents. A shared snapshot
timestamp does not prove a coordinated multi-table delivery completed.

The initial suites check projected columns, required/nonblank/unique identifiers,
and Account-reference integrity. Full history validation is deferred.

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
| `athena.py` | Connection settings, inspection, snapshot-bound sources, and SQL compilation. |
| `batches.py` | Shared SQL state selectors and relationship queries. |
| `gx/<subject>.py` | Native structural suites and one failing-row check per `.sql` file. |
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
