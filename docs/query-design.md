# Account / Survey Result validation directly from history

The default path builds plain Ibis expressions, compiles the final comparison to
Athena SQL, and passes that SELECT to a native GX Query Asset. The built-in GX
suites compare expected and independently observed values. No Athena views or
intermediate tables are required.

## Files

| File | Responsibility |
|---|---|
| `runtime/` | Athena/DuckDB adapters, native GX runner, and SQL-file metadata TODO |
| `schemas/` | Explicit validation-input/history schemas and inferred derived schemas |
| `snapshot.py` | Composable SCD2 snapshot expression |
| `queries.py` | History bindings, comparison joins, Flow and rollup query composition |
| `gx_queries.py` | Compile Athena SELECT and register a native GX Query Asset |
| `account_to_survey_results.py` | Existing named Ibis Flow decisions, formulas, derived fields and rollups |
| `account_to_survey_results_lineage.py` | Original metadata IDs, workbook rows, branch lineage and output-alias mappings |
| `account_to_survey_results_expectations.py` | Native GX suite builders, independent of dataset construction |
| `views.py` | Optional publishing of a final query as an Athena view |
| `account_to_survey_results.sql` | Two illustrative expected-value SELECTs over history |
| `account_to_survey_results_gx_comparison.sql` | Two illustrative comparison SELECTs accepted by GX |
| `suites/` | Native Flow and rollup suite JSON |
| `tests/` | Snapshot, expression, lineage and native GX Query Asset verification |

## Validate one verified Flow event

Supply Ibis history relations with real catalog schemas and your existing GX SQL
Data Source. `schemas.history_tables()` binds the explicit input profiles without
a backend. Supply catalog-verified schemas through its schema arguments when
available. Credentials and connection configuration remain outside these modules.
See `schemas/README.md` for field coverage, workbook provenance and physical-type
assumptions. `queries.bind_history_tables()` remains available for catalog discovery
through an existing backend. For Athena, configure the
GX SQL Data Source with the PyAthena SQLAlchemy dialect and temporary-table
creation disabled. The adapter itself never creates a Context or datasource.

```python
from datetime import date, datetime
from ppsc_ops_data_quality.queries import flow_account_query
from ppsc_ops_data_quality.schemas import history_tables
from ppsc_ops_data_quality.gx_queries import query_batch_definition
from ppsc_ops_data_quality.account_to_survey_results_expectations import flow_account_suite

history = history_tables(
    account_database="your_account_database",
    contact_database="your_contact_database",
    survey_result_database="your_survey_result_database",
)

# Illustrative values: replace with independently verified event timing.
before_at = datetime(2026, 10, 21, 11, 59, 59)
execution_at = datetime(2026, 10, 21, 12, 0)
after_at = datetime(2026, 10, 21, 12, 5)
run_id = "example_run_20261021_1200"

Comparison = flow_account_query(
    history,
    survey_result_id="YOUR_VERIFIED_SURVEY_EVENT",
    account_before_at=before_at,
    execution_at=execution_at,
    account_after_at=after_at,
    flow_run_date=date(2026, 10, 21),  # org-local execution DATE
)
definition = query_batch_definition(
    data_source,
    Comparison,
    name=f"account_survey_flow_{run_id}",
    metadata={
        "run_id": run_id,
        "account_before_at": before_at.isoformat(),
        "execution_at": execution_at.isoformat(),
        "account_after_at": after_at.isoformat(),
        "survey_result_id": "YOUR_VERIFIED_SURVEY_EVENT",
    },
)
batch = definition.get_batch()
result = batch.validate(flow_account_suite(expected_row_count=1))
```

The query selects one triggering survey record, uses all survey records at
execution for FlowRecordLookups, and joins Contact at execution to Account BEFORE.
Expected values follow the existing Flow decisions and CASE expressions. Observed
values come from the independently supplied Account AFTER time and are explicitly
associated with the selected survey event. The final LEFT JOIN uses both Account
and survey event identity; missing observations and duplicates remain visible.

Verify the Complete transition, automation exemption, settled asynchronous work,
and source temporal contract upstream. Timestamps must satisfy BEFORE < execution
< AFTER and match the validity columns' time-zone awareness. The execution DATE
used for Flow age calculations is explicit and may differ from a UTC calendar day.
Date-grain history cannot reconstruct several states within one day.

Use a run-scoped ephemeral GX Context, or unique asset names in a persistent
Context. The adapter deliberately lets GX reject an existing asset name; it does
not silently replace a query another run may be validating. `metadata` records
run facts and does not substitute SQL parameters or filter rows.

If you do not use an Ibis backend to discover schemas, author unbound relations
from your catalog-derived Ibis schemas. Compilation still targets Athena:

```python
import ibis

history = {
    "Account": ibis.table(account_schema, name="history", database="your_account_database"),
    "Contact": ibis.table(contact_schema, name="history", database="your_contact_database"),
    "Survey_Result__c": ibis.table(
        survey_schema, name="history", database="your_survey_result_database"
    ),
}
```

## Validate snapshot rollups

```python
from ppsc_ops_data_quality.queries import rollup_account_query
from ppsc_ops_data_quality.account_to_survey_results_expectations import rollup_account_suite

RollupComparison = rollup_account_query(history, as_of=execution_at)
definition = query_batch_definition(
    data_source,
    RollupComparison,
    name=f"account_survey_rollups_{run_id}",
    metadata={"run_id": run_id, "as_of": execution_at.isoformat()},
)
result = definition.get_batch().validate(rollup_account_suite())
```

Both sides use the same effective snapshot. The grain is one person Account,
including Accounts with zero matching survey records. Supply `expected_row_count`
from an independent source count when you need a volume contract.

For finer composition, import `flow_account_comparison()` and
`rollup_account_comparison()` from `queries.py` and supply already bound Ibis
relations. The derivation functions remain directly importable from
`account_to_survey_results.py`.

## Snapshot and batch semantics

`snapshot(history, as_of=None)` returns an Ibis table expression with
`is_current = TRUE`. With a date/datetime, it applies:

```sql
valid_from <= as_of AND (valid_to > as_of OR valid_to IS NULL)
```

This translates `state_predicate()` / `state_sql()` from the previous
`ppsc-athena-gx-sample/batches.py`, October 17, 2026. That sample described the SCD2
interval as a proposed ETL contract. Confirm it and the deletion/tombstone contract
against the history producer. No ranking, deduplication or deletion policy is
invented here. NULLs and overlapping versions remain visible.

Date bounds require a date; timestamp bounds retain datetime precision. A date
against timestamp bounds means midnight in the column's time zone. Column names
can be mapped explicitly through `valid_from=`, `valid_to=` and `is_current=`.
Map catalog column casing and scope combined-object history upstream if needed.
`bind_history_tables()` assumes one table named `history` in each explicitly
configured object database; a mapping of your own Ibis relations works equally.

GX batch parameters select configured partitions. They are not arbitrary SQL
bindings for BEFORE, execution, AFTER, survey event IDs, or SCD2 interval predicates.
Those values are explicit query-builder arguments compiled as Ibis literals.
The Query Asset uses a whole-query Batch Definition; it does not need batch params.

An effective `as_of` is not a physical Iceberg version pin. Later corrections can
change history and results across metric queries. For immutable run inputs, bind
pinned physical source versions upstream or materialize a run-specific comparison.
Neither is inferred or automatically implemented by this code.

## Compilation and lineage

```python
from ppsc_ops_data_quality.gx_queries import query_asset_sql

sql = query_asset_sql(Comparison)  # one SELECT; no terminal semicolon
```

Complete composition before compilation. `to_sqlglot()` annotates final projections
by explicit output alias using the independent lineage mapping. Comparison aliases
such as `expected__Basics_Date_Time__c` retain the original Flow branch lineage;
`observed__Basics_Date_Time__c` describes an independent observed Account field.
Observed fields do not inherit expected calculation branches.

The GX adapter wraps the compiled query in `SELECT * FROM (...) AS comparison`.
GX 1.24 requires SELECT followed by whitespace at the start of query text; the
wrapper accommodates Ibis CTEs and leading lineage comments. SQL text contains
readable comments; structured SQLGlot meta remains in the AST/canonical mapping.
Native GX expectations also carry canonical field/branch lineage in `meta["ppsc"]`.

The example SQL files use `example_account.history`, `example_contact.history`,
`example_survey_result.history`, an example event, and illustrative timestamp field
types. They are reviewable examples, not verified production catalog bindings.
Regenerate from the actual catalog schemas through `queries.py`.

## Expectations and performance

The Flow suite has 27 native expectations; the rollup suite has 24. Each optionally
adds an independent row-count expectation. Checks cover required columns, non-null
identity, unique grain, lookup determinism and 19 expected/observed field pairs.

Pairs use `mostly=1` and `ignore_row_if="both_values_are_missing"`: two NULLs are
excluded together; a one-sided NULL fails. An ambiguous unsorted pediatric
permission lookup fails the determinism expectation, while CABOR equality also
requires deterministic evidence to avoid comparing an unresolved expected value.

The Flow comparison preserves `survey_completion_timestamp` and the named Ibis
predicate `survey_completion_occurred_on_or_after_launch`. The predicate compares
the completion timestamp calendar date to the inclusive DATE literal 2024-12-16;
source timestamps must already use the agreed business timezone. GX's named
`POST_LAUNCH_COMPLETION` predicate consumes this Boolean column. All Flow row
expectations (including the optional independent post-launch count) use it;
CABOR combines it with lookup determinism. Structural expectations remain
unconditional. No pre-launch trigger or lookup records are removed by this scope.
NULL completion timestamps yield unknown scope and are excluded from Flow checks,
so a successful Flow suite alone does not establish timestamp/population coverage.
The source mapping identifies the launch condition as a user-specified
BusinessCondition, not a translated FlowDecision. Rollups remain independently
scoped to their Account snapshot. Migration joins and coverage checks are deferred.
Empty batches pass unless an independent count contract says otherwise.

A Query Asset or normal Athena view does not guarantee that GX computes the joins
once for all expectations. GX can issue multiple metric queries. Measure Athena
query count, bytes scanned and runtime before optimizing. Materializing the final
comparison is an optional later optimization for expensive repeated scans.

## Run native Validation Definitions

`runtime/athena.py` and `runtime/duckdb.py` take Ibis comparisons and return a
native GX Validation Definition plus that definition's batch parameters.
`runtime.run_validations()` executes a supplied collection with separate parameter
mappings and one run ID. Supply `suite_directory` for that run: immediately before
each validation, the runner saves its actual registered suite as native GX JSON,
including configured values and lineage. Existing snapshots are not overwritten.
The runner returns native GX results and uses the Context's result store. See `runtime/README.md` for setup, resource ownership and complete examples.

Athena uses the existing Query Asset adapter. DuckDB evaluates the comparison
locally and validates the resulting pandas frame. No compiled SQL files are read
for execution. `runtime/TODO.md` records the future authored-SQL path and required
comment/metadata/parameter/audit conventions.

## Optional view publishing

```python
from ppsc_ops_data_quality.views import create_view_sql, create_view

# Review only:
ddl = create_view_sql(Comparison, name="account_survey_comparison", database="quality")

# Explicitly execute using an existing Athena DB-API connection:
PublishedComparison = create_view(
    connection, Comparison, name="account_survey_comparison", database="quality"
)
```

This is separate from the normal GX path. A normal view recomputes its query and
does not freeze or materialize rows. This revision removes the `AthenaView` wrapper
and intermediate view chain: `snapshot()` no longer takes `view_name` or `database`,
and comparison builders now live in `queries.py`. No compatibility wrappers remain.

## Verification and dependencies

```bash
uv sync --locked
uv run poe check
```

Verified with GX Core 1.24.0, Ibis 12.0.0 and SQLAlchemy 2.1.6. The 64 tests cover
source schema types and conversions, catalog overrides, SCD2 boundaries/types,
duplicate preservation, direct history-to-comparison
execution on DuckDB, missing relationships, NULL semantics, ambiguous lookups,
source lineage, and actual native Query Asset validation on SQLAlchemy/SQLite
including a deliberately wrong observed value. All example SQL parses in Athena
dialect. No live Athena queries or DDL were executed. Use your configured Athena
runtime and install its GX/PyAthena dependencies for the remaining live smoke test.

## References

- [GX QueryAsset API, 1.24](https://docs.greatexpectations.io/docs/reference/api/datasource/fluent/sql_datasource/queryasset_class/)
- [GX SQL assets and batches](https://docs.greatexpectations.io/docs/core/connect_to_data/sql_data/)
- [GX data integrity](https://docs.greatexpectations.io/docs/reference/learn/data_quality_use_cases/integrity/)
- [GX native row conditions](https://docs.greatexpectations.io/docs/core/customize_expectations/row_conditions/)
- [Athena views](https://docs.aws.amazon.com/athena/latest/ug/views.html)
- Previously reviewed [expectations-and-suites skill](https://github.com/VectorSpaceLab/AREX-Skill/blob/main/skills/repositories/repo-skills/great-expectations/sub-skills/expectations-and-suites/SKILL.md) and its expectation API / row condition references informed suite authoring. Current API behavior was verified against GX 1.24's installed implementation and tests.
