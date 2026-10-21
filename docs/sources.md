# Source evidence and authoring status

Reviewed October 20, 2026. Source references below identify authoring evidence;
validation runs the committed Python modules and does not retrieve these sources.

## Pilot contract

The initial Account and AccountContactRelation (ACR) suites implement the authored
pilot contract in the repository initiation plan:

- Each selected state row has a non-null, nonblank identifier; identifiers are
  unique within that object's selected state.
- Each selected ACR row has an Account reference that resolves to exactly one
  Account row in the corresponding selected state. Missing references, missing
  parents, and duplicate parents remain distinguishable.
- Both sides use the same effective-date or current-state selection. The proposed
  half-open effective interval convention must be confirmed against the lake.

These are explicit pilot expectations. They are not represented as checks copied
from an existing job or automatically inferred from a complete Salesforce graph.
The cached [AccountContactRelation API reference][acr-reference] confirms the
meaning of `AccountId`, but it is a platform reference, not the selected org's
field export or proof of lake-wide referential integrity.

## Reviewed sources

| Source | Pinned revision and purpose |
| --- | --- |
| [APMP data lake project][lake-project] | `ppsc-salesforce` at `e33ffbce97383ead61f4d16f16cc816723e7b907`. Contains the overview and its catalog; the adjacent Python, parameter, and DVC files are empty. It does not supply verified live bindings. |
| [Salesforce lineage guide][lineage-guide] | Same revision. Defines saved graph artifacts, provenance, associations, and interpretation limits. Graph integrity does not establish complete dependencies or executable rule equivalence. |
| [Source-data validation Glue script][source-job] | `ppsc-calculations` at `4c4fd6131f6535c94235ad877dd9d734e57bc4c2`. Provides the concrete candidate below. This source repository requires access. |
| [String preparation helper][trim-helper] | Same calculations revision, `trim_strings`, lines 162–176. Trims string columns before the source checks. |
| [Pinned native Survey Completion Flow][flow-fixture] and [fixture notes][fixture-notes] | Same Salesforce revision. Retained native QA2 Flow metadata, rather than participant records. |
| [Matching field catalog fixture][catalog-fixture] | Same Salesforce revision. Supplies the Survey Result → Contact → Account relationship bridge used by that Flow. |
| [Direct lineage fixture test][lineage-test] | Same Salesforce revision, lines 610–681. Source assertions cover the pinned Flow's graph construction and relationship resolution. Reading this test is not a new test execution or inspection of the saved graph bundle. |

The APMP overview's Git blob is
`882dcc8048dcbbbb0c739f14e013b2dd2452d171`. The source-data validation script's
Git blob is `30f2d8aac6c54db8d00b55b33df64239534522cc`. No source records, notebook
outputs, actual connection settings, or deployment resource identifiers are
copied into this repository.

## Candidate from the operational job

**Candidate:** `account.ubr_income_requires_basics_timestamp`.

**Rule:** an Account with a present `UBRINCOME__pc` value should have a present
`Basics_Date_Time__c` value. A finding has Account-row grain.

The [operational implementation][source-rule] establishes this predicate:

1. Read the newest Account JSON file in the configured source prefix. The job
   selects the weekly full-pull prefix on Monday and its ordinary prefix on other
   days. The actual parameter values and source-file completeness are unresolved.
2. Trim string columns. Treat null and the resulting empty string as missing.
3. Flag rows where the trigger is present and the required timestamp is missing.
   The check itself adds no test-account, deletion, or withdrawal filter.
4. Log findings for this rule. It is a monitoring check in that job; it does not
   independently set the job's failure flag.

The initial lake pilot selects complete state from history. That population is
different from an unspecified latest source file. Moving the predicate into a
blocking GX suite would also change its operational treatment. Both choices need
an explicit contract before this candidate joins the runner's selected suites.
The candidate is currently excluded; metadata saying “candidate” is not an
execution gate.

## What native metadata contributes

The [fixture notes][fixture-notes] identify active QA2 Flow version
`301SL00000dpJqKYAU`, `Survey_Result_Survey_Completion_Updates`, API 61.0, from an
export with SHA-256
`95d55a7510a58a729ccf6e38404b47051ec24a92f657280630f2a213edf44a76`.
“Active” describes the saved QA2 fixture, not a verified current production Flow.

The inspected native JSON contains these evidence points:

| Pointer | Evidence |
| --- | --- |
| `/Metadata/start` | Survey Result create/update trigger, completion and automation-exemption conditions, and an `AsyncAfterCommit` path to `Survey_Index`. |
| `/Metadata/decisions/3/rules/4` | Survey index `2001` or `2002` routes to `updateAccount2001`. |
| `/Metadata/recordUpdates/7/filters/0` | The target Account `Id` equals `$Record.Participant__r.AccountId`. |
| `/Metadata/recordUpdates/7/inputAssignments/0` | Assigns `Basics_Date_Time__c` from `$Record.Completion_Status_Timestamp__c`. |
| Catalog `/fields/29` and `/fields/21` | `Survey_Result__c.Participant__c` references Contact; `Contact.AccountId` references Account. |
| Catalog `/fields/1` | Identifies the target `Account.Basics_Date_Time__c` field. |

This explains one source of the timestamp required by the operational check and
where to investigate a finding: source UBR calculation inputs, the relevant
survey-completion event, its participant/account relationship, automation
exemption, and asynchronous execution timing. The operational job supplies the
requirement; the Flow supplies provenance and investigation context.

The assignment does not establish that a current Account timestamp must equal
the maximum or latest timestamp across Survey Result records. The fixture does
not establish production coverage, deployed lake columns/types, or the complete
definition of `UBRINCOME__pc`.

## Graph evidence still to inspect

At the pinned Salesforce revision, [the DVC lock][dvc-lock] records:

| Artifact directory | DVC content pointer |
| --- | --- |
| `build/lineage/qa2` | `4f968963c48414b46a81c2c98cb9ca6f.dir` |
| `build/network/qa2` | `0175336275b38249c2b750c22a1343c2.dir` |

These are inspected lockfile pointers. The saved artifact bytes were not
retrieved or inspected for this implementation. Use the lineage guide to restore
the selected bundle from its approved cache, then examine the relevant Flow
nodes, incident edges, expressions, and native source pointers. Follow
`refers_to` associations deliberately; they are not themselves data propagation.

Confirm the Flow version and native pointers above against that bundle. Retain
the actual graph node/edge IDs and manifest source hashes after inspection.
Do not copy illustrative `athena_sql` into an expectation as if execution
equivalence had been verified.

## Remaining inputs and milestone status

The combined-evidence milestone is **pending**. A real operational candidate and
its native metadata explanation are identified, but the candidate is not selected
for execution and the saved graph subset has not been inspected.

Completion requires:

- Confirm the candidate's applicability to the complete lake-state population and
  whether findings should remain monitoring-only or fail this validation run.
- Select the intended Salesforce org/revision and inspect its relevant graph and
  native metadata. The QA2 fixture is a bounded authoring example.
- Verify the actual Account columns and types for the trigger and timestamp;
  preserve null semantics without casting a physical schema mismatch away.
- Implement the accepted rule in the Account module with passing/failing fixtures,
  explicit missing-value behavior, and the reviewed source references.
- Supply live Athena bindings and credential access, confirm temporal/deletion
  conventions, and use a known completed delivery for live acceptance.

[lake-project]: https://github.com/mbkranz/ppsc-salesforce/tree/e33ffbce97383ead61f4d16f16cc816723e7b907/projects/apmp-data-lake
[lineage-guide]: https://github.com/mbkranz/ppsc-salesforce/blob/e33ffbce97383ead61f4d16f16cc816723e7b907/docs/salesforce/lineage.md
[acr-reference]: https://github.com/mbkranz/ppsc-salesforce/blob/e33ffbce97383ead61f4d16f16cc816723e7b907/.agents/skills/platform-data-and-tooling-api-context-get/assets/enterprise_api/AccountContactRelation.json
[source-job]: https://github.com/mbkranz/ppsc-calculations/blob/4c4fd6131f6535c94235ad877dd9d734e57bc4c2/glue/scripts/calculations-validate-source-data.py
[source-rule]: https://github.com/mbkranz/ppsc-calculations/blob/4c4fd6131f6535c94235ad877dd9d734e57bc4c2/glue/scripts/calculations-validate-source-data.py#L105-L164
[trim-helper]: https://github.com/mbkranz/ppsc-calculations/blob/4c4fd6131f6535c94235ad877dd9d734e57bc4c2/src/ppsc_calculations/calculations_utils.py#L162-L176
[flow-fixture]: https://github.com/mbkranz/ppsc-salesforce/blob/e33ffbce97383ead61f4d16f16cc816723e7b907/tests/fixtures/flows/survey_completion.json
[fixture-notes]: https://github.com/mbkranz/ppsc-salesforce/blob/e33ffbce97383ead61f4d16f16cc816723e7b907/tests/fixtures/flows/README.md
[catalog-fixture]: https://github.com/mbkranz/ppsc-salesforce/blob/e33ffbce97383ead61f4d16f16cc816723e7b907/tests/fixtures/flows/survey_catalog.json
[lineage-test]: https://github.com/mbkranz/ppsc-salesforce/blob/e33ffbce97383ead61f4d16f16cc816723e7b907/tests/test_lineage_build.py#L610-L681
[dvc-lock]: https://github.com/mbkranz/ppsc-salesforce/blob/e33ffbce97383ead61f4d16f16cc816723e7b907/dvc.lock
