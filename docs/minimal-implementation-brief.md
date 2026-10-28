# Minimal implementation brief

## Authority and starting point

This brief records the user's explicit direction for this refactor. Where
`AGENTS.md`, the Python design skill, or earlier plans conflict with this brief,
follow this brief for the implementation. In particular, do not preserve `core`,
the current module boundaries, Ibis-only interfaces, or legacy public APIs merely
to satisfy earlier guidance. This is a scoped override, not permission to ignore
credential protection, explicit failures, or data correctness.

Start from the current checked-out HEAD and integrate any subsequent user edits.
At authoring, Ops HEAD is `f318eeb7a7be495885a822671d1322c10dc624e4`.
Backward compatibility is not required: remove obsolete APIs, aliases, fixtures
and configuration paths; update callers, tests and documentation directly.
Do not add compatibility shims, parallel implementations or deprecation machinery.

Use the sibling `ppsc-salesforce` branch `native-athena-products`, not
`codex/native-athena-products`. Its reviewed HEAD is
`d024c15c95e581fbc10eaaf9b62e7b50630edda9`. Build and pin an immutable wheel from
the selected reviewed commit, including its hash and source identity. Do not
substitute a mutable branch dependency or editable sibling install in releases.

## Target organization

Use ordinary functions and native SQLGlot/GX objects. Keep configuration models
only where validation is useful; do not model every intermediate operation.

```text
src/ppsc_ops_data_quality/
    io.py
    runtime.py
    account_to_survey_results/
        queries.py
        suites.py
        workflow.py
```

Package initializers, CLI/hosting entry points and saved inputs may remain.
This is the application layout, not a demand to fold unrelated deployment tools
into these five files. Do not recreate `core`, generic providers, registries,
plugin bases, a query DSL or an alternative validation framework.

- **`io.py`:** shared lake DDL discovery/reading and export. Take clients,
  locations and paths explicitly; return native parsed definitions and useful
  export receipts. Exporting DDL does not execute it or deploy tables. Source
  metadata acquisition delegates to Salesforce package functions, not a new
  acquisition implementation here.
- **`runtime.py`:** shared native GX query registration and validation execution.
  Consolidate the useful behavior of `gx_queries.py` and the existing runner.
  Accept final comparison queries, native suites and explicit runtime
  dependencies; serialize each registered suite immediately before validation,
  retain native results and report execution failures explicitly. Keep necessary
  catalog/version checks here without recreating a runtime framework.
- **Domain `queries.py`:** Account/Survey relationships, event selection,
  expected/observed comparisons and genuinely domain-authored SQL/Python rules.
  Keep pure lake adaptation of Salesforce column definitions, resolved
  expressions and query projections here: physical names (including the
  `_history` convention), lake-specific columns/types, explicit aliases and
  role-specific snapshot predicates. Keep any necessary Ibis-to-SQLGlot bridge
  here, not in another compiler layer. No GX calls and no duplicate Salesforce
  Flow interpreter.
- **Domain `suites.py`:** authoritative native GX suite builders consuming
  prepared comparison columns and explicit provenance.
- **Domain `workflow.py`:** one visible composition of selected inputs, source
  projections, lake bindings, comparisons, suites and runtime execution. Supply
  domain lineage explicitly. Another domain follows the same small layout
  without a registration mechanism.

Move retained helpers beside their actual consumers. Delete the old modules
after updating callers; do not preserve their directory structure under new names.
Do not add a shared `projections.py` for the POC. Extract shared lake adaptation
only when a second concrete domain needs the same behavior.

## Projection inputs and ownership

The distribution imports as `salesforce`; `import salesforce as sf` is valid.
Use actual public submodule functions, not invented root-level methods.

Read native column definitions from **FieldDefinitions**, including the necessary
type, precision, scale and component evidence. Read **resolved column definitions
and expressions from Flows** through Salesforce's semantic analysis/projection
APIs. Retain source identities and provenance through the lake modifications.
Do not infer missing native evidence from provisional lake types.

At the reviewed Salesforce HEAD, field `to_sqlglot` returns a `ColumnDef`;
complete supported Flow `project_flow` returns Ibis tables. Neither fact proves
that a metadata-only SQLGlot SELECT API already exists.

- **[TODO in ppsc-salesforce]** Expose resolved Flow output definitions,
  expressions and complete logical projection SELECT ASTs through a small public
  API where currently unavailable. Reuse existing analysis and projection logic;
  include logical input roles, assignment/determinism evidence and provenance.
  Do not implement that missing source-semantic layer in Ops.
- **[TODO in ppsc-salesforce]** Ensure selected FieldDefinition acquisition
  supplies the native type evidence consumed by the column compiler, and provide
  a direct collection-to-column-definitions entry point if current public calls
  require consumers to duplicate native normalization.

Mark any additional missing source-semantic capability with the exact
`[TODO in ppsc-salesforce]` tag. Do not label deployment-specific history binding
as upstream work. If an upstream API is unavailable, state the gap; an explicit
bridge through existing native expressions is acceptable, a second interpreter
or a successful-looking placeholder is not.

## Correctness and authoring boundaries

- Bind Account BEFORE, execution lookups and Account AFTER independently.
  Select effective intervals, not a window of recently modified records.
  Preserve old unchanged versions, duplicate matches, missing parents, assigned
  NULLs, unassigned retained values and unmatched observations.
- Apply snapshot filters inside source subqueries before outer joins. Distinguish
  business-effective time from immutable physical snapshot IDs.
- Treat native definitions and lake DDL as inputs to compatibility checks, not
  proof of deployed types. Keep explicit physical overrides where actual names
  differ from the `_history` convention.
- Support direct Python query/suite builders without requiring Salesforce inputs.
  Permit intentionally authored comparison SELECTs through an explicit SQL path,
  not filename/string guessing. Before enabling file execution, define the
  smallest explicit metadata/parameter/lineage contract in this implementation;
  the previous TODO is not a permanent ban. Stop for a user decision if that
  contract has unresolved behavioral choices. Do not parse arbitrary comments
  as suite definitions or use ad hoc SQL string replacement.
- Do not add dbt. Retain native GX and one implementation of each rule.

## Implementation and acceptance

1. Pin the requested Salesforce wheel and resolve/report upstream gaps.
2. Implement the layout above; migrate concrete callers and remove obsolete
   modules, including `core`. Fold rather than duplicate shared behavior.
3. Update examples, documentation and tests to the new interfaces. Compatibility
   tests for removed APIs may be replaced; semantic tests must remain meaningful.
4. Verify row multiplicity, NULL/assignment evidence, temporal roles, exact suite
   registration/serialization, query provenance and explicit failure behavior.
   Run `uv run poe check`, `uv run poe check-queries` and
   `uv run poe check-synthetic`; report actual results and baseline blockers.

Preserve Poe operational ownership and the four root DVC release producers.
Update release inputs when files/wheels change; finalize release locks only from
real outputs. Never cache live validation or publication, include credentials or
record-level outputs in version control, or claim synthetic checks establish
live Athena/Glue acceptance.
