# PPSC operational data quality

Compute expected Account values from Survey Result history with Ibis, then compare
them with independently observed Account values using native Great Expectations
(GX) suites. Run the same query builders against Athena or bounded local DuckDB
data. Athena DDL profiles supply input schemas; reviewed local Ibis builders own
Flow projections, bindings, history and rollups. Python owns native GX suites.
Salesforce tooling is an optional offline authoring producer; neither it nor ODCS
is an installation or execution dependency.
SQL and suite JSON are generated review and run-audit artifacts.

The first implementation covers the Survey Result completion Flow and 19 Account
survey rollups. It preserves the relationship
`Survey_Result__c.Participant__c -> Contact.Id -> Contact.AccountId -> Account.Id`,
missing parents, duplicate matches, assigned NULLs and unchanged prior values.

The local Flow definition is provisional and pins QA2 Flow version
`301SL00000dpJqKYAU`. See [metadata compilation](docs/metadata-compiler.md) for the
artifact boundary, native behavior changes and remaining local acceptance work.

## Development workflow

Use AWS Glue with the `data-migration-dev` local profile for normal development.
Populate the ignored YAML runtime and environment files with verified bindings,
build a release, render its deployment plan, deploy, and submit a settled event:

```bash
uv sync --locked --python 3.11
uv run --no-sync poe plan-deployment --revision EXACT_RELEASE_SHA --environment dev --output build/deployment-dev
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
uv run poe check-standalone
uv run poe suite-diagrams
```

`check-queries` compiles illustrative Athena comparisons and serializes the native
29/25-expectation baseline suites. `check-synthetic` validates independently authored
DuckDB history, checks all 56 expectations (30 Flow + 26 rollup), and verifies
56 uniquely identified expectation rows, two validation summaries, native results,
registered suites, exact SQL, Data Docs and the manifest. Outputs use fresh paths
under `build/checks/`; existing destinations are rejected. To choose a destination,
run `python -m scripts.check_validation compile|synthetic --output PATH`.
These are development scripts and are excluded from the installed package.
`check-standalone` builds a wheel, verifies its installed origin in an isolated
environment without producer packages, and runs the same compilation and complete
synthetic-report checks. `author-salesforce` is a separately invoked optional
producer; see [definition authoring](docs/metadata-compiler.md).

## Organization

```text
src/ppsc_ops_data_quality/
    account_to_survey_results/
        metadata.py             # Verified definition receipt and detached evidence
        flow.py                 # Reviewed native Ibis Flow builders
        input_schemas.py        # Native composition of Athena DDL input profiles
        inputs/                 # Schema-only Athena declarations
        history.py              # Explicit domain history/catalog bindings
        validation.py           # Account/Survey application orchestration
        metadata/               # Pinned native Flow, catalog and manifest
        queries.py              # Ibis history/comparisons and existing rollups
        gx.py                   # Authoritative native GX suite builders
        lineage.py              # Field, branch and original-source provenance
        schemas.py              # Schemas inferred from actual queries
    core/
        schemas/                # Domain-independent Athena DDL conversion
        queries/                # Pure snapshots and optional SQL lineage
        configuration.py        # Shared YAML loader; rejects duplicate keys
    runtime/
        glue.py                 # Argument handling and role-based bootstrap
        resources.py            # Injected S3 retrieval and checksum verification
        configuration.py        # Pydantic runtime input contracts
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
from ppsc_ops_data_quality.account_to_survey_results.history import history_tables

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
`account_to_survey_results.history.bind_history_tables()`. For combined history, construct explicitly scoped
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
2. Confirm the metadata org, exact Flow version and manifest SHA256 match the
   reviewed installed inputs. The runtime rejects a mismatched selection before
   connecting. Bind the actual databases and verify the physical columns/types, validity
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

The Flow suite has 29 built-in expectations and the rollup suite has 25, each with
an optional independent row-count check. They cover required columns, identity,
unique grain, permission-lookup resolution and 19 expected/observed field pairs.
The synthetic check supplies counts of one, yielding 30 and 26 expectations respectively.

Flow row checks use the named Ibis predicate
`survey_completion_occurred_on_or_after_launch`, consumed by the GX
`POST_LAUNCH_COMPLETION` row condition. It compares the calendar date of
`Survey_Result__c.Completion_Status_Timestamp__c` with the inclusive launch date
`2024-12-16`. Normalize timestamps to the agreed business timezone upstream;
the query does not infer or convert it. The completion timestamp and predicate
remain in the comparison, and no launch filter removes rows from the query.
All Flow row checks, including the optional count, validate only that cohort;
the required-columns and scope-completeness checks remain batch-wide. CABOR also requires a deterministic
lookup. Rollup checks retain their separate snapshot contract.

Pre-launch records and NULL completion timestamps remain available for profiling
but stay outside value equality. A NULL timestamp gives a NULL predicate and fails
the completeness check;
it is not classified as migrated. Migration reconciliation and independent
timestamp/population coverage checks remain separate work. When supplied, the
Flow `expected_row_count` must count post-launch source events independently.

Two NULLs are excluded together by the pair equality policy; a one-sided NULL
fails. Unresolved pediatric-permission lookups fail their determinism check; only
each field comparison requires its own complete computation evidence. Assignment
is provenance: unassigned fields still compare against retained BEFORE values. Empty batches require an explicit
source count if they must fail. Duplicate observations and missing parents survive
LEFT JOINs so the suites can detect them.

Schemas are ordinary `ibis.Schema` definitions, with full declarations for their
named validation-input projections. Derived schemas come from actual expressions.
Arrow is an interchange conversion, not a second authored schema. Source fields
stay nullable so GX can detect invalid raw values. The schema-only DDL profiles retain the prior precision and field types.
Field provenance remains separate from the input-type authority.

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

Generate native Ibis table graphs with Graphviz's `dot` executable installed (for example,
`sudo apt-get install graphviz` on Ubuntu):

```bash
uv run poe suite-diagrams
# Or choose one suite and an output directory:
uv run python scripts/generate_suite_diagrams.py --suite flow --output build/suite-diagrams
```

Each comparison is split into native Ibis graphs at meaningful function/table
boundaries: snapshots, event selection, `join_account`, routing, each Flow lookup,
final Flow decisions/age, `expected_account_values`, observation binding and the
final comparison. Rollups separate snapshots, `expected_survey_rollups` and their
comparison. The Markdown indexes show each part's builder, named inputs and output.

Each part receives schema-preserving unbound tables for prior stages, so its graph
does not expand the entire upstream pipeline. These are **diagram-only
boundaries**: runtime queries are unchanged and no tables are actually materialized.
Graphs are exported with `ibis.expr.visualize.to_graph()` as SVG and DOT, retaining
Ibis's native nodes, edges and labels. Colors and clusters use the **parent entity**:
Salesforce objects own fields (including both expected and observed values), and
the source Flow owns its decisions, formulas and lookup evidence. Existing
projection/Flow lineage supplies these parents; source-object ownership is carried
through the diagram-only table boundaries. Shared expressions, mixed-object
relations and unmapped query mechanics stay neutral gray. Each page includes a
color legend; cluster labels and node tooltips also identify the parent.
There are no GX overlays. Graphs show query construction, not GX checks or
validation outcomes, and execute no data.
Native Ibis node IDs are process-dependent, so regenerated graph files need not
be byte-identical. CI verifies Ibis structure, parent ownership and boundary schemas.

- [Flow table graph](docs/suites/account_to_survey_results_flow.md)
- [Rollup table graph](docs/suites/account_to_survey_results_rollups.md)

- [Query composition and original sources](docs/query-design.md)
- [Reusable comparison boundaries for other objects, mappings and surveys](docs/reusable-comparisons.md)
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

## Linux and Windows release preparation

See [portable release builds](docs/portable-build.md) for automatic local/GitHub
build selection, exact-revision lock handoff and the separate publication gate.
