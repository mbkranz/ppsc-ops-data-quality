# Standalone DDL migration: implementation and review

Implemented October 27, 2026 from the accepted
[design review and migration plan](athena-ddl-standalone-design-review.md).
No deployment, publication or live Athena/Glue validation was performed.

## Result

Athena DDL is the sole authored input-type authority. `core.schemas.schema_from_ddl`
returns native Ibis schemas and rejects unsupported declarations/type arguments.
Account/Contact/Survey profiles and history/catalog bindings live with the domain.
Core imports no Salesforce workflow or application profiles.

The selected QA2 Flow now executes through reviewed local Ibis builders in
`account_to_survey_results/flow.py`. Native metadata is detached source evidence,
not executable instructions. Expected values, assignment and determinism stay
separate; assigned NULLs and unchanged BEFORE values retain their meanings.
Existing rollups remain until actual native definitions and policies are reviewed.

ODCS loaders/contracts, compiler-dependent adapters and the vendored compiler
wheel were removed. The runtime dependency lock contains no Salesforce,
`ppsc-metadata` or ODCS dependency. The domain owns its configuration/validation
workflow; runtime retains generic GX preparation, execution and reporting.

An `ops-definitions/v2` receipt hashes DDL, executable helpers/builders, selection,
lineage and native source evidence. DDL parsing consumes the verified immutable
snapshot rather than reopening an unhashed schema. Run preparation reverifies
installed bytes. Definition capture writes a fresh candidate for explicit review.
LF Git attributes preserve the byte hashes across supported checkouts.

`poe author-salesforce` is optional offline authoring in a separate environment.
It pins the producer to `a534c63353680e41d12e3b55997a125ba703c675` from the verified
`mbkranz/ppsc-salesforce` remote. It produces candidate DDL, detached evidence and
named reference queries, with the complete normalized request, inspection date,
lookup bindings, producer revision/version and code/input/output hashes. It does
not generate or execute Python from metadata. Authored SQL execution stays deferred.

SQL examples and native Ibis diagrams were regenerated. Python GX suite builders
remain authoritative and registered suites are still serialized before validation.
The four root DVC release producers remain unchanged in number; their obsolete
vendor dependencies were removed.

## Standards: independent reviewer 1

Two P2 findings were reported and fixed:

- The DDL reader accepted malformed parameters such as `INT(7)`, `BOOLEAN(3)`
  and `VARCHAR(0)`. It now checks supported parameter shapes/ranges before Ibis
  conversion. Regression cases also verify retained DECIMAL precision, string
  length and timestamp precision.
- The authoring receipt omitted the request/date/lookup mapping and exact producer
  identity. It now embeds the validated request and hashes `request.json`, records
  its invocation directory, and verifies the installed producer's exact Git commit.

The reviewer rechecked both fixes and found no material new issue. The suggested
producer-remote and line-ending portability improvements were also implemented.
A final Gemini 4 Argon review against the PPSC agent design reference verified
that structured public output models (`MetadataInputs`, `CaptureReceipt` and
`AuthoringReceipt`) enforce explicit SHA256/literal/count field constraints and
refreshed the definition manifest receipt.

## Spec: independent reviewer 2

The reviewer independently identified the same two P2 issues, rechecked their
fixes and verified all generated authoring artifact hashes. No P1 semantic
regression or material follow-up finding remained.

The semantic review compared a deterministic 75-event batch against the query
implementation from the pinned producer: NULL inputs, missing Accounts,
incomplete events, consent variants, ordered ties and unsorted ambiguity. Both
retained all 75 events and agreed on all 57 expected/assigned/determinism outputs.
That independent run used the pinned query file with sibling helper imports.

A supplementary run repeated the comparison against the complete immutable
producer installed in an isolated environment. It also retained 75 events with
zero differing columns. Producer parity supplements the independently authored
expected-result fixtures in normal CI; it does not replace them.

## Executed verification

- Focused DDL/integrity/SQL regressions passed: 45 tests, including all 24 DDL cases.
- Query compilation and all 56 synthetic native GX expectations passed.
- The standalone wheel built and passed compilation, suite serialization and the
  complete synthetic-report checks with no `salesforce`, `ppsc_metadata` or ODCS
  installed. Its actual wheel origin and loaded package location were verified.
- The optional producer was fetched from the declared remote at the exact pinned
  revision, installed in a separate environment, and successfully emitted a
  candidate field DDL plus all six named Flow reference queries and lineage.
- Native Ibis diagrams and checked-in SQL examples were regenerated.
- `uv run poe check` passed lint/format checks and 230 tests. One release
  integration test skipped because the pinned producer tools are unavailable.
- `uv run poe check-queries`, `uv run poe check-synthetic` and
  `uv run poe check-standalone` passed. Updated local documentation links resolve.

Ignored executed evidence is retained under `build/checks/`: standalone receipts,
`authoring-produced/manifest.json`, and `review-parity/installed-result.json`.
These contain only synthetic records and definition evidence.

The release-integration test now requires the prepared local producer and forces
its local backend. With host uv 0.10.10 rather than the required 0.12.23, it skips
explicitly instead of falling through to a GitHub build from an uncommitted test
fixture. No release acceptance is claimed in this environment. `dvc.lock` remains
the prior release's real outputs; reproduce the four stages with the pinned tools
before a release commit. No new lock output hashes were fabricated.

Actual catalog types, deployed Flow activation, event eligibility/settlement and
live Athena/Glue behavior still require separate acceptance with verified local
configuration.
