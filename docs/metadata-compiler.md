# Native Salesforce compilation and APMP inputs

The existing `ppsc-salesforce[ibis]` distribution supplies Flow queries from
`salesforce.entities.flows.queries` and rollups from
`salesforce.entities.field_definitions.rollups`. APMP owns ODCS authoring, Athena
schema parsing, physical aliases, keys and history definitions. Ops consumes
APMP's generated `tables.json` and saved native JSON, then owns event selection,
historical alignment, comparisons and native GX suites. ODCS is not an Ops dependency.

The selected files live in `account_to_survey_results/metadata`. Native Ibis
schemas are reconstructed from generated field/type pairs; explicit selections
apply physical-to-logical aliases. Git, the vendored wheel and the locked release
pin these files. No separate metadata package or handoff manifest is required.

`metadata_inputs()` and `metadata_request()` return fresh values from an immutable
serialized compilation cache. `metadata_receipt()` checks the selected bytes,
request and compiler version before runtime connections. Its ordinary run metadata
records source revision, exact Flow version/hash, ODCS identity and inputs digest.

The packaged catalog remains a provisional synthetic fixture. Offline compilation
does not establish real lake compatibility or Flow applicability.

## Native expression boundary

The compiler preserves `flow_context`, `flow_assignments`, `rollup_values`,
plain named Ibis values and independent presence predicates. Native expressions
remain Ibis tables/values. No ODCS model, expression serialization, query registry
or acquisition dependency is needed.

`sources.salesforce.flow_comparison` takes explicitly supplied generated inputs, Flow
request, prepared record, independently observed table and `ComparisonSpec`.
Fields must occur in the selected APMP mapping and native source identities.
Ordered relationship bindings remain separate from field provenance.
`sources.salesforce.native_rollup_comparison` requires actual selected native
rollup metadata; workbook-derived rollups do not silently become native rules.

The comparison core remains independent of Salesforce. It supports differing
expected/observed column names, ordered composite keys, strict key/value types,
missing keys/parents, duplicate fanout and unmatched observations. Assigned NULL,
unassigned retained BEFORE values and unknown routing remain distinct. Required
and must-be-null predicates are independent; one is not the inverse of the other.

Suite metadata carries ordinary provenance: native source pointers and
hashes, APMP definition identity, BEFORE/expected/observed roles and output aliases.
`expected_value_provenance()` does not construct a separate comparison contract.

## Runtime evidence

`params.example.yaml` binds dataset IDs to explicit catalog/database/relation
locations and per-relation data versions. Runtime types, keys and transformations
cannot be overridden outside the selected producer definitions. Database-only
`history` bindings and nonempty `schema_overrides` are rejected.

`runtime.preflight.check_catalog` takes an explicit Athena client. It compares
selected columns/types, partition declarations and relation kind. Unreferenced
additions are recorded without automatically changing the schema. Missing or
incompatible metadata blocks the affected check before GX validation queries.
Views currently require additional captured deployed-definition/dependency
verification before live acceptance.

An `iceberg_snapshot` binding supplies an exact positive snapshot ID. Preflight
executes a bounded schema probe using `FOR VERSION AS OF`; the same IDs are
applied through native SQLGlot Version nodes to every physical occurrence in all
GX query assets. Run metadata records IDs, schema probe execution identity, exact
source SQL, checked catalog digest/time, resolved locations and configuration
hash. Independent table snapshots establish neither a cross-table transaction
nor business-time alignment.

Mutable input can run only as an explicit diagnostic selection with
`require_repeatable_reads: false`. Its inability to guarantee repeatable reads
across GX metric queries is recorded. Stable-input assertions are unestablished
and blocked by default. Timestamp fields alone are not data-version evidence.

Local selection/schema/history checks occur before client creation. Library
callers supply an Athena client or explicit factory; the CLI and Glue adapter
provide factories after local checks. This keeps offline use free of credential
resolution and network access.

## Refresh

1. Capture and review actual native and lake evidence in Salesforce/APMP.
2. Build the selected APMP product through its DVC stage; review its dictionary,
   unresolved coverage and provisional status.
3. Build the existing Salesforce wheel from the reviewed source revision. Freeze
   that wheel and copy `tables.json`, `flow.json`, `source_catalog.json` and
   `observed.json` into the consumer selection.
4. Update the wheel reference and lockfile. Regenerate suites, SQL and diagrams
   through the existing Poe tasks.
5. Run the installed-release smoke and real DVC producers.
6. Use explicit online preflight and selected snapshots for a targeted Athena run.

Real physical definitions, historical observations, Flow applicability and rollup
policies remain evidence gates for the checks that depend on them.
