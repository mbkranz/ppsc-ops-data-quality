# Ops-owned physical definitions

The current implementation replaces the generated APMP `tables.json` handoff
with reviewed schema-only Athena DDL and explicit application bindings in
`account_to_survey_results`. The reusable source compiler remains in Salesforce.
No ODCS or Salesforce acquisition dependency is installed in Ops.

Source-specific schema constants now live in the domain package. Core receives
native tables/schemas and explicit comparison and provenance mappings. The Athena
reader and online discovery/capture scripts moved into Ops with focused tests.
Physical types are authored only in DDL; native Ibis type lists are derived in
memory. Existing authored descriptions/policies remain in `definitions/descriptions.json`.

Original native field metadata and Flow fragments travel through explicit
`PROJECTION_LINEAGE` mappings and final SQLGlot node metadata. Comments are safe
summaries; AST serialization and GX metadata retain machine-readable evidence.
Source coverage, definition digest and provisional approval remain distinct.

## Local release verification, 2026-10-27

Ops explicitly pins `duckdb==1.5.6`. The previous DuckDB 2.0.0 bundle installed
and compiled queries but failed with SIGILL during native import. This producer's
translated CPU exposes no AVX/AVX2, FMA, BMI or XSAVE support, matching the
[upstream CPU-baseline issue](https://github.com/duckdb/duckdb/issues/27691).
A separate diagnostic changed only DuckDB to 1.5.6 and passed all 56 synthetic
expectations before the actual pin and release rebuild.

The reviewed implementation was built with `--platform linux/amd64`
using `python:3.11.17-slim-bookworm` (image digest
`sha256:f06d01d4ba3f8ad5af45a3ec87df19c1d317d8e8961edc0fabda61811af6f7cf`).
The producer verified Linux x86_64, glibc 2.36, Python 3.11.17, uv 0.12.23,
pip 25.3 and locked Hatchling 1.27.0 before running
`uv run --no-sync poe build-release --backend local`.

Only DuckDB changed among the 149 locked package records; Ibis 12 and Salesforce
compiler 0.1.1 remain unchanged. All four DVC producers completed. The actual
`dvc.lock` records the requirements,
58 dependency wheels, application wheel and final bundle. Both independent
reviewers verified the lock/output identities and the bundle's 59 unique wheels.
The compiler wheel is 0.1.1 and matches its vendor receipt and runtime lock.

| Output | SHA256 |
| --- | --- |
| Runtime requirements | `80c5354efa2e3a6f015f101f6819f6a680044074e0571fb5045d9450ac5fb376` |
| Application wheel | `2974cdd5e37d168749d6e0d99249e3c677be39ea98fbcbf30c0b0fa05ec3b62f` |
| Final bundle | `acbf9e684e80477649626c01a4e7995db4c032e7d52e46791d54537b680d83d2` |

The bundle contains exactly one DuckDB 1.5.6 wheel and no DuckDB 2.0 wheel.
The application wheel declares the direct pin; its 45 application payload files
match the source and are unchanged from before the pin. Authoritative
`dvc status dvc.yaml --quiet` passed inside the pinned producer. The new `uv.lock` SHA256 is
`ec86b31a79e8cc25918db4f247165b01605f4a566a6beea9b6079c46ae06e56c`.

The original full installed smoke passed with a fresh environment. It installed
all 59 packages without an index or cache,
checked dependency compatibility, verified installed package identity/provenance,
checked CLI behavior, and compiled two baseline suites containing 29 and 25
expectations, then executed all 56 synthetic expectations (30 Flow and 26 rollup).
Saved results contain 56 expectation rows, two validation summaries, native GX
JSON, registered suites, compiled query SQL, complete Data Docs and a completed
success manifest. This is the rebuilt frozen bundle's smoke result, separate
from the earlier diagnostic environment.

Independent review checked the Flow fragments and field definitions in the
actual GX results against the packaged source records and digests. Source
coverage remains provisional. No release publication was performed.

`poe check` passed lint, formatting and all 274 tests on the pinned Linux
producer, with no skips. This includes the full release integration fixture:
forced wheel and archive rebuilds preserve bytes, source changes invalidate
outputs, version-only changes reuse dependency downloads, fresh local Git/DVC
retrieval succeeds, final-bundle-only verification succeeds, and corruption in
the isolated local store is rejected. The fixture's requirements, application
wheel and bundle are byte-identical to the release files above. The required
`poe check-queries` and `poe check-synthetic` commands also passed.

No online Salesforce/AWS operation, deployment, or live lake acceptance is claimed.
The selected catalog and physical schema profiles remain synthetic provisional
fixtures. See [native compilation](../metadata-compiler.md) for active boundaries
and commands.
