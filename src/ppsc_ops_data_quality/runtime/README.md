# Runtime adapters and native GX validation execution

Runtime inputs are already-composed Ibis comparison expressions. Athena compiles
one to a Query Asset; DuckDB executes one locally and supplies the resulting
pandas DataFrame to GX. The shared runner receives native GX Validation Definitions
and their per-definition parameters, with no query-building logic or engine API.

## Files

| Module | Responsibility |
|---|---|
| `athena.py` | Prepare a Query Asset and native Validation Definition |
| `duckdb.py` | Evaluate Ibis with DuckDB and prepare a pandas-backed definition |
| `runner.py` | Save each actual suite, then run definitions with separate parameters and one run ID |
| `artifacts.py` | Serialize actual suites and gzip native result JSON without overwriting evidence |
| `reports.py` | Build native Data Docs, write typed Parquet discovery rows, and upload the run to S3 |
| `TODO.md` | Future authored-SQL execution and comment/metadata standards |

There are no custom Engine or ValidationDefinition classes, backend registries,
automatic connections, schema discovery, AWS job submission or framework-specific
rule wrappers. The existing query, schema, suite and lineage modules remain the
owners of their respective definitions.

## Per-run reports and S3 publication

Use `run_validations_with_reports()` for a complete run with publication. It
composes the existing runner with native Data Docs and explicit boto3 uploads.
The Athena entrypoint requires `[reports].s3_uri`; the local demo uses the same
builder without AWS unless `--s3-uri` is supplied. Provide a fresh Context, a new
report directory and source metadata for each definition (physical table names,
actual comparison SQL and dialect). The function returns native GX results.

The main discovery dataset has **one row per expectation result per Validation
Definition per run**, including successful results. Each row repeats its run,
definition and source/query identity. An independent validation-summary dataset
records one row per planned definition, including missing results after an
execution error. Gzip native JSON remains the complete audit representation.

Schemas are ordinary Ibis schemas in `schemas/validation_reports.py`. See
[`docs/validation-reports.md`](../../../docs/validation-reports.md) for the format
decision, S3 layout, failure semantics and catalog setup. The two external-table
templates in `sql/validation_reports_catalog.sql` register only Parquet analytics
prefixes. No crawler or table creation is performed during validation.

## Athena

Supply an existing GX Context, an Athena SQL Data Source in that Context, and a
comparison composed from your correctly bound history relations. The suite must
be registered in the same Context. Use a run-scoped ephemeral Context or unique
names for different query bindings; existing assets are never silently replaced.

```python
from ppsc_ops_data_quality.runtime.athena import prepare_validation
from ppsc_ops_data_quality.runtime import run_validations
from ppsc_ops_data_quality.account_to_survey_results_expectations import flow_account_suite

suite = context.suites.add(flow_account_suite(expected_row_count=1))
definition, parameters = prepare_validation(
    context,
    athena_data_source,
    Comparison,
    suite,
    name=f"account_survey_flow_{run_name}",
    metadata={"run_id": run_name, "survey_result_id": verified_trigger_id},
    sql_path=f"artifacts/{run_name}/flow_athena.sql",
)
results = run_validations(
    [definition],
    suite_directory=f"artifacts/{run_name}/suites",
    batch_parameters={definition.name: parameters},
)
```

Preparation builds and stores the native definition but does not fetch a batch.
Execution happens in `run_validations()`. The optional SQL file is the exact
SELECT stored in the Query Asset, including the existing SQLGlot lineage comments.
Actual GX metric queries can wrap that SELECT and may execute it multiple times.
The runtime neither materializes rows nor pins source versions. Record verified
BEFORE/execution/AFTER parameters, physical source versions and code version in
your run metadata/artifact conventions. Credentials remain in your configured
connection, not in comparison metadata.

## DuckDB local development and CI

Use an existing Ibis DuckDB connection with local fixtures/Parquet sources. Rebuild
the comparison with those relations before passing it to the adapter; production
catalog names are not automatically redirected. Supply a GX pandas Data Source.

```python
from ppsc_ops_data_quality.runtime.duckdb import prepare_validation
from ppsc_ops_data_quality.runtime import run_validations

pandas_source = context.data_sources.add_pandas(name="local_comparisons")
# suite is already registered in context; LocalComparison uses local Ibis inputs.
definition, parameters = prepare_validation(
    context,
    pandas_source,
    duckdb_backend,
    LocalComparison,
    suite,
    name="local_account_survey_flow",
    sql_path="artifacts/local/flow_duckdb.sql",
)
results = run_validations(
    [definition],
    suite_directory=f"artifacts/{run_name}/suites",
    batch_parameters={definition.name: parameters},
)
```

DuckDB preparation evaluates the Ibis expression once and collects the entire
comparison into local memory. GX then validates that pandas result. This is the
existing tested local path; it does not use DuckDB's SQLAlchemy dialect for GX.
Compiled audit SQL uses the DuckDB backend, not Athena SQL transpilation. It does
not persist source fixture data and need not be a standalone replay script.

## Several definitions

Both adapters return a `(native_definition, batch_parameters)` tuple. Athena's
parameter dictionary is empty; DuckDB's contains its evaluated DataFrame.

```python
# prepared_flow and prepared_rollups are tuples returned by either adapter.
prepared = [prepared_flow, prepared_rollups]
results = run_validations(
    [definition for definition, parameters in prepared],
    suite_directory=f"artifacts/{run_name}/suites",
    batch_parameters={definition.name: parameters for definition, parameters in prepared},
)
all_passed = all(result.success for result in results.values())
```

`expectation_parameters` can likewise be supplied as a mapping keyed by definition
name, for suites using GX `$PARAMETER` values. Snapshot times and event IDs belong
to the Ibis query-builder arguments, not generic GX batch parameters.

A shared `RunIdentifier` groups the invocation; pass one explicitly to attach a
run name/time. GX stores results through each definition's configured Context,
and the runner returns the native results keyed by definition name. Configure
persistent GX stores outside the runtime if results must outlive the process.
The returned DataFrames and their parameters live only in this Python session.

Expectation failures do not skip later definitions. Execution/configuration
exceptions propagate immediately; GX may already have stored earlier results.
Duplicate definition names and unknown parameter targets fail before execution.
The runner does not run Checkpoint actions, retry, close supplied resources or
translate validation failures into process exit codes. A job entrypoint can use
`all_passed` to decide its exit status. If using a native GX Checkpoint, note that
its run parameters are shared; this runner exists to support separate frames and
parameters per definition.

## Serialize the suite used for each validation

`run_validations()` requires an explicit `suite_directory`. Immediately before
calling each native definition's `run()`, it writes `definition.suite.to_json_dict()`
as JSON. This records the actual registered suite, including expectation IDs,
field/branch lineage and builder-supplied values such as `expected_row_count`.
The validation then uses the same suite object; it is not rebuilt or loaded from
an independently maintained JSON file.

Files are named by execution sequence and a readable sanitized definition name,
for example `000_account_survey_flow.suite.json`. Each definition gets a snapshot
even when several definitions share a suite. Choose a new directory for every
run. Existing files are rejected to preserve earlier audit records. A write or
serialization failure stops execution before that definition is evaluated.
Snapshots remain available if validation subsequently fails or raises an error.

These files document suite configuration, not validation outcomes or source data.
GX stores validation results separately through the configured Context. Runtime
GX `$PARAMETER` placeholders remain symbolic in the suite: retain the supplied
`expectation_parameters` with your run metadata when using them. Python builders
remain authoritative; the snapshot is an audit artifact.

```python
import json
import great_expectations as gx

saved_suite = gx.ExpectationSuite(**json.loads(suite_path.read_text()))
```

`runtime.artifacts.save_suite(suite, path)` is also available for an explicit
release/documentation export without running a validation. It uses the same
native serialization and rejects overwrites.

## Glue and Spark

Glue is a hosting environment. An existing job script can call these adapters and
the runner. This package does not submit jobs or provision AWS resources; retain
that work in the existing deployment/Poe layer. The Athena path still performs
its data computation in Athena when called from a Glue job.

Verify runtime compatibility before deployment: GX 1.24 requires Python 3.10+,
while the documented Glue Python Shell runtime is Python 3.9. Do not assume this
bundle runs unchanged there. Use a compatible Glue Spark environment or another
supported Python host. No Spark execution adapter is included; add one only when
distributed comparison evaluation is required, and test the same NULL/decimal/
timezone/ordering behavior across backends. Do not use pandas collection for a
production-scale Spark comparison.

## Verification

The test suite runs full Flow and rollup suites through DuckDB -> pandas -> native
GX definitions, verifies separate frames and common run IDs, and covers failed
expectations, execution errors, parameter routing, suite JSON round trips, overwrite protection and SQL audit output. The Athena
adapter is tested with native SQLAlchemy/SQLite for a compatible SELECT shape;
complex Athena query preparation is tested without execution. Live Athena and
Glue execution remain unverified.

References:

- [GX Validation Definitions](https://docs.greatexpectations.io/docs/core/run_validations/create_a_validation_definition/)
- [GX run parameters/results](https://docs.greatexpectations.io/docs/core/run_validations/run_a_validation_definition/)
- [GX DataFrame sources](https://docs.greatexpectations.io/docs/core/connect_to_data/dataframes/)
- [Ibis DuckDB backend](https://ibis-project.org/backends/duckdb)
- [Glue Python Shell runtime](https://docs.aws.amazon.com/glue/latest/dg/add-job-python.html)
