# PPSC Ops Data Quality

Repeatable data quality checks for Account, AccountContactRelation (ACR), and their
relationship in the operational Iceberg lake. Ibis defines the selected data;
native Great Expectations (GX) suites validate it through Athena and PyAthena.

The repository keeps one explicit runner and one module per subject. Graphs,
metadata, and existing jobs inform rule authoring; routine runs use committed code.
Live Athena acceptance and the combined operational/graph evidence milestone are
tracked in [Acceptance](docs/acceptance.md).
The [implementation plan](docs/implementation-plan.md) records the initial scope
and sequence.

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

Update column names and Ibis types from that report. Inspection reads schema, DDL,
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
| `batches.py` | Reusable state selectors and relationship expressions. |
| `gx/<subject>.py` | Native suite builders for a subject or relationship. |
| `run.py` | Explicit suite selection, execution, results, and Data Docs. |
| `tests/` | Synthetic Ibis/DuckDB behavior and native GX/result checks. |
| [Sources](docs/sources.md) | Reviewed evidence, assumptions, and unresolved rule candidates. |

Python module paths are relative to `src/ppsc_ops_data_quality/`. Add a named query
function and native expectation where the operational question belongs. State the
population, row grain, null/duplicate behavior, and sources, then add meaningful
passing/failing fixtures. Accepted checks join the runner's explicit selection;
unresolved candidates stay outside it.

Poe owns operational commands. Add DVC only when there is a concrete deterministic
artifact build to manage.
