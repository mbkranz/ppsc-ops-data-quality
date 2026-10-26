# Applied PPSC review

The consumer uses the existing Salesforce distribution and APMP-generated JSON.
ODCS authoring and Athena DDL parsing stay in the data lake project. The separate
metadata package and its artifacts, evidence, projection and handoff abstractions
have been removed.

| Finding | Implemented result |
| --- | --- |
| A shared metadata framework obscured ownership | Native Flow and rollup functions live in Salesforce's existing domain modules; Ops retains temporal selection and comparisons |
| Ops duplicated producer schema interpretation | Native Ibis schemas and aliases come from generated `tables.json`; no ODCS or DDL parser dependency |
| Wrapper results hid the Ibis operations | Flow functions return named Ibis expressions; rollups return an Ibis table |
| Parsed data and provenance could select different bytes | Load once, cache immutable serialized values, return fresh dictionaries and check the selection before connecting |
| Python tuples differed from saved JSON lists | Native lineage uses JSON-compatible lists; registered GX suites preserve exact lineage on round trip |
| Extra receipt and compiler fingerprint protocols complicated packaging | Use the existing vendored wheel, lockfile and DVC release; record ordinary input, request and Flow hashes in run metadata |
| Stale docs and output files described the removed architecture | Rewrite active instructions and regenerate actual SQL, suites and diagrams |

The generic comparison core retains independent presence predicates, assigned
NULLs, retained BEFORE values, unknown routing, missing parents, duplicate matches,
ordered composite keys and unmatched observations. The native adapters keep
source binding explicit; eligibility and snapshot policy remain with the caller.

The synthetic catalog is provisional. Runtime preflight and selected data
versions remain separate from offline source compilation. No live Athena/Glue
acceptance or deployment is claimed.
