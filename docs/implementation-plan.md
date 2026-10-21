# Alternative implementation: one SQL check per file

Prepared October 20, 2026. This branch is an independent alternative to PR #1,
based on its implementation at `d0add86`. Choose one implementation; do not merge
both alternatives together. The initial Ibis plan is preserved in PR #1 history.

## Design study before implementation

| Tool and official source | Observed pattern | Decision here |
| --- | --- | --- |
| [dbt data tests](https://docs.getdbt.com/docs/build/data-tests) | Singular tests are one failing-row SQL query per file; generic tests are separately parameterized. | Prefer a concrete check file before introducing a reusable DSL. |
| [SQLMesh audits](https://sqlmesh.readthedocs.io/en/stable/concepts/audits/) | Audits query bad rows; generic audits accept arguments and can reference a selected model. SQLMesh permits multiple audits per file. | Use zero failing rows as success; deliberately choose one check per file for this repository. |
| [Soda filters](https://docs.soda.io/soda-documentation/soda-v3/sodacl-reference/filters) | Shared filters reduce repetition, but raw failed-row SQL does not inherit dataset filters automatically. | Supply selected populations explicitly on every referenced side of a relationship. |
| [Narwhals SQL generation](https://narwhals-dev.github.io/narwhals/generating_sql/) | Polars-style functions can generate DuckDB SQL, then use SQLGlot for other dialects. | Compile only the tested expressions and keep Athena execution separate. |
| [GX SQL expectations](https://docs.greatexpectations.io/docs/core/customize_expectations/use_sql_to_define_a_custom_expectation/) | Unexpected-row queries use native validation, results, and reporting. | Retain GX rather than build another executor or report format. |

These patterns inform this design; neither dbt nor SQLMesh is a new runtime
dependency. This repository validates existing lake tables and does not need their
model materialization, deployment, scheduling, or state-management machinery.

## Implementation plan

1. Preserve configuration, data access, batch selection, subject suites, and runner
   separation, plus all operational population semantics.
2. Replace Ibis with the branch's authoring approach. Use SQLGlot SQL types for
   declarations and physical schema preflight; never cast bad data into compliance.
3. Keep an explicit list of three subject populations in `run.py`. Reuse the
   existing GX validation/reporting path and existing Poe commands.
4. Verify exact selected row identities, half-open date/timestamp boundaries,
   null/blank keys, case/whitespace identity, duplicate/absent parents, repeated
   children, and current flags on both sides. Verify compiled Athena SQL locally.
5. Run locked lint/format/tests, the credentials-free preview, and wheel packaging.
   Preserve pending live acceptance and combined-evidence work in the existing docs.

### SQL-file alternative

Keep `config.py`, `athena.py`, `batches.py`, `run.py`, and all three `gx/<subject>.py`
modules. Add only sibling `gx/<subject>/*.sql` files and a shared loader in the
existing `gx/__init__.py`. Retain native structural expectations; represent all
nine identity/reference predicates as one failing-row query per file.

Use `{batch}` for the selected subject and named `account_state` /
`account_contact_relation_state` relations for joins. The runner supplies the
selected relation SQL. The loader adds only used relations as CTEs, rejects
unknown/physical relations and multiple/nonquery statements, and constructs native
GX unexpected-row expectations. File paths provide stable rule identities; SQL
comments provide human explanations and evidence. No macro language or sidecar
configuration is required. New files in an existing subject are discovered in
sorted order, without editing Python or an explicit list of rules.

`batches.py` uses short SQL functions. Remove Ibis and avoid adding Narwhals or
DuckDB to production dependencies for this alternative. DuckDB is for tests only.
Narwhals can still be present transitively through GX reporting dependencies.

## Preserved contracts and acceptance

- Keep old unchanged records and `[valid_from, valid_to)` state selection.
- Pin every physical source with the same explicit `--lake-as-of` timestamp.
- Count duplicate parents without multiplying or deduplicating child rows.
- Keep missing keys, absent parents, and ambiguous matches separately explainable.
- Keep native results, Data Docs, suite JSON, run provenance, and exit codes 0/1/2.
- Full failure counts remain distinct from diagnostic samples capped at 200 rows.
- Keep credentials, live bindings, reports, and participant data out of Git.

See [README](../README.md) for authoring and commands and
[Acceptance](acceptance.md) for controlled/live gates. Synthetic tests and offline
SQL compilation do not establish live Athena compatibility. Real bindings,
credentials, completed-delivery evidence, and the operational/graph rule review
remain necessary before claiming production readiness.
