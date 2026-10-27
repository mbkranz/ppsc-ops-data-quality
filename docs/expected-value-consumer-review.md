> Historical review of the previous ODCS/compiler integration. Current behavior is documented in [standalone definitions](metadata-compiler.md).

# Expected-value consumer implementation and PPSC review

This completes the offline consumer work from the October 24 Spaces plan. Review
after the cache-integrity and foreign-key changes. The Salesforce producer is
pinned at `1eedb2abcf5cac6471fb6cc45e5a40c007982854`; its independently built wheel
is stored under a source-revision directory and locked by its actual SHA256.

## Implemented behavior

- BEFORE, execution, and observed AFTER remain explicit independent states. The
  observed answer never selects its own expected value or presence condition.
- Every Flow field carries native assignment and determinism evidence. Assignment
  is provenance: retained BEFORE values are still checked when assigned is false.
- Unknown scope/computation fails completeness. Invalid comparison keys or join
  fanout block equality, while identity/uniqueness findings remain visible. Rollup
  source-parent duplicates are checked before aggregation can collapse them.
- Independent required/must-be-null predicates remain nullable and source-bound.
  Native GX checks consume their named columns. No new org policy is selected.
- Native pair checks retain both-NULL `missing_count` and their scoped denominator;
  one-sided NULLs fail. Runtime native findings carry `validation_record_id`.
- Suite metadata retains ODCS source definitions and stable BEFORE/expected field
  pointers. Expected properties explicitly map to `expected__<field>` columns;
  original authored properties retain their precedence.
- Selected native COUNT/SUM/MIN/MAX handoffs have executable synthetic coverage.
  The new comparison function receives its verified `MetadataBundle` explicitly
  and requires a validated request with an explicit empty/all-null policy. It
  returns a native Ibis table. Existing workbook rollups are retained until org
  definitions and policies have been reviewed.

## Corrections found during review

ODCS alias-preserving serialization prevents loss of the nested schema. Native
source pointers are not prefixed with `/Metadata` twice. Public native-rollup
inputs are explicit, and expected output physical names match prepared columns.
Evidence outputs and structural flags have corresponding lineage entries.

The SQL renderer retains shared CTEs inside a SELECT-first input relation, uses
compact runtime SQL, and verifies UTF-8 length before registering a GX asset.
This corrects a generated comparison that exceeded
[Athena's query quota](https://docs.aws.amazon.com/athena/latest/ug/service-limits.html).
Native DuckDB execution verifies CTE naming, self joins, NULL behavior, duplicate
observations and source-row preservation; native SQLite/GX verifies the SQL asset.

The installed-bundle smoke check bypasses uv's wheel cache. Before the correction,
the rebuilt and bundled wheel contained the new code but the same-version install
used old cached bytes. The corrected check installs and exercises the supplied
bundle without an index.

## Verification and limits

Executed scoped Ruff/formatting, the full offline suite, native query/result
regressions, query compilation, 56 native synthetic expectations (30 Flow and
26 rollup), diagram generation, actual four-stage DVC reproduction, freshness,
and installed-bundle smoke. Public-boundary and final expected-contract mapping
checks were rerun after their review corrections. DVC analytics was disabled.
Producer: Python 3.11.17, uv 0.12.23, pip 25.3; GX 1.24.0, Ibis 12.0.0,
DuckDB 2.0.0 and SQLGlot 30.24.0. The selected producer metadata package's 62 tests
also passed independently on Python 3.12.

No registry, relational DSL, acquisition layer, custom GX engine, or new live
operation was added. Poe and the four DVC release producers retain ownership.
No merge, deployment, publication, source refresh or live query was performed.
Reviewed org metadata/contracts, actual native rollup policies, physical catalog
bindings and live Athena/Glue acceptance remain adoption requirements. Survey
workflow ownership, optional displayed-question policy and governance acceptance
remain separate NIOCCS work.
