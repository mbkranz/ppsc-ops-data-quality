# PPSC operational data quality

Compare native Salesforce Flow outputs and authored Account survey rollups with
independently observed lake history using SQLGlot SELECTs and native Great Expectations.
The application preserves duplicate matches, missing parents, assigned NULLs,
unknown computation and unassigned BEFORE values.

The Salesforce dependency is pinned to commit
`4ce491c3266e052bf1e1f6a70e8f7d2aed86f9f1` and its immutable wheel SHA256 in
[vendor/4ce491c/source-receipt.json](vendor/4ce491c/source-receipt.json).
Version `0.1.1` alone is insufficient identity.

## Application

```text
src/ppsc_ops_data_quality/
    io.py                       # explicit DDL/capture reads and exports, YAML
    runtime.py                  # native GX registration, checks, execution, reports
    account_to_survey_results/
        queries.py              # lake bindings, native Flow SELECT, comparisons
        suites.py               # authoritative native GX suite builders
        workflow.py             # visible composition and validated runtime settings
        metadata/               # saved native Flow and provisional offline lake DDL
    cli.py, glue.py              # hosting entry points
```

Flow generation delegates to `salesforce.entities.flows.to_sqlglot(..., simplify=True)`.
Ops binds `Flow_Record` and each named lookup role to independent effective snapshots.
It does not interpret Flow decisions, formulas, assignments or lookup filters.
Ibis remains only for authored rollups, relational history composition and report schemas;
completed expressions are converted to SQLGlot in the domain module. The shared runtime
accepts final native SELECTs and has no domain imports.

## Checks

```bash
uv sync --locked
uv run poe check
uv run poe check-queries
uv run poe check-synthetic
uv run poe render-queries
uv run poe suite-diagrams
```

The reproducible producer requires Linux x86_64, Python 3.11.17, uv 0.12.23 and pip
25.3. Run `uv run poe build-release --backend local` in that prepared environment.
Poe owns operations; root DVC retains exactly four release producers. Live validation,
deployment and publication are never cached. See [portable builds](docs/portable-build.md)
and [deployment](docs/build-deployment.md).

Offline synthetic checks validate 30 Flow and 26 rollup expectations, independent
observations, native results, exact suite snapshots, Data Docs, typed Parquet reports
and manifest publication. These checks do not establish live Athena/Glue acceptance.

## Inputs and execution

Read [native inputs and lake bindings](docs/metadata-compiler.md) and
[query authoring](docs/query-design.md). `params.example.yaml` names an explicit input
directory, source org/version, physical locations, independent BEFORE/execution/AFTER
instants, org-local Flow date, verified trigger eligibility and physical snapshot IDs.
The bundled DDL is a provisional offline profile; live execution rejects it and requires
complete selected native field evidence plus reviewed lake definitions. No native
precision/scale is inferred from lake types.

```bash
ppsc-dq validate --config params.local.yaml --run-dir build/runs/unique-run
```

Use `data-migration-dev` for local AWS operations unless explicitly overridden.
Glue uses its execution role. Keep credentials, live settings and record-level results
out of Git. Queries in `sql/` are generated review artifacts; execution from an authored
SQL file requires the explicit versioned sidecar path described in the authoring guide.

The [implementation plan and review](docs/specs/minimal-implementation-plan.md)
records current decisions, verification and remaining live-input requirements.
