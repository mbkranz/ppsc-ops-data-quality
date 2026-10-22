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

## Development workflow

Use AWS Glue with the `data-migration-dev` local profile for normal development.
Populate the ignored YAML runtime and environment files with verified bindings,
build a release, render its deployment plan, deploy, and submit a settled event:

```bash
uv sync --locked --python 3.11
uv run poe plan-deployment --environment dev --output build/deployment-dev
uv run poe deploy --plan build/deployment-dev --operation create
# Upload/hash params.local.yaml, then:
uv run poe run-glue --plan build/deployment-dev \
  --config-uri s3://YOUR_CONFIG_BUCKET/run.yaml --config-sha256 YOUR_SHA256
uv run poe glue-status --plan build/deployment-dev --run-id RETURNED_JOB_RUN_ID
```

These tasks default to `data-migration-dev`; `--profile PROFILE` explicitly overrides
it. Follow [build and deployment](docs/build-deployment.md) to build the required
bundle, review the plan and inspect terminal status and report evidence. A submitted
run ID alone does not establish successful validation. Glue uses its execution
role; local profile names do not belong in its runtime configuration.

Credential-free checks remain available for CI and bounded synthetic verification:

```bash
uv run poe check
uv run poe check-queries
uv run poe check-synthetic
uv run poe suite-diagrams
```

`check-queries` compiles illustrative Athena comparisons and serializes the native
27/24-expectation baseline suites. `check-synthetic` validates independently authored
DuckDB history, checks all 53 expectations (28 Flow + 25 rollup), and verifies
53 uniquely identified expectation rows, two validation summaries, native results,
registered suites, exact SQL, Data Docs and the manifest. Outputs use fresh paths
under `build/checks/`; existing destinations are rejected. To choose a destination,
run `python -m scripts.check_validation compile|synthetic --output PATH`.
These are development scripts and are excluded from the installed package.

## Organization

```text
src/ppsc_ops_data_quality/
    account_to_survey_results/
        queries.py              # Ibis derivations and history comparisons
        gx.py                   # Authoritative native GX suite builders
        lineage.py              # Field, branch and original-source provenance
        schemas.py              # Schemas inferred from actual queries
    core/
        schemas/                # Account, Contact, Survey Result and history inputs
        queries/                # Pure snapshots, unbound history, optional SQL lineage
        configuration.py        # Shared YAML loader; rejects duplicate keys
    runtime/
        glue.py                 # Argument handling and role-based bootstrap
        resources.py            # Injected S3 retrieval and checksum verification
        configuration.py        # Pydantic runtime input contracts
        validation.py           # Shared Athena orchestration and result contract
        data_access.py          # Backend catalog discovery
        athena.py, duckdb.py     # Separate native GX preparation adapters
        runner.py, reports.py   # Engine-independent execution and publication
        report_schemas.py       # Athena-discoverable report projections
    gx_queries.py, views.py      # Generic SQL registration and optional view publishing
    cli.py                      # Installed ppsc-dq validate command
scripts/check_validation.py      # Development-only synthetic fixtures/checks
scripts/generate_suite_diagrams.py
params.example.yaml             # Illustrative runtime bindings
glue/job.yaml                  # Configurable Glue hosting settings
glue/environments.example.yaml  # Illustrative deployment targets
```

The runtime accepts native Ibis tables. Athena compiles a final comparison into a
GX Query Asset; DuckDB evaluates a bounded comparison for synthetic checks. The
shared runner serializes the registered suite immediately before validation.
Reporting adds Data Docs, gzip native JSON, Parquet discovery datasets and explicit
S3 publication. Pydantic models validate structured configuration and completed-run
receipts; expressions, dataframes and GX objects retain their native interfaces.

## Use the library

```python
from ppsc_ops_data_quality.account_to_survey_results.queries import flow_account_query
from ppsc_ops_data_quality.core.queries import history_tables

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
`runtime.data_access.bind_history_tables()`. For combined history, construct explicitly scoped
Ibis relations upstream. Neither binding path infers object discriminators or
silently fixes column casing.

The Flow query selects one verified triggering event, looks up related surveys at
execution, derives expected Account AFTER values from Account BEFORE, and compares
with an independently observed settled AFTER snapshot. Caller-supplied timestamps
must satisfy BEFORE < execution < AFTER. Current Account state cannot validate all
historical events. Rollups use one common effective point at a person Account grain,
including zero-child Accounts.

## Run directly against Athena

`ppsc-dq validate` provides the packaged GX/SQLAlchemy runtime; the example script delegates to it:

1. Copy `params.example.yaml` to ignored `params.local.yaml`.
2. Bind the actual databases and verify the physical columns/types, validity
   intervals, deletion semantics and completed delivery/event timing.
3. Set standard AWS credentials/profile outside the configuration file.
4. Run with a new output directory:

```bash
uv run ppsc-dq validate \
  --config params.local.yaml --run-dir build/athena-run-001
```

The example uses an existing Athena workgroup/results location and a required
`[reports].s3_uri` destination; it creates no views or tables. Native GX
result/configuration stores are written under the run directory. Reports are
built locally and uploaded after every invocation, including ordinary failed
expectations. Completed earlier results are also reported on an execution error.
Schema overrides supplement the explicit input profiles; no automatic
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

Glue 5.0 hosts the same Athena runtime on Python 3.11. Build a hashed wheel bundle,
render an account-checked deployment plan, create/update the job, and submit a
hash-pinned runtime configuration through Poe. See the
[build, deployment and Glue acceptance plan](docs/build-deployment.md) for commands,
reference review, rollback and remaining live acceptance. Athena executes the SQL;
the Glue driver does not initialize Spark.

## Rules, schemas and lineage

The Flow suite has 27 built-in expectations and the rollup suite has 24, each with
an optional independent row-count check. They cover required columns, identity,
unique grain, permission-lookup resolution and 19 expected/observed field pairs.
The synthetic check supplies counts of one, yielding 28 and 25 expectations respectively.

Flow row checks use the named Ibis predicate
`survey_completion_occurred_on_or_after_launch`, consumed by the GX
`POST_LAUNCH_COMPLETION` row condition. It compares the calendar date of
`Survey_Result__c.Completion_Status_Timestamp__c` with the inclusive launch date
`2024-12-16`. Normalize timestamps to the agreed business timezone upstream;
the query does not infer or convert it. The completion timestamp and predicate
remain in the comparison, and no launch filter removes rows from the query.
All Flow row checks, including the optional count, validate only that cohort;
the required-columns check remains batch-wide. CABOR also requires a deterministic
lookup. Rollup checks retain their separate snapshot contract.

Pre-launch records and NULL completion timestamps remain available for profiling
but are excluded from Flow row checks. A NULL timestamp gives a NULL predicate;
it is not classified as migrated. Migration reconciliation and independent
timestamp/population coverage checks remain separate work. When supplied, the
Flow `expected_row_count` must count post-launch source events independently.

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
by stable projected alias when `projection_lineage=PROJECTION_LINEAGE` is explicitly
supplied by domain orchestration; generic compilation omits domain annotations. SQL comments explain generated queries; arbitrary
structured metadata is not preserved by ordinary SQL or Ibis schema round trips.

The runner requires a run-scoped `suite_directory` and serializes the actual
registered suite immediately before each native validation. IDs, configured row
counts and field/branch metadata are retained. Existing suite snapshots are not
overwritten. GX `$PARAMETER` values remain symbolic in the suite; retain runtime
expectation parameters separately with your run metadata.

## Documentation and follow-up work

Generate the suite diagrams with Graphviz's `dot` executable installed (for example,
`sudo apt-get install graphviz` on Ubuntu):

```bash
uv run poe suite-diagrams
# Or choose one suite and an output directory:
uv run python scripts/generate_suite_diagrams.py --suite flow --output build/suite-diagrams
# Optional native expression diagnostic, using Ibis's unchanged formatting:
uv run python scripts/generate_suite_diagrams.py --include-expression-graph --output build/suite-diagrams
```

Each suite gets an overview grouped by exact GX row condition and expandable
Markdown sections for fields, identities, lookup evidence and table/schema checks.
Each section has a small SVG/DOT diagram connecting the actual target columns to
their expectations. Paired expected and observed columns stay together; the
shared row condition appears once as the enclosing scope label. Each expectation
also retains its exact condition in the accompanying table.

The default diagrams use ordinary Graphviz clusters and styles, with no dependency
on Ibis operation IDs or a JavaScript application. The optional diagnostic is the
unmodified native Ibis expression graph. Both use illustrative unbound queries
and execute no data. Regeneration replaces generated documentation, and CI
verifies the generator. Keep generated diagnostic graphs under `build/`.

- [Flow suite diagram](docs/suites/account_to_survey_results_flow.md)
- [Rollup suite diagram](docs/suites/account_to_survey_results_rollups.md)

- [Query composition and original sources](docs/query-design.md)
- [Schema contracts and conversions](src/ppsc_ops_data_quality/core/schemas/README.md)
- [Runtime setup and native definitions](src/ppsc_ops_data_quality/runtime/README.md)
- [Authored SQL-file execution and metadata/comment standards TODO](src/ppsc_ops_data_quality/runtime/TODO.md)
- [Build, deployment and Glue acceptance](docs/build-deployment.md)
- [S3 reports, format decision and catalog registration](docs/validation-reports.md)
- [Athena catalog DDL templates](sql/validation_reports_catalog.sql)

Authored SQL-file execution remains deferred. Before implementing it, agree a
versioned comment/manifest convention, stable column lineage IDs, typed parameter
binding and audit/round-trip behavior. Generated SQL files are not runtime inputs.

A Query Asset or normal Athena view does not promise one computation for all GX
metrics. Measure query count, scan bytes and runtime before adding materialization.
Deployment is explicit through Poe. No data cleaning or quarantine behavior is included.
