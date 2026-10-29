# Native Flow SQL implementation plan and review

Updated October 28, 2026. Implements the [minimal brief](../minimal-implementation-brief.md)
on Ops base `035ae5fedf4f63393f8e92e04336ec22ea4725ea` (`codex/refactor-handoff`).
The brief overrides older module/compatibility guidance. No backwards compatibility
layer, provider registry, second Flow interpreter, dbt or new query framework is retained.

## Updated source contract

Use the reviewed Salesforce commit `4ce491c3266e052bf1e1f6a70e8f7d2aed86f9f1`, replacing
the original plan's `d024c15` baseline. The immutable 0.1.1 wheel SHA256 is
`c625b6f4273241ee29bde7b4cdfbcebc9ddf4ab5b0e2caf1840727de4fb67c9b`.
`vendor/4ce491c/source-receipt.json`, `pyproject.toml` and `uv.lock` identify the bytes.

The upstream TODOs for native SELECT generation and complete explicit acquisition are
resolved: `salesforce.entities.flows.to_sqlglot(record, simplify=True)` returns a native
SELECT, graph lineage, source node sequence, logical role inputs, output definitions when
available, and assignment/determinism evidence. `field_definitions.api.download_api_export`
returns an exclusive complete selected capture and receipt; Ops delegates acquisition.
The single-column compiler accepts selected native fields/components directly. A generic
collection compiler is unnecessary for this consumer.

Ops must preserve the distinction between capture `source_sha256` and canonical
`metadata_sha256`. Simplification is upstream, before physical binding. Do not rewrite
native Flow branches in Ops. Unsupported effects/lookup-derived update targets fail
explicitly upstream. Lake history, relation naming, physical aliases and snapshots are
Ops responsibilities.

## Work sequence and resulting design

1. Pin the reviewed wheel and remove retired FlowRequest/flow_context/flow_assignments
   consumers. Inspect the actual logical-role contract before implementing physical binding.
2. Create `io.py` for explicit DDL read/discovery/export and input loading. Native field
   captures and lake DDL are independent evidence. Preserve decimal precision/scale,
   component parent identities, pointers and content hashes. Replace generated APMP
   schema JSON with separately parsed DDL and a visible input manifest.
3. Consolidate domain operations in `account_to_survey_results/queries.py`. Bind Account
   BEFORE, execution Contact/Survey/lookups, and Account AFTER independently. Keep filters
   inside source subqueries. Preserve all occurrence multiplicity, old unchanged intervals,
   missing parents, assigned NULLs and retained values. Retain authored rollups and the
   narrow Ibis relational bridge; return final SQLGlot comparisons to runtime.
4. Consolidate registration, catalog/version checks, native execution, suite snapshots,
   partial-result retention and reporting in `runtime.py`. No domain imports. Scope-based
   physical-source validation and version binding must distinguish CTE names from tables.
   Preserve native results, no-result reporting, Data Docs/assets, typed Parquet and
   immutable manifest-last publication with joint failure diagnostics.
5. Move native suite builders to `suites.py`, consuming prepared columns and explicit
   provenance. Keep `workflow.py` a visible sequence of input verification, comparison
   construction, preflight, suite registration, execution and reporting. CLI and Glue
   bootstrap remain hosting modules. Imports perform no source metadata reads/compilation.
6. Enable an explicit authored SELECT path with version-1 YAML contract: definition and
   suite identity, Athena dialect, scalar type/nullability, relation bindings and one
   structured output lineage/role per alias. The caller supplies a native suite. Bind
   named placeholders using typed AST literals; reject ambiguity before registration.
7. Migrate callers, semantic tests, generated SQL/suites and graph diagrams; remove obsolete
   modules, APIs and API-only tests. Run required checks, then the four real DVC producers
   and installed smoke. Update `dvc.lock` only from actual outputs before committing.
8. Perform a separate post-implementation review as an Ops consumer, fix findings and
   rerun affected gates. Open a new PR against the plan-bearing handoff branch so its
   review diff contains this implementation rather than the earlier unmerged refactor.

## Concrete implementation choices

- Five application modules plus `cli.py`, `glue.py` and package initializers. Removed
  `core`, `sources`, the runtime package, `gx_queries`, `views`, and separate domain
  metadata/schema/lineage modules. Existing report and failure behavior is folded, not
  replaced with a framework. No new runtime package is introduced. DuckDB is constrained to 1.5.6 after the Linux x86_64 2.0.0 wheel raised an illegal-instruction error on the measured producer.
- Native Flow event identity is preserved. Comparison context is carried alongside the
  existing event identity projections, avoiding a second join on duplicate event IDs.
  The upstream graph and node order remain attached independently of the simplified CTEs.
- Eligibility is required explicitly (true/false/unknown). It denotes independently verified
  start transition, exemptions and settled asynchronous execution. Completion status alone
  is insufficient. Org-local date is separate from physical snapshot and UTC parameters.
- Lake DDL, aliases, `_history` default/explicit overrides, relation kind, partitions and
  history boundaries come from selected inputs. Live execution rejects provisional profiles,
  missing native definitions and unreviewed/lossy type mappings before client creation.
- Existing saved catalog evidence is insufficient to reconstruct a native field capture.
  Bundled DDL is explicitly provisional offline evidence; no native metadata is fabricated.
  Real field captures and reviewed lake DDL remain deployment prerequisites.
- SQL rendering suppresses verbose comments for Athena size, while `.lineage.json` and native
  AST metadata retain source graph, output lineage and capture/type evidence. Generated SQL
  is not implicitly executable. Authored file execution is an explicit workflow call.
- Required/must-be-null presence rules remain explicit prepared-column suite policies;
  generic comparisons retain independently supplied Boolean presence columns. They are
  not inferred from Salesforce requiredness or from observed values.
- Rollup observations use a full join, preserving observed-only rows as invalid-key findings.
  Duplicate source parents are checked before aggregation. Zero-child and revocation
  semantics remain explicit authored rules.

## Acceptance matrix

| Concern | Required verification |
| --- | --- |
| Temporal roles | Half-open intervals; old unchanged BEFORE; independent observed AFTER; comparable instants; explicit org date/eligibility |
| Multiplicity | Duplicate triggers, BEFORE parents, Contacts and AFTER rows retain exact occurrence count; missing relationships survive; no context-rejoin fanout |
| Source semantics | All original simple update/primary/EHR/assent/physical-measurement/default branch cases; metadata mutation changes output; NULL/unknown versus unassigned |
| Simplification | Faithful and simplified result multisets equal, including duplicates; original graph/node order and output identities retained |
| Definitions | Native precision/scale zero; component identity; incomplete captures; missing/lossy evidence rejected; DDL read/export never executes |
| Runtime | SELECT-first and explicit outputs; CTE/table name collision; conflicting/unread snapshots; exact suite snapshots; parameter isolation; failure/partial reports |
| Authored SELECT | Native suite pairing; named scalar AST binding; quoted values; decimal/timezone/null policy; undeclared reads/parameters/aliases and unsupported contracts rejected |
| Independence | Runtime import loads no domain; query/suite builders require no source acquisition; installed wheel contains no retired modules |
| Release | Exact wheel SHA/source identity; real four-producer lock; fresh index-free installed smoke; unchanged Poe operational ownership |

## Post-implementation review record

This is a separate review pass by the implementing agent, not a claim of an independent
reviewer. The review focuses on how an Ops developer supplies inputs, diagnoses incomplete
findings, preserves provenance and reproduces the installed release.

| Finding | Resolution |
| --- | --- |
| Joining Flow outputs back to context on native Id would multiply duplicates | Carry context through event-identity projections; four duplicate-role cases assert exact counts |
| Splitting native field names on `__` truncated `__c`/`__pc` and dropped suite lineage | Strip only assignment/determinism suffixes; regression checks native target field in the registered suite |
| A matching lake type could be mistaken for native evidence | Separate captures/DDL; live gate requires selected native definitions and lossless compatibility |
| CTE references could receive physical version clauses | Resolve scopes, bind physical occurrences only, reject conflicts and unused bindings |
| Left-only rollup comparison discarded observed-only rows | Full observation join preserves them with invalid keys |
| SQL serialization would lose graph and output provenance | Write explicit lineage sidecar and verify native dump/load metadata round trip |
| Shared runtime imported the Account adapter after consolidation | Remove domain imports; runtime takes final SELECTs and explicit schemas/locations |
| Full GX metric SQL can exceed the base QueryAsset size | Measure every SQLAlchemy statement immediately before submission; reject over-limit UTF-8 statements and record sizes in run evidence |
| Earlier fixture/API assertions no longer exercised the real integration | Port independent branch/value tests; add native SQL, authored contract, definition and duplicate/missing-role tests; retain report/release tests |
| Native lookup diagnostics disappeared from the comparison projection | Preserve native lookup IDs, counts, knownness and values for consumer diagnosis |
| Two compound fields could share the same component name | Preserve native parent identity in `Object.Parent.Component`; test distinct address parents |
| Python's default decimal context could round a valid 38-digit literal | Validate magnitude exactly and quantize in an explicit 38-digit context; test the maximum 38-digit value |
| ISO timestamp text was not the canonical Athena cast form | Normalize aware inputs to explicit UTC timestamp text and test the rendered literal |

## Verification

Final gate results and release artifact identities are recorded in
[the implementation evidence](../evidence/native-flow-sql-ops.md). Synthetic/offline checks
and installed release verification establish no live Salesforce/Athena/Glue acceptance.
No live configuration, record-level data or report rows belong in Git.
