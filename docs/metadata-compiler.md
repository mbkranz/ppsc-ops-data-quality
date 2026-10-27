# Native Salesforce compilation and Ops lake bindings

`ppsc-salesforce[ibis]` interprets saved native Flow/rollup metadata. It supplies
`flow_context`, `flow_assignments`, and `rollup_values` as native Ibis functions.
Field definitions compile through `salesforce.entities.field_definitions.schemas.to_sqlglot`;
Ops uses native `ibis.Schema.from_sqlglot` when a selected source schema is needed.
Unsupported source types remain explicit evidence; they are never guessed from a lake type.

Ops owns the Account/Contact/Survey Result physical schema files under
`account_to_survey_results/definitions/`. These provisional schema-only Athena
DDLs are not deployable storage definitions. `account_to_survey_results.inputs`
contains the explicit aliases, keys, relationship and history bindings and reads
DDL into nullable Ibis schemas. No `tables.json`, ODCS definition, or generated
APMP product is a runtime input. The former authored descriptions and policies
are retained separately in `definitions/descriptions.json`.

The saved Flow, native field catalog, and observed catalog remain under
`account_to_survey_results/metadata/`. Git, the vendored Salesforce wheel and the
existing release graph pin them. `metadata_inputs()` returns fresh parsed values
from an immutable serialized compilation cache. `metadata_receipt()` checks the
actual selected files, application bindings, request and compiler version before
online client creation. It records definition/input digests and source coverage
separately from provisional status. The catalog is synthetic and no real lake or
Flow applicability is certified by these files.

## Explicit query and provenance boundaries

The caller supplies trigger identity, lookup candidates, BEFORE state, independent
AFTER observations, execution date and eligibility. Salesforce resolves supported
native lookups, formulas, decision priority and assignments against those inputs.
Ops binds catalog/database/relation, historical instants and per-table data
versions. The comparison core receives native tables and explicit key/value/evidence
bindings and contains no Salesforce object names or metadata loading.

`field_definitions()` keeps original native field records and exact source
pointers/hashes. Supported records use annotated SQLGlot ColumnDefs; missing type
evidence remains `unsupported` alongside its original record. Ibis schema
conversion does not carry these annotations. The domain's `PROJECTION_LINEAGE`
therefore carries field definitions and native Flow evidence alongside query
composition, and `core.queries.sql.to_sqlglot()` attaches it to final projections
after SQL rewrites. Expected and independently observed roles remain distinct.
Readable comments are escaped summaries; structured `meta["ppsc"]` and serialized
GX suite metadata retain the full provenance. Native SQLGlot copy/dump/load retains
that metadata; rendering and reparsing SQL alone does not reconstruct it.

Duplicate/missing keys, join fanout, unmatched observations, assigned NULL,
retained BEFORE values and unknown routes remain observable. Required and
must-be-null predicates remain independent application policies.

## Capture and live acceptance

`uv run poe discover-lake` explicitly discovers the catalog using `lake/params.yaml`.
`uv run poe capture-lake -- --help` describes selected Glue storage/view capture.
Both operations are separate from the four offline DVC release producers.
They never execute DDL and do not run during imports or schema construction.

Runtime preflight checks selected native physical types before conversion to
Ibis, including distinctions such as CHAR versus VARCHAR. It rejects duplicate
and case-colliding declarations, verifies schema/partitions/relation identity,
and records unreferenced additions. Native evidence coverage is recorded separately
from definition approval. Views still require deployed-definition verification.

An explicit Iceberg snapshot is schema-probed with `FOR VERSION AS OF` and applied
to every physical query occurrence. Separate table snapshots establish no
cross-table transaction or business-time alignment. Mutable inputs require an
explicit diagnostic selection and cannot establish repeatable reads across GX
metric queries. Flow checks also require sufficient history resolution.

## Refresh

1. Explicitly capture and review the selected native and lake evidence.
2. Edit the Ops schema files and bindings as required; retain source differences
   and provisional/coverage limitations explicitly.
3. Build and pin the reviewed Salesforce wheel and update the existing lockfile.
4. Run `poe check`, `poe check-queries`, and `poe check-synthetic`; regenerate
   affected SQL, suites and diagrams using existing commands.
5. Run installed-release smoke and the real DVC producers in their supported
   release environment; commit locks only from actual outputs.
6. Perform separately authorized targeted Athena validation with explicit source
   versions and independently observed historical records.
