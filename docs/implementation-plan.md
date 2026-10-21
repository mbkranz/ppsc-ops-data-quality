# Alternative implementation: simpler SQL check authoring

Prepared October 20, 2026. This branch is an independent alternative to PR #3,
based on its head `9b95662`. The original PR stays unchanged. Choose one
implementation rather than merging both alternatives into main.

## Review of PR #3

| Finding | Evidence and effect | Change |
| --- | --- | --- |
| SQL text substitution changes literals | `WHERE id = '{batch}'` is silently compiled as `WHERE id = '__dq_batch'`. Literal braces also collide with GX string formatting. | Author `FROM batch` as normal SQL; bind table nodes and handle native GX/SQLAlchemy formatting internally. |
| Injected CTEs can follow their consumers | `WITH selected AS (SELECT * FROM account_state) SELECT * FROM selected` puts `account_state` after `selected`; a local DuckDB execution fails with a missing-table error. | Inline the selected relation at the external table node; preserve authored CTE order and scope. |
| Repeated suite and rule metadata obscures authoring | Three modules repeat structural-suite setup; rule metadata copies the entire description into a generic rationale. | One shared suite builder, compact subject modules, shared suite evidence, authored SQL descriptions. |
| Inspection stores the same type twice | Every column repeats identical `type` and `declared_type` strings. | Keep `type` as the single physical schema field. |

The review reproduced the first two failures before implementation. Regression
fixtures exercise native GX execution, rather than checking only generated text.

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
2. Replace placeholder substitution and CTE injection with table-node binding.
   Retain SQLGlot type checks and physical preflight without coercing input data.
3. Keep an explicit list of three subject populations in `run.py`. Reuse the
   existing GX validation/reporting path and existing Poe commands.
4. Verify exact selected row identities, half-open date/timestamp boundaries,
   null/blank keys, case/whitespace identity, duplicate/absent parents, repeated
   children, and current flags on both sides. Verify compiled Athena SQL locally.
5. Run locked lint/format/tests, the credentials-free preview, and wheel packaging.
   Preserve pending live acceptance and combined-evidence work in the existing docs.

### SQL-file alternative

Keep `config.py`, `athena.py`, `batches.py`, `run.py`, and all three
`gx/<subject>.py` modules. The subject modules supply columns and assumptions to
one shared native suite builder in the existing `gx/__init__.py`. Each of the nine
identity/reference checks remains in its own `gx/<subject>/*.sql` file.

Author `FROM batch` for the selected subject. Join `account_state` and
`account_contact_relation_state` for cross-table checks. The loader binds external
table references to selected subqueries, preserving local CTE scope and aliases.
It constructs native GX unexpected-row expectations and rejects unknown/physical
relations, multiple/nonquery statements, and top-level limits.

File paths supply stable rule identities. Opening SQL comments supply explanations
and rule evidence. Shared sources and population assumptions live once in native
suite metadata. There is no macro language, sidecar configuration, or registration
step for a new check in an existing subject.

`batches.py` retains short SQL functions. Dependencies are unchanged from PR #3;
DuckDB remains a development dependency. GX formatting and SQLAlchemy escaping
are handled at the loader boundary so SQL authors can write literal braces and
JSON normally.

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
