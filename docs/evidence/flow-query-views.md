# Expected Flow view implementation and PPSC review

## Scope and interfaces

Implemented the [plan](../specs/flow-query-views-plan.md) on top of Ops PR #14's
canonical-query boundary. Optional `flow_view` configuration extracts its existing
`Expected_Account` CTE into one UUID-named Athena view. The native Salesforce compiler,
vendored wheel, dependency versions and GX suite builders are unchanged.

`views.py` colocates validated configuration/request/receipt models, native SELECT
extraction/rendering and explicit create/drop functions. Clients and query execution
options are supplied. The workflow visibly binds snapshots, extracts the view,
checks statement sizes, saves definitions, creates the view, registers suites, reports
results and cleans up. Existing inline execution remains compatible. No registry,
general DAG planner, new package dependency or materialization layer was added.

## PPSC review findings and resolutions

Reviewed against `AGENTS.md` and the installed
`.agents/skills/design-python-contracts/SKILL.md`, including its configuration,
effectful-operation and visible-workflow examples.

| Finding | Resolution |
| --- | --- |
| Canonical/GX output renames copied stale native output-column references. | Remap only current value/assigned/deterministic and record-identity columns at each boundary; retain original compiler names in explicitly named native provenance. Execute invariants against emitted aliases. Native graph identities remain unchanged. |
| The expected relation must be a stable projection boundary. | Extract the existing explicitly named top-level CTE; preserve every output and metadata entry. Reject wildcard/duplicate outputs, unsupported SELECT shape, outer-CTE dependencies and external qualified columns. Do not scan compiler stages or reconstruct Flow semantics. |
| Snapshot binding after extraction could version a view or lose hidden source pins. | Pin underlying expected reads before CREATE; independently pin the observed read in the short query. Carry transitive base-source provenance and DDL/lineage dependency files. |
| Rejoining context using event Id would multiply duplicate occurrences. | Keep context in the canonical expected projection. Native occurrence row numbers remain internal to that definition; no cross-view row-number join. |
| Replacing shared views could mix concurrent validation runs. | Generate UUID-suffixed names, issue plain CREATE without replacement and drop only after a successful creation receipt. Record failed/ambiguous creation and its diagnostic query ID without claiming ownership. |
| Cleanup errors must not hide validation/publication errors or leak the engine. | Cleanup runs in finally; simultaneous errors propagate as ExceptionGroup, final cleanup status is recorded locally and engine closure has its own finally. |
| Reports would otherwise contain a small query whose dropped dependency was unavailable. | Publish exact dependency definitions, hashes, outputs and lineage in the existing query-artifact allowlist. Creation metadata is published before cleanup; final cleanup status is explicitly local. |
| Core helpers must remain domain independent and rendering must fail on unsupported SQL. | Use a generic query-view prefix in the shared module, pass the CTE boundary from the domain workflow, reuse the bounded Athena executor and render CREATE with unsupported generation set to raise. |

## Complexity

One new application module (`views.py`, approximately 175 lines) and one focused test
module. Existing domain/runtime/report functions are extended directly. No dependency,
compiler pin, public suite implementation, release stage or operational dispatcher was
added. Generated SQL and suite metadata account for most changed artifact lines.
The simpler alternative of retaining only inline CTEs cannot reduce submitted statement
size. Automatic DAG partitioning and CTAS would add lifecycle and planning responsibilities
without a demonstrated need for this first boundary, so they remain deferred.

## Executed verification

The pinned producer is Linux x86_64, Python 3.11.17, uv 0.12.23 and pip 25.3.

| Check | Result |
| --- | --- |
| `poe check` | Passed: lint/format and all **203 tests**, including isolated release build/retrieval integration |
| `poe check-queries` / `poe render-queries` | Passed; inline and view-based examples compiled/regenerated |
| `poe check-synthetic` | All 56 native expectations passed (30 Flow, 26 rollup) |
| Full Flow view parity | Actual DuckDB view versus inline SQL matched for ordinary inputs, duplicate inputs/parents/observations, missing AFTER, assigned NULL and unknown eligibility |
| Real SQL GX | SQLite view validated through native GX; complete submitted statements remained below 10 KB; dependency JSON was retained in report artifacts |
| Lifecycle | Success, failed expectations, publication errors, failed CREATE, cleanup failure, combined publication/cleanup failure, timeouts, status failures and cancellation failures exercised; errors retain submitted query IDs |
| Compatibility | All 29 committed Flow check definitions and check IDs match the predecessor; only lineage metadata changed |
| `poe build-release --backend local` | Complete; real four-stage DVC production and fresh index-free installed smoke passed |
| Installed source inspection | All ten installed application Python files match final source byte-for-byte |
| `dvc status dvc.yaml --quiet` | Exit 0 after the final release build |

Measured statement sizes exclude illustrative comments and terminal semicolons:

| Statement | UTF-8 bytes |
| --- | ---: |
| Existing inline GX base query | 251,644 |
| Illustrative CREATE VIEW | 229,498 |
| Illustrative comparison through view | 26,009 |
| CREATE VIEW with representative physical snapshot pins and runtime wrapper | 234,937 |
| Comparison with independent observed snapshot pin | 26,037 |

Final release SHA256 identities:

- Application wheel: `7b6c667008451eeaf1cab2c7e0b3131870e9d570fb03d508de658699119a745c`.
- Runtime bundle: `152871ab2bdcc1bb65819fa170cf498da1727dfc91e2dfa942d2055cac93d7c0`.

Only final successful gates establish the stated results. Earlier fixture assertions
were corrected before the final gate; an intermediate run using those assertions is
not an acceptance result. No source acquisition, live Athena call, release publication
or deployed Glue execution was performed.

## Acceptance limits

Synthetic DuckDB and SQLite GX execution is not live Athena acceptance. Actual CREATE
VIEW with reviewed native captures, schema types, selected Iceberg snapshots, permissions
and complete GX statements remains required. Nested view expansion may remain expensive;
this change establishes a statement-size boundary and does not claim materialization,
cross-table atomicity or performance improvements. Failed/ambiguous CREATE queries require
inspection using their recorded query ID/location before manual cleanup.
