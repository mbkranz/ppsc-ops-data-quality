# Native/APMP migration inventory

The October 26 implementation preserves the useful PR 8–12 comparison fixes and
replaces the provisional ODCS schema boundary. The producer's migration inventory
covers Salesforce dictionary content; this table records consumer-owned elements.

| Previous source/pointer | Meaning | Destination/treatment | Verification |
| --- | --- | --- | --- |
| `core/schemas/validation-inputs.odcs.yaml#/schema/*/properties/*/logicalType` and decimal options | Provisional field types only | Migrated to producer APMP provisional fixture DDL; generated copy pinned in `metadata/lake/tables` | Shared schema reader and source-type regression tests |
| Same profile relationship declarations | Survey→Contact, Contact→Account, Account→Contact ordered joins | APMP explicit relationships in generated bindings | Exact workflow relationship checks; composite-key/fanout GX fixtures |
| Same profile purpose/status | Unverified compatibility profile | Manifest/binding/catalog provisional flags and explicit synthetic evidence note | Preflight/run metadata retains provisional status |
| Same profile absent required/enum/display logic | No authored requiredness/value-set/display semantics existed in this profile | No invented rules; existing native and workflow checks retain policy | Independent required/must-null, false/zero/sentinel/NULL and unknown-evidence fixtures |
| `metadata/flow.json` and `source_catalog.json` | Exact native identities, relationships and Flow behavior | Saved selected native artifacts; original supplied Flow bytes preserved exactly | Digest/exact-version checks, source pointers and mutation isolation |
| `expected_value_contract()` generated object copies | BEFORE/expected roles and authoritative native pointers | `expected_value_provenance()`, `expected-values/v2`, ordinary field bindings | Pointer traversal and unchanged-source tests |
| Runtime `schema_overrides` | Untracked type changes | Nonempty values rejected; changes originate in reviewed APMP definitions | Migration-message test and changed-definition hash tests |
| Runtime database-only `history` names | Partial physical relation identity | Explicit catalog/database/relation per selected dataset | Renamed physical key/value/table execution and reported identity tests |
| Workbook-derived survey rollups | Existing proven aggregate behavior, not certified native rollups | Retained workflow implementation and explicit lineage | Existing rollup fixtures and no-native-fallback test |

The retired profile contained no authored allowed-value sets, requiredness,
uniqueness or conditional predicates. Generic source-independent comparison
fixtures continue checking those independent policy/evidence roles where supplied.
Native field links do not create relational keys. Missing native metadata remains
unresolved; this migration does not certify native rollup equivalence.

Live AWS acceptance has not been executed here. The packaged catalog is an
explicit synthetic fixture. Catalog preflight tests use injected fake clients;
no credentials, cloud instance metadata or real participant data are needed.
