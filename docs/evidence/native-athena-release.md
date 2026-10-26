# Native/APMP release evidence

The coordinated producer is [Salesforce PR 7](https://github.com/mbkranz/ppsc-salesforce/pull/7).
This consumer retains the useful PR 8–12 chain and applies the PPSC design
reference: structured configuration/receipts, explicit runtime dependencies,
native Ibis/GX interfaces and visible orchestration.

| Identity | Frozen selection |
| --- | --- |
| Compiler/definition source revision | `7f4f3108ea0910ebd3649c770242f69e0301917c` |
| Compiler | `ppsc-metadata==0.3.0` |
| Compiler wheel SHA256 | `c26afb47820ecabc654f4f73b098af3e96062329815d09304e8f5c3686074ecf` |
| Installed compiler source fingerprint | `a74bb14dd0640a500d3050b32d22ae2c7a08c2f188107df8c98d8f7e11e5124a` |
| Generated APMP/native manifest SHA256 | `fa86c65c60ead5b220036b057eee70d909cb390eba6bba350edc2d9d524682c5` |
| Original native source revision | `1eedb2abcf5cac6471fb6cc45e5a40c007982854` |
| Engine conversion profile | Ibis 12.0.0 / SQLGlot 30.24.0 |
| Manifest/evidence formats | `projection-inputs/v2` / `native-apmp/v2` |

The vendor wheel and generated handoff are one selection. Runtime verifies
installed compiler source bytes, installed input hashes, mappings and the
compiled request. Fresh returned models cannot change cached serialized inputs.
The APMP physical schema is read by the shared converter; Ops owns no authored
duplicate. Source tables use real physical fields followed by explicit aliases.

Fresh review traced the current Flow's four physical SQL occurrences and the
rollup's two occurrences: each receives its selected native SQLGlot
`FOR VERSION AS OF` binding. Reports derive actual selected sources from submitted
SQL scopes, excluding CTEs and unused selections. Live catalog preflight checks
kind, selected columns/types, partitions and snapshot-era schema separately from
static receipt verification. Uninspectable/changed views remain unsupported.
Mutable diagnostic runs explicitly report stable-input assertions unestablished;
their GX metric success does not imply live acceptance.

Executed gates include `poe check`, `check-queries`, `check-synthetic`,
`render-queries`, `suite-diagrams`, actual DVC release reproduction/freshness,
and the installed-bundle smoke outside the checkout. The pinned Linux producer
uses Python 3.11.17, uv 0.12.23 and pip 25.3. The smoke keeps
`--no-index --no-cache`, verifies compiler 0.3.0, compiles the installed queries
and runs all 56 synthetic expectations (30 Flow, 26 rollup).
Its actual Parquet outputs contain two validation rows and 56 expectation rows,
preserving one expectation per row. Native JSON, suites, SQL, Data Docs and
manifest outputs remain present. Linux 3.11/3.12 and Windows automation CI
definitions remain intact; remote CI status is separate from local checks.

The full test run exposed an outdated generated SQL example, which was
regenerated with its suites and diagrams. Final verification runs against the
frozen wheel and updated generated inputs. Behavioral coverage includes
renamed physical tables/keys/values, different objects and ordered composite
keys, non-Salesforce-shaped comparisons, assigned NULL and unassigned retention,
unknown evidence, missing/duplicate/unmatched rows, native source/hash mutation,
same-version installed compiler changes, catalog drift and snapshot application.

Live lake acceptance remains unestablished: no configured AWS profile/region,
real catalog snapshot, reviewed physical mappings, selected actual data versions
or independent BEFORE/AFTER evidence is available here. The bundled catalog is
explicitly synthetic/provisional. No live Athena query, deployment or report
publication was performed. See [the semantic migration inventory](native-apmp-migration.md).
