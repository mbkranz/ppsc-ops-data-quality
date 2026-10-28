# Frozen Salesforce compiler

`a534c633/ppsc_salesforce-0.1.1-py3-none-any.whl` is `ppsc-salesforce==0.1.1`
from [PR #7](https://github.com/mbkranz/ppsc-salesforce/pull/7), whose
`codex/native-athena-products` head was resolved on October 28, 2026 to
`a534c63353680e41d12e3b55997a125ba703c675`.

SHA256: `635ee8ac99d375cb318e33d809e6a6efac8a7e96707a3292a08a1637435a9ba0`.

Ops selects the `ibis` extra. Salesforce acquisition SDKs and ODCS/workbook
dependencies are absent from this runtime. The compiler supplies native Flow,
rollup and field-definition interpretation; Ops retains the physical schema
consumer adapter and saved input selection. The old Salesforce APMP project was
removed upstream; this update neither relocates a producer nor refreshes metadata.

## Reproduce

Prepare Salesforce's locked development environment (`uv sync --locked --group
pipeline`). The verified build used Python 3.12.14, build 1.6.1 and setuptools
80.9.0 from that environment. Export the exact commit into a clean directory to
exclude stale setuptools output:

```bash
git archive a534c63353680e41d12e3b55997a125ba703c675 | tar -x -C CLEAN_DIRECTORY
cd CLEAN_DIRECTORY
SOURCE_DATE_EPOCH=315532800 /PATH/TO/SALESFORCE/.venv/bin/python -m build --wheel --no-isolation
```

Two independent clean exports produced the hash above. All 164 packaged source
and template files were compared byte-for-byte with the pinned source. Ops'
installed distribution must have this wheel's `direct_url.json` path, matching
lockfile/archive hash and byte-identical installed package files; version alone is insufficient.

For a reviewed compiler update, use a new source-revision directory, update the
requirement and lock without upgrading unrelated packages, regenerate affected
SQL/suites/diagrams, and reproduce the four offline DVC release producers and
installed smoke through Poe. Change saved input representations only when source
compatibility requires it; retain the native Flow/version/evidence.
