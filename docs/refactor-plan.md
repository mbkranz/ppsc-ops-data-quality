# Salesforce and Ops data quality refactoring plan

Status: Ready for Phase 1 implementation.
Prepared: October 27, 2026.
Canonical plan: `ppsc-ops-data-quality/docs/refactor-plan.md`.

## Goal

Simplify `ppsc-salesforce` and `ppsc-ops-data-quality` while preserving their behavior and making additional validation modules straightforward to author. Prefer fewer overlapping implementations, explicit functions and cohesive modules. Keep Ibis transformations authoritative and GX validation native.

This file is the self-contained implementation handoff. Read the applicable repository `AGENTS.md` first. External references provide background; implementation must not depend on access to the originating ChatGPT conversation or Page.

## Starting points and dependency identity

| Repository or dependency | Reviewed starting point |
| --- | --- |
| Ops integration | `mbkranz/ppsc-ops-data-quality`, branch `codex/apmp-athena-inputs`, PR #13, commit `39c513985c3b4665058f7bef5f8a960d8ee52af3` |
| Ops default branch | `main`, commit `63aa04a783152ddd9907b81852dd47f166f6137e`; does not contain the full reviewed integration |
| Salesforce integration | `mbkranz/ppsc-salesforce`, branch `codex/native-athena-products`, PR #7, commit `a534c63353680e41d12e3b55997a125ba703c675` |
| Salesforce default branch | `dev`, commit `2ac94684e3ff3be798ef73b2d45e250413f3d170` |
| Salesforce wheel actually consumed by Ops | `vendor/1d59b5b8/ppsc_salesforce-0.1.0-py3-none-any.whl`, built from Salesforce commit `1d59b5b87b69e2b7da52c3c0bdb008c2af37c200` |
| Pinned wheel SHA256 | `7d588d32c56c1890a5b2988b3d7b4981042aa6ee1de5b829d58e936c93b240ec` |

The documentation handoff branch starts from the Ops integration commit above. Establish actual checked-out revisions and baseline status before implementation. If revisions have advanced, inspect the relevant diff and reconcile this plan against current consumers. Do not reset or overwrite intervening work.

The latest Salesforce source and the implementation in the pinned Ops wheel are different baselines. Do not silently replace the wheel with the latest source or treat package version `0.1.0` as sufficient source identity.

## Binding refactoring constraints

1. Prefer deleting or consolidating code over adding abstractions. Check whether an existing function, direct call or local implementation meets the requirement first.
2. Do not introduce new packages, registries or framework layers without a demonstrated second use case. Planned future modules, hypothetical extensibility and additional tests of the same consumer do not qualify.
3. Keep SQL transformations separate from GX definitions. Transformation functions return native Ibis expressions or SQL ASTs; they must not import GX or construct expectations. GX builders consume prepared columns. Workflow functions compose the two.
4. Require evidence from actual consumer code before generalizing an interface. Identify the concrete call sites, their differing needs and the precise shared behavior. A second consumer is necessary evidence, not an automatic reason to add an abstraction.
5. Evaluate final complexity, including module count, lines added and deleted, new dependencies, indirection and whether a simpler alternative meets the same requirements.
6. Use Pydantic for meaningful authored/serialized public boundaries, ordinary functions with explicit dependencies, and native Ibis/GX/frame return values. Keep cohesive request models and workflow code together when small.
7. Keep existing operational entry points, native GX execution and reporting. No replacement runner, workflow DSL, plugin discovery, DI container, generic CRUD interface or second query-authoring language.
8. Preserve semantic correctness while reducing code. Do not optimize for line count by concealing behavior, deleting diagnostics or weakening checks.

For permanent guidance, add concise versions of constraints 1–5 to the existing applicable `AGENTS.md` during implementation, preserving its other instructions. Do not create another guidance package or document hierarchy.

## Ownership

| Concern | Owner |
| --- | --- |
| Native metadata retrieval, saved Flow/field definitions, source identities and graph | Salesforce |
| Supported native decisions, assignments, formulas, lookups and rollup interpretation | Salesforce |
| Composable expected-value expressions and logical projection/query templates | Salesforce |
| Consumption of generated lake schemas, physical column mappings and Athena locations | Ops source adapter |
| Event selection, BEFORE/execution/AFTER state, snapshot cohort and business policy | Individual Ops validation module |
| Source-independent reconciliation mechanisms | Small shared Ops helpers |
| GX suites and module-specific integrity/completeness rules | Individual Ops module |
| Backend setup, catalog preflight, native GX execution and reporting | Shared Ops runtime |

The latest Salesforce PR already removes the earlier `ppsc-metadata` distribution and associated framework layers. Do not reintroduce them.

Current Salesforce `entities/field_definitions/schemas.py` interprets native metadata as SQLGlot column definitions. It is not a physical lake-schema adapter; do not move it solely because of its filename.

Documentation is inconsistent about the location of producer-side APMP schema authoring. Verify current code and resolve the documentation before any producer relocation. Keep the existing Ops consumer adapter. ODCS is not a required mediation layer for this cleanup.

## Semantics that must survive every phase

- Assigned NULL, no assignment with retained BEFORE, and unknown assignment are distinct states.
- `assigned=False` does not skip comparison: the expected value retains BEFORE.
- Both-null expected/observed pairs are accepted by the current equality policy and excluded from its denominator; one-sided NULL fails.
- Unknown scope, unresolved routing and ambiguous lookups remain visible as incomplete evidence.
- Preserve duplicates, missing parents, unmatched observations and overlapping history versions. Do not deduplicate to make validation pass.
- Flow observations must correspond to the same event and Account, with independently selected settled AFTER values. Do not compare all historical events to one latest Account state.
- Survey event uniqueness is independent of composite event/Account uniqueness.
- Participant Contact and person-contact presence checks remain even when those fields are not reconciliation keys.
- Detect source parent duplicates before rollup aggregation; post-aggregation uniqueness cannot recover collapsed evidence.
- Full reconciliation uses a deliberately selected observation cohort; unrelated Accounts must not become spurious unexpected observations.
- Zero-child rollups, deletion/revocation policy and explicit empty-cohort count contracts remain intact.
- Preserve half-open history intervals and time-zone/time-resolution checks. A date-grain history cannot establish arbitrary intra-day BEFORE/execution/AFTER.
- Preserve rejection of unsupported native Flow semantics rather than inventing translations.
- Fixture execution and SQL compilation do not establish live Salesforce/Athena/Glue acceptance.

## Adopted dbt and SQLMesh concepts

Adopt the concepts within the existing Ibis/GX implementation. Installing dbt, SQLMesh or Dataform is outside this plan.

### Meaningful relation boundaries

Use these logical stages where useful: bound sources; selected temporal states; Flow context; expected values; comparison; validation. Existing functions already implement much of this structure.

A query stage, a Python module and a persisted database object are separate decisions. A named relation does not require a new file. Extract only substantial or actually reused behavior.

### Grain and relationships

Describe each relation's intended row grain, keys and nonunique relationships. Audit cardinality rather than forcing it with deduplication. Account ID is a relationship for an event-grain Flow comparison; it is not the event identity.

### Materialization is an execution choice

Cheap single-use transformations can remain inline. Complex stages should be independently inspectable/compilable. Benchmark persistence only when expensive computation is reused or query size demands a boundary.

CTEs and views do not prove that shared work executes once. A future run-scoped persisted comparison may let GX checks share one prepared dataset, but requires explicit source identity, failure behavior and cleanup. Do not implement materialization in Phase 1.

### Tests at meaningful stages

Use small independently authored fixtures to test lookup candidates, ambiguity, routing, assignment, rollup inputs and reconciliation separately. SQLMesh's intermediate-CTE testing is a useful model: testing a stage need not require promoting it into a separate module.

Keep transformation tests in CI separate from runtime data checks. SQL-shape snapshots alone do not establish behavior parity.

### Audit dependencies and result comparison

Express prerequisites explicitly in workflow code. Invalid schemas may prevent dependent execution; invalid identities or unknown computation must still produce useful findings. Preserve independent validation and diagnostic/report behavior.

During consolidation, compare old/new values, evidence flags, findings and row multiplicity on the same frozen inputs. Verify uniqueness separately before relying on a keyed result comparison.

## Reviewed findings to verify

1. `runtime/validation.py` imports the Account POC's queries, suites and lineage, builds fixed Flow/rollup queries and selects suites with an if/else. `runtime/configuration.py` requires POC-specific event, rollup and metadata settings.
2. `runtime/runner.py` is already a useful native GX executor. Keep it: duplicate-name/parameter prechecks, actual suite snapshots and partial-result preservation are real responsibilities.
3. `core/comparison.py`, `core/comparison_gx.py` and `sources/salesforce.py` overlap with the primary bespoke Account paths. They are migration candidates, not justification for another wrapper layer.
4. `core/schemas/inputs.py` reads `account_to_survey_results/metadata`. Legacy convenience schema modules expose POC-derived constants as shared core.
5. `account_to_survey_results/lineage.py` loads/verifies inputs and compiles lineage during import. Preparation should become explicit.
6. Checked-in suite JSON has 27 Flow and 24 rollup expectations; the reviewed Python builders produce 29 and 25. Missing checks include Flow scope/computation completeness and rollup source-parent validity. Confirm current output rather than hard-coding historical counts as the sole contract.
7. The reviewed illustrative GX SQL contains separate statements of approximately 260,829 bytes for Flow and 30,568 bytes for rollups. Athena's limit is 262,144 UTF-8 bytes per submitted query. These are historical artifact measurements, not current generated or final GX metric-query measurements.
8. Salesforce dictionary query generation repeats native evidence across value/assignment/determinism columns, root metadata and owner rows. Ops also repeats substantial lineage across suite metadata and expectations.
9. Salesforce `flows/queries.py` repeats selected-path analysis for context, assignments and lineage. Exact native field identity handling also repeats across adapters.
10. Workbook-authored rollups are still provisional. Do not assume verified native rollup metadata is already available.

## Phase 1 — Baseline, generated suites and workflow ownership

Implement only this phase for the first Codex Cloud task.

### Scope

- Work in Ops. Salesforce is read-only context; keep the pinned wheel and lockfile unchanged.
- Read `AGENTS.md`, `pyproject.toml`, `poe_tasks.yaml`, `vendor/README.md`, runtime configuration/validation, CLI/Glue entry points and their actual tests/callers.
- Record starting revision, dependency/wheel identity, baseline check results and production module count before changes.
- Establish current generated-suite drift. Use authoritative native Python builders to refresh the existing tracked suite examples. Reuse existing serialization/generation functions; do not create a parallel suite format.
- Use or minimally extend the existing development generation command if needed to keep those existing examples synchronized. Prefer assertions about required check identities/semantics and deterministic suite content over a count-only test.
- Move Account workflow orchestration and its domain request models into the existing `account_to_survey_results` package, initially in a cohesive `workflow.py`. Keep shared backend/report configuration reusable.
- Update actual CLI, Glue and other consumers directly. Preserve CLI options, YAML configuration shape, registered suite names and report behavior.
- Remove the superseded shared orchestration file if no consumer requires it. Retain a compatibility import only for a demonstrated consumer, with that evidence recorded.
- Keep the native shared executor and backend/report mechanisms.
- Measure regenerated base-query bytes. Inspect final GX SQL using existing offline rendering/capture hooks if practical; distinguish unmeasured final statements from measured base SQL. No AWS calls are required.
- Add concise permanent constraints to the existing Ops `AGENTS.md`.
- Record the outcome and actual complexity assessment in this plan or the task/PR summary, without creating a planning harness.

### Non-goals

No comparison algorithm migration, general module registry, schema-wrapper cleanup beyond imports needed for the move, compiler rewrite, wheel refresh, dependency upgrade, new package, new engine, materialization, deployment or live AWS validation. Do not start later phases automatically.

### Acceptance

- Shared runtime no longer imports Account-specific query/suite/lineage builders or owns its domain request models. Update all affected imports, not merely the primary entry point.
- SQL/query modules remain independent of GX definitions.
- Existing YAML and public CLI behavior remain compatible; report creation and partial-result behavior survive.
- Tracked suite examples match the authoritative current builders and retain the required integrity/completeness checks.
- Required checks below pass, or pre-existing/environment failures are documented with exact commands and errors. Do not report blocked checks as passing.
- The Salesforce wheel, dependency lock and source metadata are unchanged.
- Final diff contains only Phase 1 changes and necessary tests/docs/generated suite output.
- Complexity assessment explains any module or authored-line increase and its simplest alternative.

## Phase 2 — Remove domain coupling and hidden preparation

After Phase 1 is reviewed, move POC-derived schema conveniences into the module or existing fixtures and update consumers. Remove unused compatibility modules. Replace import-time lineage/input work with explicit workflow preparation, passing selected inputs onward.

Simplify repeated load/cache/serialization/rehashing while retaining source/request/compiler identity. Avoid introducing a new public input framework. Keep native metadata provenance and physical-schema validation.

## Phase 3 — Consolidate comparisons and GX construction

Migrate one current path at a time onto the existing shared comparison/suite helpers where behavior truly matches. Keep module-specific integrity additions and independently selected observation cohorts. Prove parity before deleting the old path.

Keep one native equality expectation per field and separate scope, key, source-parent and computation-completeness checks. Share repetitive construction, not business policy. Keep stable check IDs. No custom GX metric engine or authored JSON rule language.

## Phase 4 — Simplify source projection and SQL generation

Coordinate Salesforce changes separately:

- Reuse one private selected-flow analysis where context, assignments and lineage need it.
- Consolidate exact native field-identity handling.
- Reduce repeated provenance by retaining selected native evidence once and using compact source/hash/JSON-pointer/role references. Avoid a new provenance framework.
- Preserve the distinction between illustrative symbolic SQL and executable Ibis projections.

In Ops, factor repetitive rollup predicates into a readable Python mapping and shared aggregate construction when semantics match. Do not call a single-rollup builder repeatedly if that multiplies scans/joins.

Narrow required columns before joins/windows. Factor repeated routing/determinism expressions and inspect the emitted SQL to verify sharing. Keep necessary SELECT-first GX and Iceberg adaptations; treat purely cosmetic AST rewrites separately.

A coordinated compiler update requires building and verifying a new pinned wheel, recording its source revision/hash, updating the lock, regenerating affected outputs and running release/installed checks. Never substitute an editable latest checkout for the deployed pin as proof of consumer compatibility.

## Phase 5 — Execution optimization and a second real module

Only after measurement, evaluate one explicit persistence boundary for repeated GX computation or query-size constraints. Validate source pinning, failure cleanup, final SQL size and actual execution cost. A fixed business timestamp alone is not an immutable source snapshot.

Use a real second validation module to test the authoring pattern. It may use native GX without Salesforce reconciliation. Share demonstrated common behavior; avoid prematurely forcing every module through `ComparisonSpec` or a registry.

## Verification

For Ops implementation changes, the current `AGENTS.md` requires:

```bash
uv run poe check
uv run poe check-queries
uv run poe check-synthetic
git diff --check
```

Use the repository's locked dependency setup. `poe check` includes lint, format and tests. The compilation and synthetic commands create fresh run directories; do not fabricate their outputs or repeatedly rerun completed checks without a new concern.

Additional existing commands are `uv run poe render-queries` and `uv run poe suite-diagrams`. Run them only when the corresponding output changes are in scope. SQL example rendering does not currently refresh tracked suite JSON by itself; inspect existing generation/serialization paths.

Phase 1 should preserve relevant CLI, configuration, runtime, reporting and deployment tests and add only meaningful coverage for changed boundaries. Later comparison phases must exercise:

- One event associated with multiple Accounts.
- Missing participant/person-contact identity.
- Duplicate source parents before aggregation.
- Missing/unexpected observations within the chosen cohort.
- Lookup ties and unknown routing.
- Assigned NULL, unassigned retained BEFORE and unknown assignment.
- Zero-child rollups and empty cohorts with/without explicit count contracts.
- Interval boundaries, overlapping versions and time-zone/time-resolution errors.

Live AWS/Salesforce access, deployment, DVC publication and Glue runs are not authorized by this plan. Offline work should proceed without them. Explain exactly what remains unverified rather than expanding the task to obtain credentials.

Keep `dvc.lock` grounded in real producer outputs under the repository's instructions. Do not hand-edit hashes or run live operations to manufacture freshness.

## Required final review

Provide per-repository before/after evidence where code changed:

| Measure | Required evidence |
| --- | --- |
| Production modules | Count recursive `.py` files under production `src`, including `__init__.py`, with the same convention before/after; list additions/deletions/consolidations |
| Changed lines | Added/deleted/net lines, separating authored production code, tests, docs and generated output; distinguish renames from substantive churn |
| Structure | Packages, registries, generalized interfaces and framework layers added or removed; actual consumers supporting anything new |
| Dependencies | New/removed runtime dependencies and justification |
| Duplication | Implementations and repeated authored representations removed or intentionally retained |
| SQL | Base/final submitted SQL bytes where measured, execution implications and any unmeasured portions |
| Behavior | Checks run and observed results; invariants preserved; known baseline/environment failures |
| Simpler alternative | The smallest viable alternative considered and why the final design needs any additional complexity |

Counts supplement readability and correctness; they do not justify removing required behavior. Explain increases with concrete consumer needs. Estimates belong to planning; final claims must come from the actual diff. State explicitly if the phase could have met the same requirements with less code or fewer modules.

## References

- [Ops PR #13](https://github.com/mbkranz/ppsc-ops-data-quality/pull/13)
- [Salesforce PR #7](https://github.com/mbkranz/ppsc-salesforce/pull/7)
- [Pinned compiler documentation](https://github.com/mbkranz/ppsc-ops-data-quality/blob/39c513985c3b4665058f7bef5f8a960d8ee52af3/vendor/README.md)
- [Clean architecture reference at the reviewed commit](https://github.com/MKToronto/python-clean-architecture-codex/blob/768bf3ec1e5a900a9a5802544d5323bfba11c537/.agents/skills/clean-architecture/SKILL.md): adopt cohesion, explicit dependencies and simplicity; not the FastAPI/CRUD scaffold.
- [dbt staging](https://docs.getdbt.com/best-practices/how-we-structure/2-staging)
- [dbt intermediate transformations](https://docs.getdbt.com/best-practices/how-we-structure/3-intermediate)
- [dbt materializations](https://docs.getdbt.com/docs/build/materializations)
- [SQLMesh grain and model metadata](https://sqlmesh.readthedocs.io/en/latest/concepts/models/overview/)
- [SQLMesh intermediate and final tests](https://sqlmesh.readthedocs.io/en/latest/concepts/tests/)
- [SQLMesh audits](https://sqlmesh.readthedocs.io/en/latest/concepts/audits/)
- [Dataform assertion dependencies](https://docs.cloud.google.com/dataform/docs/dependencies)
- [SQLGlot lineage](https://sqlglot.com/sqlglot/lineage.html)
- [Athena query limits](https://docs.aws.amazon.com/athena/latest/ug/service-limits.html)

## Progress

- Planning: complete.
- Phase 1 implementation: not started.
- Phase 2–5 implementation: not started.
- Repository tests/live validation for this planning-only commit: not run.
