> Historical release evidence for the predecessor at `39c5139`. Current schema ownership
> and provenance are documented in [native compilation](../metadata-compiler.md).

# Frozen native-query release

The consumer pins `ppsc-salesforce[ibis]==0.1.0` from Salesforce revision
`1d59b5b87b69e2b7da52c3c0bdb008c2af37c200`. Its wheel is checked into
`vendor/1d59b5b8/ppsc_salesforce-0.1.0-py3-none-any.whl` with SHA256
`7d588d32c56c1890a5b2988b3d7b4981042aa6ee1de5b829d58e936c93b240ec`.

The selected APMP product contributes `tables.json` and the original native Flow,
source catalog and saved observed catalog. The producer's single authored ODCS
definition generates schema types, aliases, keys and relationships. Ops does not
install ODCS, the APMP package or Salesforce acquisition SDKs.

Validation uses existing operational entry points:

```bash
uv run --locked --python 3.12.14 poe check
uv run --locked --python 3.12.14 poe check-queries
uv run --locked --python 3.12.14 poe check-synthetic
uv run --locked --python 3.12.14 poe render-queries
uv run --locked --python 3.12.14 poe suite-diagrams
UV_PROJECT_ENVIRONMENT=.venv-release UV_PYTHON=3.11.17 uv run --locked --only-group release poe build-release
```

The release producer uses uv 0.12.23, Python 3.11.17 and pip 25.3. DVC runs the
real requirements, dependency, wheel and bundle producers. Installed smoke uses
`--no-index --no-cache`, checks package compatibility and selected native imports,
compiles queries and executes all 56 synthetic GX expectations. The synthetic
report has two validation summaries and 56 expectation rows.

The offline compile and synthetic gates pass. Final test and freshness results
are recorded in the PR description. These checks do not establish live lake
acceptance; the saved catalog remains provisional synthetic evidence.
