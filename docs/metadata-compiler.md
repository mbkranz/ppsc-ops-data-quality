# Standalone definitions and optional Salesforce authoring

Ops executes reviewed local Ibis builders. It imports neither `salesforce`,
`ppsc_metadata` nor ODCS. Saved metadata is detached evidence: editing a Flow JSON
file does not change a rule. A selected Flow change requires reviewing the local
builder, evidence and independent expected-result cases together.

## Installed definitions

`account_to_survey_results/inputs/*.sql` owns validation-input types. The four
schema-only Athena declarations cover Account, Contact, Survey Result and shared
history metadata. Core converts them through SQLGlot to native Ibis schemas.
They are provisional profiles, not deployed-catalog certification.

`flow.py` owns the pinned QA2 Flow `301SL00000dpJqKYAU`: ordered routing, four
lookups, age at the explicit org-local execution DATE, and native assignments.
`queries.py` owns relationship/history/event bindings, comparisons and the
existing 19 workbook-authored rollups. The saved source revision is
`d769cb047a80d5ff22a011ece2d6671b71fb0646`. Detached lineage was migrated from the
previous producer at `1eedb2abcf5cac6471fb6cc45e5a40c007982854`; this is recorded
honestly as provenance rather than relabeling it as a new export.

Per-field expected value, assignment and determinism remain separate. Assigned
NULL remains NULL; unassigned fields retain BEFORE. First-row lookup ties do not
invent a tiebreaker; unsorted ambiguous payloads become unknown. Private event
identities preserve duplicate triggers. Missing parents and duplicate observations
remain visible. The independent tests retain the native consent/assent truth tables.

`metadata/lineage.json` retains source pointers and branch evidence independently
of DDL. `metadata/selection.yaml` records the reviewed selection and aliases;
it is not a generic executable Flow language. The `ops-definitions/v2` manifest
hashes DDL, builder/helper source, selection, lineage and original source evidence.
Public metadata reads return fresh copies. A run reverifies the installed bytes
against the immutable snapshot used during query construction. Native suite and
report metadata carry the receipt. A receipt identifies code/definitions; actual
record-state snapshots and physical source pins identify data.

Runtime YAML retains explicit `metadata.org`, `flow_version_id` and
`manifest_sha256` selection. A mismatch fails before connecting or creating GX.
Update the example hash only after accepting a reviewed definition manifest.

## Refresh reviewed definition hashes

After changing the listed source/DDL/evidence files, create a fresh candidate:

```bash
uv run poe capture-definitions --output build/definitions/reviewed.json
```

Review its source identities, coverage, artifact list and digests before copying
it to `src/ppsc_ops_data_quality/account_to_survey_results/metadata/manifest.json`.
The capture operation updates digests only. It does not acquire source metadata,
interpret a Flow or claim that reviewed code matches the source. Independent
semantic fixtures are required; producer parity is supplementary evidence.

## Optional offline producer

The pinned Salesforce revision's implemented entry points provide annotated scalar ColumnDefs,
`flow_context`, `flow_assignments`, `flow_queries` and `flow_lineage`. Prepared
analysis entry points discussed during the initial review were proposals at
that snapshot; this task deliberately uses the immutable authoring revision. The pinned Ibis experimental Python decompiler cannot round-trip this
Flow; no automatic Python emitter is assumed.

`poe author-salesforce` uses a separate environment with a producer pinned to
`a534c63353680e41d12e3b55997a125ba703c675`. The normal dependency lock and test
installation contain no producer. The operation reads saved flattened native
field JSON and an explicit YAML selection, writes candidate DDL and source
evidence, and optionally writes named Flow query references. No acquisition or
live query occurs. Output must be fresh; the manifest is written last.

Paths below are explicit paths relative to the invocation directory:

```yaml
fields_file: build/saved/fields.json
objects:
  Account: [Id, Basics_Date_Time__c]
# Optional Flow references require all four explicit bindings:
# flow_file: build/saved/flow.json
# selection_file: build/saved/selection.yaml
# record_ddl: build/saved/prejoined-event-before.sql
# flow_run_date: 2026-10-21
# lookup_ddls:
#   Survey_Result__c: build/saved/survey-input.sql
```

```bash
uv run poe author-salesforce --config build/authoring.yaml --output build/candidate
```

Choose the full required field closure, including trigger fields, relationship
keys, BEFORE values, lookup filters/sort/output fields and formula dependencies.
Missing selected fields or compiler-required bindings fail instead of being
invented. Native field types do not determine physical aliases/history policy.
Generated SQL references use an explicitly supplied inspection DATE and label
eligibility=true; they are logical templates, not historical reconstructions or
runtime SQL-file inputs. Structured evidence is written separately because SQL
comments do not serialize SQLGlot `.meta`.

Use these references to help author local Ibis code. Review it against independently
authored expected results. Keep one executable implementation after cutover.
Acquire/review actual native rollup definitions before replacing the existing 19
application rollups. Generic users supply their own expected Ibis relation to
`core.comparison.compare_values`; metadata-driven source adapter interfaces were
removed. Library inputs remain native tables and schemas.

See [the design review](athena-ddl-standalone-design-review.md) for the decision
and alternatives. Authored SQL execution remains deferred by
[`runtime/TODO.md`](../src/ppsc_ops_data_quality/runtime/TODO.md). Offline success
does not establish deployed catalog or live Athena/Glue acceptance.
