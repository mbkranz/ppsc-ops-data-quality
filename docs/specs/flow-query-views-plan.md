# Run-scoped expected Flow views

## Problem and decision

The native Flow comparison currently submits about 251,644 UTF-8 bytes before GX
adds metric SQL. Athena limits each statement to 262,144 bytes. Persist the existing
canonical expected-state SELECT as an optional run-scoped Athena view, and reference
its explicit outputs from the existing comparison. Keep the native compiler and GX
suite builders unchanged. Ordinary inline compilation remains available.

AWS recommends views or CTAS to split long statements:
https://repost.aws/knowledge-center/athena-query-string-length
Views are evaluated on read, not materialized:
https://docs.aws.amazon.com/athena/latest/ug/views.html

## Interfaces and ownership

- Ops owns view names, SQLGlot CREATE/DROP statements, snapshot binding and execution.
- An optional `flow_view` YAML setting declares the target database, safe name prefix
  and bounded DDL timeout. The workflow uses its configured Athena catalog and a UUID
  suffix. No shared view is replaced; independent runs cannot overwrite one another.
- Compile/extract the existing `Expected_Account` CTE through its explicit named
  boundary. Return native SELECTs: the full expected definition and the comparison
  with an explicit view projection. No generic DAG planner, registry or new dependency.
- The view request/receipt use Pydantic. SQL trees stay native. Effectful operations
  receive the Athena client and execution options explicitly.
- Bind table snapshots before extraction. Snapshot IDs belong on underlying reads,
  never on the view reference. Keep event, BEFORE/execution/AFTER and eligibility
  literals in the appropriate definitions. Do not rejoin context by nonunique Id.
- The query-local `flow_row_id` remains inside the single expected definition and is
  not used as a key across separately evaluated views. Preserve every canonical output,
  assignment/determinism flag and lookup diagnostic.
- Correct current output-column lineage through canonical and GX renames; retain
  native output names separately as source provenance.

## Visible workflow

1. Validate the native captures, reviewed DDL, temporal configuration and physical
   catalog using existing gates. Prepare snapshot-bound SELECTs and size-check both
   CREATE VIEW and comparison before any DDL.
2. Create the fresh run directory and save exact DDL/lineage. Execute CREATE VIEW and
   wait for success with an explicit timeout and query ID evidence.
3. Register the existing native suites over the small comparison SELECT. Keep base
   physical source provenance, view dependency definitions and statement-size evidence
   in reports. Include dependency files in the existing query-artifact publication.
4. Drop the created view after validation/reporting, including exceptional paths.
   Save cleanup evidence. Preserve the original error if cleanup also fails. Failed
   or timed-out DDL must expose its query ID; no successful deployment is invented.

## Verification and review

- Execute original and view-based SELECTs on independent synthetic DuckDB history;
  compare multisets including duplicate parents/events/observations, missing rows,
  assigned NULLs and unknown eligibility. Assert input ASTs and native provenance
  remain unchanged and output-reference metadata resolves to current output names.
- Exercise CREATE success/failure/timeout, unique run names, physical snapshot
  placement, size rejection before DDL, cleanup and error preservation using fakes.
- Run native GX against a small real SQL view to verify checks read the view and
  retain short submitted statements. Retain full Flow fixture parity separately.
- Extend credential-free compile/render examples with CREATE VIEW and the short
  comparison, reporting their actual sizes. Preserve the existing inline examples.
- Run `poe check`, `poe check-queries`, `poe check-synthetic`, the real pinned release
  producer and installed smoke. Regenerate derived examples and dvc.lock from outputs.
- Review against AGENTS.md and `.agents/skills/design-python-contracts/SKILL.md`;
  record resolved findings, complexity changes and acceptance limits.

## Acceptance limits

No live catalog creation, deployment or validation is part of offline implementation.
Actual Athena CREATE VIEW with selected native captures, snapshot clauses, output
types and GX execution remains a live acceptance gate. View expansion can still be
expensive; CTAS/materialization requires measured reuse/performance evidence and is
deferred. Additional view stages are warranted only when this CREATE itself no longer
fits. Existing input/source governance gates remain enforced.
