# Native Salesforce compilation and APMP handoff

Ops uses the offline `ppsc-metadata` compiler with a pinned `projection-inputs/v2`
selection. Salesforce owns saved native fields, relationships, exact Flow versions
and rollup evidence. APMP owns lake DDL and physical-to-native mappings. Ops owns
event selection, eligibility, historical alignment, settlement, comparisons and GX.

The generated handoff lives in `account_to_survey_results/metadata`. Its manifest
hashes native source artifacts, the captured lake catalog, schema-bearing Athena
DDL and explicit bindings. APMP and Ops share the same pure DDL-to-Ibis reader.
The installed wheel and generated inputs are one frozen selection; a rollback
restores both together. Version 1 receipts are rejected with a migration message.

`metadata_inputs()` returns freshly parsed values from an immutable serialized
compilation cache. Mutating a returned Flow, mapping or request cannot change
subsequent compiled behavior. `metadata_receipt()` rereads installed selected
bytes and rejects same-path replacements, manifest changes, compiler changes or
request changes before runtime connections. The compiler source fingerprint is
derived from the same frozen wheel and rechecked before native compilation and
receipt creation, so a same-version installed-source replacement also fails.

The packaged evidence is provisional. Its catalog is a synthetic migration
fixture rather than observed AWS evidence. Native Salesforce facts remain saved
with their identifiers and pointers; unmatched native/lake evidence remains
unresolved rather than becoming a fabricated mapping.

## Native expression boundary

The compiler preserves `flow_context`, `flow_assignments`, `rollup_values`,
`expected_values` and independent `presence_requirements`. Native expressions
remain Ibis tables/values. No ODCS model, expression serialization, query registry
or acquisition dependency is needed.

`sources.salesforce.flow_comparison` takes a supplied verified bundle, Flow
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

Suite metadata carries ordinary versioned provenance: native source pointers and
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

1. Capture/review actual native and lake evidence in the Salesforce/APMP producer.
2. Build the selected APMP product offline and review unresolved/provisional items.
3. Build the exact compiler revision; freeze its wheel and generated selected
   handoff together. Copy only manifest-selected artifacts, preserving their paths.
4. Update the consumer wheel reference, lockfile, compiler constants and configured
   manifest hash. Regenerate suites, SQL and diagrams through existing Poe tasks.
5. Run the installed-release smoke and real DVC producers; do not invent locks.
6. Use explicit online preflight and selected snapshots for a targeted Athena run.
   Report catalog compatibility, data identities and semantic evidence separately.

The source dictionary and offline checks do not establish real lake acceptance.
Real physical definitions, historical observations, Flow applicability and rollup
policies remain evidence gates for the checks that depend on them.
