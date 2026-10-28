# Minimal implementation plan

Status: proposed for review; implementation has not started.
Prepared: October 28, 2026.

## Basis and authority

Implement [the minimal implementation brief](../minimal-implementation-brief.md), added in Ops commit [`c965adb70ea8b6a2734fa0c55fea6b7345446f93`](https://github.com/mbkranz/ppsc-ops-data-quality/commit/c965adb70ea8b6a2734fa0c55fea6b7345446f93) on `codex/refactor-handoff`. This plan was checked against that commit, including its actual callers and tests. Recheck the branch and reconcile subsequent user edits before implementation; do not reset intervening work.

The brief governs conflicts with `AGENTS.md`, the installed Python design skill and [the previous refactor plan](../refactor-plan.md). Keep their correctness, explicit dependency and failure guidance. Replace incompatible requirements to retain `core`, Ibis-only interfaces, old public APIs or models for every intermediate operation. Earlier progress reports remain historical evidence, not acceptance of this implementation.

The requested Salesforce baseline is `mbkranz/ppsc-salesforce`, branch **`native-athena-products`**, reviewed commit **`d024c15c95e581fbc10eaaf9b62e7b50630edda9`**. The branch was verified at that commit for this plan. It is different from `codex/native-athena-products`. Ops currently pins the older `vendor/a534c633/ppsc_salesforce-0.1.1-py3-none-any.whl`; the selected Salesforce source still reports version `0.1.1`, so version alone is insufficient identity.

This change is a replacement, with direct caller/configuration migration. Delete obsolete APIs, aliases, fixtures, modules and configuration paths. Do not build compatibility shims, a registry, providers, a query DSL, a new compiler layer or a replacement validation framework. Do not add dbt.

## Resulting application

```text
src/ppsc_ops_data_quality/
    io.py
    runtime.py
    account_to_survey_results/
        queries.py
        suites.py
        workflow.py
```

Initializers, the CLI, hosting entry points and saved inputs may remain. Release/deployment tools keep their existing operational ownership. Five application modules are the target; this is not a requirement to hide unrelated deployment tools in them.

| Module | Responsibilities and native interfaces |
| --- | --- |
| `io.py` | Discover/read selected lake DDL through explicit clients/locations or saved files; parse native SQLGlot definitions; export definitions and receipts with paths, source identities and content hashes. Export never executes DDL or deploys tables. Delegate Salesforce acquisition to its public package functions. |
| `runtime.py` | Register final comparison SELECT ASTs with native GX, run native suites/ValidationDefinitions, perform catalog/version compatibility checks and preserve execution/report evidence. Accept explicit context/source/client/path dependencies. No domain query construction or Salesforce semantics. |
| Domain `queries.py` | Build Account/Survey event selection, temporal states, relationships, expected/observed comparisons and authored domain rules. Adapt native definitions/projections to physical lake names/types/aliases and role-specific predicates. Keep the narrow Ibis-to-SQLGlot bridge here while required. No GX imports. |
| Domain `suites.py` | Authoritative ordinary functions returning native `gx.ExpectationSuite` objects, using prepared column names and explicitly supplied provenance. Retain built-in GX expectations and the existing comparison policies. No metadata acquisition or hidden compilation. |
| Domain `workflow.py` | Load/verify selected inputs explicitly; compose source analysis, projections, lake binding, comparisons, suites and runtime execution with named intermediate values. Own event/rollup configuration and pass domain lineage explicitly. |

Keep useful configuration validation beside the consumer, with models only where it adds validation. Use ordinary functions and native ASTs, expressions, suites and validation results elsewhere. Do not introduce a shared `projections.py`; a second concrete domain would have to demonstrate a later extraction need.

## Verified Salesforce capabilities and gaps

The distribution imports as `salesforce`. Use verified public submodules, not hypothetical root-level methods. These are source-inspected facts at the selected commit, not an installed-wheel acceptance result:

| Capability | Current public surface and implementation consequence |
| --- | --- |
| Native field columns | `salesforce.entities.field_definitions.schemas.to_sqlglot(field, *, source=None)` returns one annotated SQLGlot `ColumnDef`. Preserve object/field identities, native type evidence, precision/scale (including scale zero) and actual scalar component definitions. Unsupported/ambiguous native types fail explicitly. |
| Field acquisition | `salesforce.entities.field_definitions.api.field_definition(client, object_qualified_api_names, output_path)` already requests native `DataType`, `Length`, `Precision`, `Scale` and identity evidence. Validate the selected captured payloads and acquire component evidence where necessary; do not assert that every acquisition lacks precision/scale. |
| Flow analysis and selection | `salesforce.entities.flows.analysis.analyze_flow` followed by `salesforce.entities.flows.plans.select_projection` yields a selected slice with logical `before`/`lookup` inputs and detached `field_evidence`. Analyze once and select the necessary closure. |
| Executable projection | `salesforce.entities.flows.queries.project_flow(event_relation, sources, slice_, *, flow_run_date, eligibility)` returns a `FlowProjection` mapping to native Ibis tables. Existing assignment APIs retain assigned/deterministic evidence. Individual expression AST functions do not establish a complete logical SELECT AST API. |
| Provenance | Structured `expression.meta['ppsc']` and detached field evidence carry source fragments/paths and identities. SQL text/comments alone do not preserve that structure through rendering and reparsing. |

Record and resolve these gaps before treating the source contract as complete:

- **[TODO in ppsc-salesforce]** Expose resolved Flow output definitions, expressions and complete logical projection SELECT ASTs through a small public API that reuses existing analysis/projection semantics. Include logical input roles, assignment/determinism evidence and provenance. Ops must not implement another Flow interpreter.
- **[TODO in ppsc-salesforce]** Add a direct selected FieldDefinition/component-collection-to-column-definitions entry point if current public calls otherwise force Ops to duplicate native normalization. Validate the selected evidence; never infer missing native precision, scale or component identity from lake DDL.
- **[TODO in ppsc-salesforce]** If acquisition is used, make incomplete/query failures explicit and fix the current `Path(output_path)` behavior for the default `None`. The inspected function can print failures and return incomplete responses. A verified complete offline capture can avoid this acquisition blocker; a partial capture cannot count as success.

The permitted interim route is explicit: call the existing native projector, compile its Ibis table through the domain bridge, parse to SQLGlot and carry detached source/output evidence alongside the AST. Check output identities/types and assignment/determinism evidence before binding. Report this as a bridge, not a completed metadata-only AST API. Mark any further missing source-semantic capability with the exact `[TODO in ppsc-salesforce]` tag. History naming, physical overrides and snapshot binding belong to Ops.

## Concrete migration map

| Existing implementation | Planned disposition |
| --- | --- |
| `gx_queries.py`, `runtime/athena.py`, `runtime/runner.py` | Fold query registration, exact SQL capture and native sequential execution into `runtime.py`. Move Ibis compilation into domain `queries.py`. |
| `runtime/preflight.py`, `runtime/configuration.py` | Keep useful shared catalog/version checks and Athena/report settings in `runtime.py`, accepting explicit definitions/locations instead of APMP/global domain inputs. Domain settings remain in `workflow.py`. |
| `runtime/artifacts.py`, `reports.py`, `report_schemas.py` | Consolidate real report behavior in `runtime.py`: suite snapshots, native gzip JSON, exact queries, HTML plus assets, typed Parquet discovery rows, manifests and S3 publication. Preserve diagnostics instead of deleting them as infrastructure. |
| `runtime/duckdb.py` | Move development-only evaluation beside its concrete consumer in `scripts/check_validation.py`; use native GX directly. Retain a small shared runtime function only if a real execution need remains. No backend registry. |
| `runtime/glue.py`, `resources.py` | Move necessary bootstrap/config-hash/release-provenance handling to an allowed hosting entry point and update `glue/scripts/validate_history.py`. Keep engine cleanup and host status behavior. |
| `runtime/data_access.py`, `sources/apmp.py` | Replace generated JSON schema authority with native definitions plus parsed lake DDL. Put DDL I/O in `io.py`, and physical mapping/history/type adaptation in domain `queries.py`. Keep meaningful collision/type diagnostics. |
| `core/queries/*`, `core/comparison.py`, `sources/salesforce.py` | Retain only actually consumed history, comparison, bridge and native-source calls in domain `queries.py`. Consolidate competing comparison paths; remove the generic adapter packages. |
| `core/comparison_gx.py`, domain `gx.py` | Consolidate into domain `suites.py`, consuming explicit provenance. |
| Domain `schemas.py`, `core/schemas/*` | Replace generated/convenience schema constants and loaders; retain pure domain adaptation in `queries.py`. Remove `core`. |
| Domain `metadata.py`, `lineage.py` | Make saved-input loading/verification explicit in `workflow.py`; place retained pure query/provenance helpers with their consumers. Remove import-time I/O/compilation and global `PROJECTION_LINEAGE`. Saved native inputs may remain. |
| `core/configuration.py` | Retain duplicate-key YAML rejection beside its actual consumers. Update `scripts/render_report_catalog.py` too; do not create a generic configuration package to retain the old path. |
| `views.py` | Remove the unused legacy publishing API after checking callers. Any concrete operational publishing need belongs with deployment scripts. DDL export remains separate from execution. |

Delete obsolete `core/`, `sources/`, `runtime/` and root modules once callers migrate. Replace the old `runtime/` package with `runtime.py` atomically; leaving both is not an acceptable transition endpoint.

## Implementation sequence and review gates

### 1. Freeze the baseline and establish the source contract

1. Record actual Ops/Salesforce revisions, working changes, installed dependency identity and baseline checks. Preserve current synthetic inputs and semantic results for comparison. Historical counts/timings are not fresh acceptance evidence.
2. Select or acquire complete native FieldDefinition/component captures and the intended lake DDL before exercising the source contract. The checked-in `metadata/source_catalog.json` contains relationship/identity evidence but lacks native `DataType`/`Precision`/`Scale`; generated `tables.json` lake types cannot fill that gap. Record selected object/field/component identities, capture hashes and source org/version. Obtain missing inputs through Salesforce acquisition or explicitly supplied verified captures; report unavailable evidence as a blocker rather than fabricate it.
3. Exercise the selected public Salesforce APIs against those captures and the actual saved Flow. Inventory missing native/component evidence and unsupported semantics. Either use the explicit supported bridge or resolve the upstream gaps and review a new exact source commit; never silently substitute another branch or an empty successful projection.
4. Build the wheel from the selected exact reviewed commit. Record repository, commit, filename/version and SHA256; update the vendored artifact, `vendor/README.md`, `pyproject.toml` and `uv.lock` together. Remove the superseded wheel. No editable sibling installation or mutable branch dependency in the release.
5. Verify an isolated installed consumer: imports resolve to site-packages, installed package files match the wheel, actual submodule functions work, and source identity/hash match the selected commit. Source-tree inspection alone does not satisfy this gate.

Exit: a verified immutable dependency and an explicit supported projection route, with remaining upstream work named and incomplete paths failing visibly.

### 2. Establish DDL inputs and domain projection/binding

1. Add narrow DDL read/discover/export functions in `io.py`. Require explicit selected relations, clients/paths, and overwrite behavior. Parse/copy native ASTs; return useful receipts without executing DDL. Exercise saved-file and mocked-client paths with synthetic definitions.
2. In `queries.py`, bind native output/column identities to explicit physical catalog/database/relation/column names. Apply `_history` only as the documented default; explicit overrides win. Keep native definitions and lake DDL as separate evidence for compatibility, not competing source-semantic authorities.
3. Replace the old generated APMP `tables.json`/`source_catalog.json` schema authority. Inventory and remove obsolete input/config/fixture paths after migrating useful identity/provenance evidence. Do not retain a second loader as a fallback.
4. Construct source role subqueries before joins. Bind Account BEFORE, execution-time Contact/Survey/lookups and Account AFTER independently; retain necessary prior field/history evidence. Apply role-specific effective intervals and physical version bindings to every relevant source occurrence. Resolve SQL scopes so CTE aliases are never mistaken for physical sources; require all physical reads to match the selected catalog/database/relation allowlist, and reject undeclared reads or conflicting versions.
5. Adapt upstream projections through AST operations or the explicit domain bridge. Preserve detached lineage, logical roles, output identity, type/precision/scale and assignment/determinism evidence through aliases and lake-specific casts. Verify unsupported/lossy adaptations fail.

Exit: final comparison SELECT ASTs and explicit provenance, independent of GX, with synthetic semantic parity and no source interpreter in Ops.

### 3. Consolidate native validation and reports

1. Create `runtime.py` from the existing useful registration/execution/report implementations. Accept final queries and native suites/definitions with explicit dependencies; a direct Python query/suite builder must work without Salesforce inputs. Retain GX's SELECT-first query normalization for CTE inputs with explicit output columns, without string rewriting or expanding shared CTEs indiscriminately. Preserve scope-safe CTE/physical-name collision handling and reject unsupported recursive CTEs.
2. Keep preflight before validation: selected column types, decimal precision/scale, duplicate/case collisions, relation/partition/view identity, selected physical versions and declared repeatability. Record extra unrelated columns rather than silently changing selected types. Version probes must correspond to actual query reads.
3. Preserve runner semantics: reject duplicate definition names and unknown per-definition parameter targets before running anything; serialize the actual registered `definition.suite` exclusively immediately before each validation; archive each returned native result immediately. Failed expectations allow subsequent definitions; execution errors propagate while prior results survive. Do not fabricate a GX result for an exception.
4. Preserve reports and publication: fresh run directories, exact query/source metadata, native results, suites, Data Docs assets, typed validation/expectation Parquet and `no_result` rows where execution did not finish. Keep manifest-last immutable publication and jointly visible execution/publication errors. Do not imply transactional writes.
5. Measure compact base SQL and complete GX-submitted statements for realistic configured names, predicates and versions. The previous plan records very little Flow query headroom; do not reuse those measurements as current proof. Retain size rejection and diagnostics. If full statements exceed the backend limit, resolve the actual query expansion before acceptance; do not assume CTEs, views or Query Assets execute once or add materialization by default.

Exit: one native runtime, with no domain imports or Salesforce input requirement for direct builders; preserved report/partial-failure behavior and measured executable SQL.

### 4. Make composition explicit and migrate callers

1. Move authoritative builders to `suites.py`, passing prepared columns and provenance explicitly. Generate serialized examples from these same functions.
2. Rewrite `workflow.py` as visible input verification → source analysis/selection → lake role binding → projection/comparison → suite construction → runtime calls. Keep event/rollup settings here. Remove import-time metadata work and retired `schema_overrides`/`databases` compatibility logic.
3. Update `cli.py`, `examples/validate_athena.py`, Glue bootstrap, `scripts/check_validation.py`, diagram generation and report-catalog generation directly. Preserve configuration-before-client validation, explicit client creation, configuration hash/release evidence, engine cleanup and host exit meaning (pass, failed expectations, execution/configuration error).
4. Replace `params.example.yaml` and relevant deployment fixtures with the new explicit DDL/native-input/location/version shape. Keep YAML duplicate-key rejection and rejection of example placeholders. Validate all referenced files, roles and outputs before online work.
5. Delete obsolete modules and tests that only assert retired APIs. Port meaningful comparison, identity, metadata, report, CLI/Glue and release tests to the new interfaces. Check imports and installed-package contents for retired paths.

Exit: the five-module application is the only implementation, all concrete callers use it, and direct imports perform no metadata acquisition or projection compilation.

### 5. Enable intentional authored SELECTs under a reviewed contract

Proposed contract for review: an explicit workflow argument selects a `.sql` source file plus a small YAML sidecar with `schema_version: 1`, a definition ID, `suite_name`, dialect, typed parameter declarations, physical relation bindings and structured output/source lineage. The workflow passes the native Python-built suite directly; `suite_name` must equal that supplied suite's name. The sidecar neither serializes a GX object nor dynamically imports a builder. Python builders remain ordinary calls, with no discovery or registry. Use Athena dialect initially; reject unsupported sidecar versions/dialects and unknown keys.

- Accept exactly one comparison SELECT, optionally with nonrecursive CTEs and one terminal semicolon. Require explicit output columns, stable names for direct columns and explicit aliases for expressions; reject `SELECT *`, duplicate/case-colliding output names, DDL/DML and multiple statements. Require one lineage entry and a key/expected/observed/evidence role per projected output, permitting an explicit domain-authored rule identity/description for columns without Salesforce metadata. Reject missing/extra/contradictory alias mappings using parsed identifier identities.
- Proposed initial value types are string, Boolean, integer, exact decimal (declared precision/scale), date and timestamp, each with explicit nullability. Propose UTC-normalized timestamps and rejection of ambiguous naive input; do not alter the separate org-local `flow_run_date` semantics. Reject undeclared/unknown/unbound or unused parameter declarations, invalid values and unsupported collection/arbitrary-expression inputs before execution. Keep runtime values separate from the declarations; record effective typed bindings in run evidence, outside version control.
- Use named scalar placeholders such as `:as_of`, parsed as native placeholder nodes and replaced with validated typed literal/CAST ASTs before GX registration. Bind relations separately as identifier/table nodes against the selected physical-source allowlist. Apply the same scope-safe physical version binding and SELECT-first GX normalization to authored and Python-built queries. Never interpolate SQL strings or infer source execution from a filename, string content or generated audit directory.
- Hash and retain the original SQL/sidecar, the bound executable SQL, declared dialect, typed parameters, suite snapshot and code/source/version identities. Validate alias-to-lineage correspondence after binding and preserve detached metadata through export/read-back.
- Keep parsing/loading with the explicit workflow path and pure AST binding in domain `queries.py`; use existing `io.py`/`runtime.py` functions for effects/execution. Do not create `runtime/sql_files.py` or another compiler package.
- Before enabling execution, confirm the proposed contract resolves its behavioral choices, especially alias/lineage correspondence and parameter types. If review leaves any choice unresolved, request that specific user decision; the file path must remain visibly unavailable until resolved. This gate does not block direct Python builders or justify permanently deferring the SQL path.

Exit: the agreed minimal contract is documented and tested for successful execution, round-trip provenance and explicit rejection paths.

### 6. Refresh documentation, generated artifacts and release evidence

1. Update README, query/runtime/reusable-comparison documentation, examples and suite/diagram generation. Move useful `runtime/README.md` and `runtime/TODO.md` content into surviving docs. Mark conflicting older plan directions superseded without rewriting their historical measurements.
2. Regenerate illustrative SQL, `suites/*.json` and applicable diagrams through the migrated authoritative builders. Compare complete suite metadata/conditions and findings; expectation counts alone do not establish equivalence.
3. Run the required gates below; explain actual failures and baseline blockers. Review complexity: production module/line changes, dependencies, indirection, deleted duplicate paths and the simplest viable alternative. Five files must not conceal a new framework.
4. For changed source/wheel release inputs, update relevant DVC dependencies, prepare locked release tooling once, and run the four real root producers (`requirements`, `dependencies`, `wheel`, `bundle`) through existing Poe tooling. Finalize `dvc.lock` only from real outputs; verify freshness and isolated installed-release smoke, including the new hosting imports and Salesforce source identity.
5. Keep publication, deployment, run submission and live validation uncached. Exclude credentials, live configuration, bound run parameters and record-level outputs from version control; preserving report evidence does not authorize committing it. This implementation does not itself establish live Athena/Glue acceptance. Record any separately executed live checks by exact release/input identity; do not imply synthetic checks prove them.

Exit: coherent source, callers, docs and reproducible release evidence, with remaining limitations stated accurately.

## Semantic acceptance matrix

Use independently authored synthetic fixtures, retaining baseline assertions rather than only rewriting expected outputs around the new code. Compare multisets, values, evidence flags and findings; do not key results until uniqueness has independently been checked.

| Risk | Required evidence |
| --- | --- |
| Temporal role confusion | BEFORE < execution < settled AFTER; half-open effective intervals; old unchanged versions; independent roles; timestamp/timezone resolution; snapshot filters inside source subqueries before outer joins. A physical snapshot ID is not business-effective time or cross-table atomicity. |
| Fanout or lost records | Duplicate/missing parents, overlapping histories, duplicate lookups, unmatched observations and invalid identities survive into findings. Survey event uniqueness is independent of Account/event composite uniqueness. No deduplication to make checks pass. |
| Assignment/NULL confusion | Assigned NULL differs from no assignment; assigned False retains BEFORE and remains comparable; unknown assignment/routing/determinism yields incomplete evidence. Both-null pairs retain existing accepted/excluded-denominator policy; one-sided NULL fails. |
| Lookup and rollup drift | Ambiguous permission lookups remain visible; Contact/person-contact presence remains checked. Detect parent duplicates before aggregation; preserve zero-child, deletion/revocation and explicit empty-cohort count policy. Keep the independent observation cohort aligned with the same event/snapshot. |
| Provenance/type loss | Source commit/capture/hash, native field/Flow identities, logical roles, definitions/expressions and detached evidence survive lake aliases/casts and SQL serialization. Decimal scale zero, compound components, missing evidence and lossy coercions have focused cases. |
| Hidden coupling | Import without I/O; native Python query/suite builders work without Salesforce selection; shared runtime has no Account imports; removed modules and old config/API paths are absent. |
| SQL scope/version mistakes | GX accepts normalized SELECT-first queries with explicit projections; CTEs and physical tables with the same spelling resolve independently. Reject undeclared physical reads, conflicting versions and recursive CTEs; bind selected versions to every physical occurrence without binding CTE references as tables. |
| Execution/report regression | Exact registered suite snapshot, per-definition parameters, unsuccessful expectations versus execution errors, surviving partial results, no-result report rows, manifest-last publication and simultaneous failure diagnostics. |
| Authored SQL ambiguity | Explicit source selection, one SELECT/CTE parsing, typed values versus identifiers, quoted aliases, missing/duplicate lineage, round-trip evidence and rejection before execution. Generated SQL is never auto-executed. |
| Release ambiguity | Exact immutable wheel SHA256/source identity, updated locks from actual outputs, isolated installation, correct CLI/Glue imports and unchanged Poe/four-producer ownership. |

Primary existing test families to migrate are `test_flow_derivations`, `test_snapshot`, `test_expected_evidence`, `test_reusable_comparison`, `test_account_to_survey_results_expectations`, `test_gx_queries`, `test_runtime`, `test_reports`, `test_apmp`, metadata/integrity/foreign-key tests and CLI/deployment/release/diagram tests. Rename obsolete families when their subject changes; retain semantic coverage. Add focused DDL/export, native-bridge and SQL-contract cases where behavior is new.

## Verification and review record

Required implementation gates are `uv run poe check`, `uv run poe check-queries` and `uv run poe check-synthetic`. Artifact generation uses `uv run poe render-queries` and `uv run poe suite-diagrams`. Changed release inputs additionally require the prepared Linux producer's `uv run poe build-release --backend local`, installed smoke and `dvc status dvc.yaml --quiet`.

This plan-only change modifies no release input and does not require regenerating release locks. Source/API and caller inspection was performed at the exact revisions above. No implementation, upstream API addition, wheel replacement, release build or live acceptance is claimed by this plan.

### Observed baseline checks for this plan

Checks ran in an isolated macOS checkout at `c965adb`, using its existing vendored dependency. The default `uv run poe check` could not start because pinned Python `3.11.17` is unavailable here. The subsequent commands used `uv run --python 3.11.11 --locked poe …`; these results do not establish the pinned Linux release environment or the proposed new Salesforce wheel.

| Check | Observed result |
| --- | --- |
| `poe check` with Python override | Ruff lint passed. Formatting stopped on pre-existing Python snippets in `.agents/skills/design-python-contracts/references/ppsc-design-examples.md`; the combined task therefore did not reach pytest. No unrelated formatting change was made. |
| Separate `poe test` | **226 passed, 3 failed**. Both real-DVC handoff cases failed at `python -m dvc init`; this checkout has neither DVC in its development environment nor a prepared `.venv-release`. The release integration case selected the remote build route on macOS and stopped for absent GitHub CLI authentication. These release-environment blockers remain open; the suite is not fully green. |
| `poe check-queries` | Passed; offline comparison queries and native suites compiled. |
| `poe check-synthetic` | Passed; **56/56 expectations** succeeded (30 Flow, 26 rollup). No live queries. |
| Document checks | Relative links resolve; code fences balance; no trailing whitespace. Only this plan is included in the documentation commit. |

Implementation must rerun the required gates and release acceptance in the appropriate environment, reporting actual results rather than inheriting this baseline's passes or treating its blockers as waived.

### Independent review after initial generation

A separate reviewer compared the initial draft with the brief, current consumers and source APIs. The following additions were incorporated; a second read found no remaining material issue in the plan. The SQL choices remain proposed review decisions until implementation enables that path.

| Review finding | Change incorporated |
| --- | --- |
| Existing saved catalog is not a complete native type capture | Phase 1 now requires complete FieldDefinition/component captures and separately selected lake DDL, with identities/hashes and explicit blockers. Generated lake types cannot replace missing native evidence. |
| SQL sidecar/suite/parameter behavior was underspecified | Phase 5 now specifies a version, supplied native suite/name match, dialect, output roles/lineage, scalar types/nullability, named placeholders, decimal/timezone policy and rejected ambiguous cases. |
| CTE execution/source/version behavior needed explicit preservation | Phases 2–3 and 5 plus the acceptance matrix now require SELECT-first GX normalization, scope-safe physical-source allowlisting and version binding, including CTE/physical-name collisions. |
| Retained report artifacts could blur the Git boundary | Phase 6 explicitly excludes credentials, live configuration, bound run parameters and record-level output from version control. |
