# Metadata compilation boundary

The 19 Flow output fields are compiled from a saved native QA2 Flow through
`ppsc-metadata==0.2.0`. The application supplies the selected fields, BEFORE/target
bindings, source relations, eligibility predicate and org-local execution DATE.
Its compatibility aliases preserve comparison columns and GX expectation IDs;
they do not reauthor branch predicates, lookup filters, formulas or assignments.

## Pinned evidence

The packaged `account_to_survey_results/metadata/manifest.json` selects
`Survey_Result_Survey_Completion_Updates`, version `301SL00000dpJqKYAU`, from the
producer fixture at revision `d769cb047a80d5ff22a011ece2d6671b71fb0646`. Native Flow
and source catalog bytes are copied unchanged. SHA256 verification covers those
artifacts and `core/schemas/validation-inputs.odcs.yaml`; exact Flow identity is
checked before compilation. Source schemas are derived from that ODCS profile.
Three explicit relationship bindings are checked against normalized object/property
foreign keys. Composite keys retain ordered source/target pairs.

The contract is a **provisional draft compatibility profile** migrated from the
existing ops schema declarations. The saved catalog supplies identities and
relationships, without sufficient type evidence to certify the profile. The
manifest is marked provisional and does not certify current QA2 or production
activation. Reviewed org contracts and deployed catalog types remain local work.

Runtime YAML must select `metadata.org`, `flow_version_id` and `manifest_sha256`.
A mismatch fails before creating connections or a GX context. At each run the
installed artifacts are reverified against the compiled snapshot. Native suite
metadata and run/report metadata carry the receipt: manifest hash, all input
hashes, org, Flow/version, source revision, contract identity/version, compiler
version, source revision, wheel hash, Flow-request hash and provisional coverage. Report Parquet rows retain it in
`run_metadata_json`. A receipt proves the selected input bytes, not live fitness.

The independently built compiler wheel is pinned under `vendor/` so CI and Glue
can install it without Salesforce application dependencies or private Git access.
The uv lock and DVC requirements/dependency stages include it. This is a temporary
transport until the package has an independent distribution channel.

## Native behavior and retained policy

Ordered decisions and defaults produce direct Ibis CASE expressions. Assigned
NULLs remain NULL and unassigned fields retain BEFORE. Native lookup filters,
first-row selection, sort keys and formulas are interpreted from the saved Flow.
Ambiguous lookup values expose determinism evidence; duplicate input events are
retained with a private row identity. The caller still owns event eligibility,
start/changed-record criteria, automation exemptions, snapshot/deletion policy,
relationship binding, launch scope, execution DATE and asynchronous settlement.
Unsupported operations in the requested closure fail explicitly. Unrelated
unsupported formulas/actions do not block a supported field slice.

The saved native metadata differs from the former handwritten rules:

- Primary consent without an earlier qualifying consent assigns the new timestamp;
  the branch with a prior consent retains the existing earliest value.
- EHR consent without an earlier qualifying consent assigns the consent timestamp;
  the prior-consent branch assigns reconsent.
- Pediatric assent uses the native AND/default branches. Missing permission or
  missing earliest consent takes the new timestamp branch; both present retains
  the existing earliest value. A four-case test covers that truth table.

Mutation tests alter native assignments and predicates without editing Python,
including explicit NULL assignment. Existing tests retain independent observations,
missing parents, duplicate observations/events, launch scope and native GX checks.
The producer exporter additionally checks exact selection, source hashes, fresh
output ownership and tamper rejection. Workbook row references remain supplemental
navigation; native JSON pointers and decision paths are the Flow rule evidence.

The shared native COUNT adapter has synthetic execution coverage, including
zero-child and duplicate-parent cases. **The existing 19 application rollups remain
unchanged.** Migrating them requires verified native field metadata; neither
workbook SQL nor the existing Python implementation is relabeled as native source.

## Complete acceptance locally

1. Author/review the actual org ODCS contract, preserving the prior priority-2
   boundary. Refresh saved exports with approved credentials and select the exact
   reviewed Flow version.
2. In the producer run `scripts.pipeline.export_projection_inputs` with the saved
   exports, authored contract, org, exact version and source commit. Use a fresh
   output. The exporter retains native source evidence and writes a verified
   manifest last; its multiple writes are not transactional.
3. Review the handoff and update the packaged contract/Flow/source artifacts and
   manifest paths/hashes together. Confirm explicit relationship and physical
   history bindings; changing just a runtime hash does not switch the compiler's
   installed input set. Regenerate SQL, suites and diagram artifacts, rebuild the
   release and commit actual DVC lock outputs.
4. Acquire native rollup metadata before replacing the existing rollup builders.
   Add independent acceptance cases for the actual definitions and null semantics.
5. Run the existing offline gates, then verify settled events and independently
   observed AFTER values against the actual Athena/Glue environment. Inspect
   native GX results and reports. Offline success does not establish live acceptance.

No live query, deployment, source refresh, publication or validation run is added
to the DVC cache. Poe remains the operational entry point and DVC retains its four
release producers.


## Expected-value consumer evidence

The consumer uses producer revision `1eedb2abcf5cac6471fb6cc45e5a40c007982854`.
Verified metadata is cached as immutable serialized content; public reads return
fresh models. Per-field `__assigned` and `__deterministic` columns
retain native evidence. Missing scope or computation is an incomplete result.
Native equality checks run only where identity/grain and computation are valid.
The native pair denominator excludes both-NULL values; their count remains in
`missing_count`. One-sided NULLs fail. Runtime findings retain `validation_record_id`.

`flow_account_comparison(..., required={...}, must_be_null={...})` accepts independent
source-bound presence predicates. Bind the corresponding field names in
`flow_account_suite(required_fields=(...), must_be_null_fields=(...))`. No new org
presence policy is invented. Unknown authored predicates remain NULL and fail
completeness. Predicates depending on an unrelated observation are rejected by Ibis.

Native suite metadata includes the derived ODCS comparison contract. Original
objects retain authored metadata; `AccountBefore` and `AccountExpected` declare
explicit roles with stable property pointers. Source definitions identify verified
artifact content by SHA256 URN and JSON pointer; resolve that URN through the
manifest's artifact hashes. These provenance links do not execute joins.

`native_rollup_comparison(parent, child, observed, request, source_field=..., inputs=...)`
accepts a verified native handoff explicitly; load it with the existing artifact loader. The validated request
requires an explicit empty/all-null policy. COUNT, SUM, MIN and MAX have synthetic
handoff execution coverage. Missing selections fail; the existing 19 workbook
rollups stay in place until native org definitions and aggregate policy are reviewed.

The renderer keeps shared CTEs inside a SELECT-first input relation instead of
repeating their bodies. Native GX conditions inspect assignment non-nullness
without treating assigned=false as exclusion. Compact runtime SQL retains lineage
comments and is checked against Athena's UTF-8 query limit before asset creation.
The source-parent uniqueness check runs before rollup aggregation; invalid source
or observed join keys block rollup equality without hiding the structural findings.

The release smoke installer bypasses uv's wheel cache. A repeated build with the
same package version had installed old bytes despite the rebuilt bundle containing
the new wheel. Native bundle smoke now tests the supplied artifact directly.
