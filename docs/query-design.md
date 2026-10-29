# Query authoring

`account_to_survey_results.queries.flow_account_query` returns an annotated SQLGlot
SELECT. Supply the selected inputs, history relations, event ID, ordered BEFORE /
execution / AFTER instants, org-local `flow_run_date` and verified `eligibility`
(Boolean or unknown). Start-transition eligibility is an explicit caller fact;
completion status alone cannot establish it. Native Salesforce controls source semantics.

`history_tables(inputs=..., locations=...)` constructs selected physical relations
from parsed lake DDL and explicit aliases. Effective half-open intervals are applied
inside each role before joins. Physical Iceberg snapshot IDs are bound separately by
`runtime.prepare_query`; they do not imply business-effective time or cross-table atomicity.

`flow_record_id` remains native event identity. Ops extends the native projections with
comparison context alongside that identity, without rejoining on a potentially duplicate
Id. Duplicate parent and AFTER matches remain findings. Comparisons preserve assignment
and determinism flags; unassigned values retain BEFORE. Both-null pairs retain the native
GX accepted/excluded-denominator policy; one-sided NULLs fail. Unknown scope/computation
is checked separately. Rollups remain explicitly authored SUM/CASE rules until verified
native rollup metadata is selected; they are not inferred from the Flow.

## Ordinary Python builders

Direct SQLGlot SELECTs and native `gx.ExpectationSuite` objects can be passed to
`runtime.prepare_validation(context, source, query, suite, name=...)`. Register the suite
in the supplied GX context first. No Salesforce inputs are required. Use explicit native
expressions; runtime rejects wildcard final projections, case-colliding outputs, recursive
CTEs and conflicting or unread physical snapshot bindings. Query registration does not
execute DDL or fetch a batch. `run_validations` serializes the registered suite immediately
before execution, retaining native failed expectations and partial results on errors.

## Explicit authored SQL path

Call `workflow.prepare_authored_validation` with `sql_path`, `contract_path`, scalar
`values`, a caller-built registered `suite`, and an audit `output_path`. It loads exactly
one SELECT and the YAML contract below. There is no filename guessing, comment-driven
suite creation, dynamic builder import or string interpolation.

```yaml
schema_version: 1
definition_id: authored_count
suite_name: authored_count_suite
dialect: athena
parameters:
  cutoff: {type: date, nullable: false}
relations:
  records: {catalog: lake, database: source, relation: survey_history}
outputs:
  record_id: {role: key, rule_id: source/id, description: Source record identity}
  expected: {role: expected, rule_id: authored/count, description: Authored expected count}
```

```sql
SELECT records.id AS record_id, CAST(1 AS BIGINT) AS expected
FROM records WHERE records.valid_from < :cutoff
```

Use named scalar placeholders. Declarations, used placeholders and supplied values must
match exactly. Types: string, Boolean, integer, exact decimal with precision/scale, date,
and timezone-aware timestamp normalized to UTC. Nullable values require explicit
permission; ambiguous naive timestamps, lossy decimals and arbitrary expressions fail.
Relations are bound separately through native identifier nodes. One structured lineage
entry is required for each output, with key/expected/observed/evidence role and authored
rule identity. Suite names must match. Unknown contract keys, versions and dialects fail.

The executable SQL and `.lineage.json` sidecar retain source/contract hashes, typed
parameters, source graph, outputs and native definition evidence when available. Those
bound run artifacts belong outside Git. SQL text does not round-trip structured AST
metadata; preserve the sidecar or native `dump()`/`load()` representation.
