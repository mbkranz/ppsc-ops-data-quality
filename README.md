# PPSC operational data quality

Compute expected Account values from Survey Result history with Ibis, then compare
them with independently observed Account values using native Great Expectations
(GX) suites. Run the same query builders against Athena or bounded local DuckDB
data. Python expressions and suite builders are the authored source; SQL and suite
JSON are generated review and run-audit artifacts.

The first implementation covers the Survey Result completion Flow and 19 Account
survey rollups. It preserves the relationship
`Survey_Result__c.Participant__c -> Contact.Id -> Contact.AccountId -> Account.Id`,
missing parents, duplicate matches, assigned NULLs and unchanged prior values.

## Quick start

Requires Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/). CI and the local
acceptance run use Python 3.12. No AWS credentials are needed for these commands:

```bash
uv sync --locked --python 3.12
uv run poe check
uv run poe preview
uv run poe demo
```

`preview` compiles two illustrative Athena comparison queries and exports their
native suite JSON. `demo` creates synthetic Account, Contact and Survey Result
history in DuckDB and validates one Basics completion event plus settled rollups.
The independently declared observed values are not generated from expected values.

Both commands print their output location. Fresh default paths are created under
`build/previews/` and `build/runs/`. To choose a destination:

```bash
uv run ppsc-dq preview --output build/my-preview
uv run ppsc-dq demo --run-dir build/my-demo
```

Existing destinations are rejected so prior evidence is not replaced. The demo
saves DuckDB SQL, exact registered suite snapshots, native validation results and
`run.json` with parameters, dependency versions and outcome. Exit codes are 0 for
success, 1 for failed expectations and 2 for execution/configuration errors.

## Organization

```text
src/ppsc_ops_data_quality/
    account_to_survey_results.py              # Ibis decisions, formulas and expected fields
    account_to_survey_results_lineage.py      # Original source IDs, workbook rows and branches
    account_to_survey_results_expectations.py # Native GX suite builders
    queries.py                               # History bindings and comparison composition
    snapshot.py                              # SCD2 state selection
    gx_queries.py                            # Ibis-to-Athena Query Asset adapter
    schemas/                                 # Explicit inputs and inferred derived schemas
    runtime/                                 # Athena/DuckDB preparation, runner and suite export
    views.py                                 # Optional final-query view publishing
    cli.py                                   # Offline preview/demo commands
    demo.py                                  # Synthetic source data and selected event
examples/validate_athena.py                   # Explicit live-runtime setup example
params.example.toml                          # Illustrative bindings and temporal parameters
sql/                                         # Generated Athena SELECTs for review
suites/                                      # Generated baseline suites for review
```

The runtime accepts Ibis tables. Athena compiles the final comparison into a GX
Query Asset. DuckDB evaluates the expression once and supplies the resulting
pandas DataFrame to GX, collecting the complete comparison into local memory.
The shared runner executes native GX Validation Definitions with separate batch
parameters per definition. It does not introduce a second rule or engine framework.

## Use the library

```python
from ppsc_ops_data_quality.queries import flow_account_query
from ppsc_ops_data_quality.schemas import history_tables

history = history_tables(
    account_database="account_database",
    contact_database="contact_database",
    survey_result_database="survey_result_database",
)
Comparison = flow_account_query(
    history,
    survey_result_id=verified_event_id,
    account_before_at=verified_before_time,
    execution_at=verified_execution_time,
    account_after_at=verified_settled_after_time,
    flow_run_date=org_local_execution_date,
)
```

`history_tables()` returns unbound Ibis relations for tables named `history` in
three explicitly configured databases. Supply catalog-verified schema overrides
when types differ. An existing backend can instead discover tables through
`queries.bind_history_tables()`. For combined history, construct explicitly scoped
Ibis relations upstream. Neither binding path infers object discriminators or
silently fixes column casing.

The Flow query selects one verified triggering event, looks up related surveys at
execution, derives expected Account AFTER values from Account BEFORE, and compares
with an independently observed settled AFTER snapshot. Caller-supplied timestamps
must satisfy BEFORE < execution < AFTER. Current Account state cannot validate all
historical events. Rollups use one common effective point at a person Account grain,
including zero-child Accounts.

## Run against Athena

`examples/validate_athena.py` shows complete GX/SQLAlchemy setup using the runtime:

1. Copy `params.example.toml` to ignored `params.local.toml`.
2. Bind the actual databases and verify the physical columns/types, validity
   intervals, deletion semantics and completed delivery/event timing.
3. Set standard AWS credentials/profile outside the configuration file.
4. Run with a new output directory:

```bash
uv run python examples/validate_athena.py \
  --config params.local.toml --run-dir build/athena-run-001
```

The example uses an existing Athena workgroup/results location and creates no
views or tables. Native GX result/configuration stores are written under the run
directory. Schema overrides supplement the explicit input profiles; no automatic
casting or case normalization is performed. The example rejects placeholder
bindings before connecting. Runtime adapters are also callable directly from your
own job entrypoint; see their README for resource ownership.

Live Athena/Glue execution and the deployed catalog schemas are not verified.
The supplied schemas cover the columns required by this workflow rather than all
Salesforce fields. History timestamp bounds are an explicit example profile; an
earlier Athena sample used DATE bounds. Date-grain history cannot reconstruct
several states within a day. An effective `as_of` does not pin an Iceberg physical
version: late corrections can change results. Use verified physical source pins
upstream or materialized run inputs when immutable evidence is required.

Glue is a hosting environment. No Spark adapter, Glue job provisioning or job
submission wrapper is included. GX 1.24 requires Python 3.10+, whereas the documented
Glue Python Shell runtime is 3.9; select a compatible host and test its dependencies.
Retain operational AWS commands in the deployment/Poe layer.

## Rules, schemas and lineage

The Flow suite has 27 built-in expectations and the rollup suite has 24, each with
an optional independent row-count check. They cover required columns, identity,
unique grain, permission-lookup resolution and 19 expected/observed field pairs.
The demo supplies counts of one, yielding 28 and 25 expectations respectively.

Two NULLs are excluded together by the pair equality policy; a one-sided NULL
fails. Unresolved pediatric-permission lookups fail their determinism check; only
CABOR equality is conditioned on resolution. Empty batches require an explicit
source count if they must fail. Duplicate observations and missing parents survive
LEFT JOINs so the suites can detect them.

Schemas are ordinary `ibis.Schema` definitions, with full declarations for their
named validation-input projections. Derived schemas come from actual expressions.
Arrow is an interchange conversion, not a second authored schema. Source fields
stay nullable so GX can detect invalid raw values. Numeric precision and field
provenance follow the supplied Salesforce workbook where available.

Original FlowDecision, FlowRecordLookup, formula and field IDs remain in the
independent lineage mapping. SQLGlot metadata is attached after Ibis composition
by stable projected alias. SQL comments explain generated queries; arbitrary
structured metadata is not preserved by ordinary SQL or Ibis schema round trips.

The runner requires a run-scoped `suite_directory` and serializes the actual
registered suite immediately before each native validation. IDs, configured row
counts and field/branch metadata are retained. Existing suite snapshots are not
overwritten. GX `$PARAMETER` values remain symbolic in the suite; retain runtime
expectation parameters separately with your run metadata.

## Documentation and follow-up work

- [Query composition and original sources](docs/query-design.md)
- [Schema contracts and conversions](src/ppsc_ops_data_quality/schemas/README.md)
- [Runtime setup and native definitions](src/ppsc_ops_data_quality/runtime/README.md)
- [Authored SQL-file execution and metadata/comment standards TODO](src/ppsc_ops_data_quality/runtime/TODO.md)

Authored SQL-file execution remains deferred. Before implementing it, agree a
versioned comment/manifest convention, stable column lineage IDs, typed parameter
binding and audit/round-trip behavior. Generated SQL files are not runtime inputs.

A Query Asset or normal Athena view does not promise one computation for all GX
metrics. Measure query count, scan bytes and runtime before adding materialization.
No automatic migration, deployment, data cleaning or quarantine behavior is included.
