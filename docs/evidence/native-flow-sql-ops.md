# Native Flow SQL Ops implementation evidence

Prepared October 28, 2026. Source base:
`035ae5fedf4f63393f8e92e04336ec22ea4725ea` on `codex/refactor-handoff`.
See the [plan and review](../specs/minimal-implementation-plan.md).

This records the initial implementation at `fa87c659faafa1f37c83e7ead8372b737bacb693`.
The subsequent canonical-query simplification has its own
[verification and release evidence](canonical-query-boundary.md).

## Verified dependency and application boundary

- Salesforce source `4ce491c3266e052bf1e1f6a70e8f7d2aed86f9f1`, unchanged wheel version 0.1.1.
- Wheel SHA256 `c625b6f4273241ee29bde7b4cdfbcebc9ddf4ab5b0e2caf1840727de4fb67c9b`;
  source receipt and immutable vendored path are committed.
- Application Python modules reduced from 40 to 9, including two initializers and two
  hosting entry points. The five application modules remain ordinary functions/models
  and native SQLGlot/GX objects. Reports and partial-failure diagnostics are retained.
- No runtime package was added. DuckDB was constrained from 2.0.0 to 1.5.6 after an actual
  illegal-instruction failure loading the Linux x86_64 2.0 wheel in the measured producer.
  Python, Ibis, GX and SQLGlot remain pinned to their existing declared versions.

## Verification progression

The macOS development run passed 177 tests and 18 subtests; two real-DVC handoff cases
failed under the macOS filesystem/process sandbox. The release integration test was
excluded there because it requires the pinned Linux producer. Those results are not
reported as a passing full gate. The final acceptance run uses Linux instead.

A disposable local Docker container uses Linux x86_64, glibc 2.36, Python 3.11.17,
uv 0.12.23 and pip 25.3. Dependencies are installed from the committed lock. No AWS
credentials, source record data or live configuration are needed for these checks.

- Native consumer adversarial checks: duplicate trigger/Contact/BEFORE/AFTER occurrences,
  missing relationships/observations, old unchanged values, unknown eligibility,
  assigned NULL versus unassigned values, independent AFTER mutations and metadata-driven
  behavior. Faithful/simplified comparison multisets and original graph/node-order evidence
  match. Existing native branch/value assertions are ported rather than replaced by
  snapshots of implementation output.
- Typed authored SQL checks cover suite identity, exact parameter/alias correspondence,
  quoted literal content, exact decimal and timezone policy, unsupported statements,
  undeclared physical relations and recursive CTE rejection.
- Input checks cover native scale zero, loss/missing evidence, actual compound component
  parent identity, incomplete captures and exclusive DDL export with no execution.
- Real SQLite GX QueryAsset validation measures complete submitted metric statements;
  an execution-engine listener rejects over-limit UTF-8 statements before submission.
  This is offline framework evidence, not a measurement of live Athena traffic.
- Final illustrative Athena Flow query is 249,381 UTF-8 bytes excluding the generated
  header and terminal semicolon; it exposes 19 expected fields plus assignment,
  determinism, identity, scope, observation and native lookup evidence. Configured names
  and versions can change size, so both base registration and full-statement execution
  checks remain enforced. No assumption that a CTE executes once is made.
- The four real root DVC producers generated requirements, Linux dependency wheels,
  the application wheel and the Glue bundle. Fresh installed smoke passed index-free
  installation of all 59 distributions, dependency compatibility, installed imports,
  metadata receipt, CLI invalid-config handling, query compilation and 56/56 synthetic
  expectations with native report evidence.

## Final acceptance results

| Check | Result |
| --- | --- |
| Linux `poe check` (lint, format and full test suite) | 181 passed; includes real DVC handoff and release reproducibility integration |
| Linux follow-up consumer review tests | 42 passed: native integration, input definitions and authored SQL |
| Linux final authored SQL regression run | 22 passed after the final 38-digit decimal boundary correction |
| Linux `poe check-queries` / `poe check-synthetic` | Compile passed; 56/56 expectations passed |
| Final `poe build-release --backend local` | Complete; fresh installed smoke passed, including 56/56 expectations |
| `dvc status dvc.yaml --quiet` | Exit 0 after final build; lock matches actual outputs |
| Final Ruff / formatting / `git diff --check` | Passed; 67 Python files formatted |
| Installed artifact inspection | All nine application Python files match final source byte-for-byte; no retired Python modules; bundled Salesforce wheel matches vendored bytes |

The full gate preceded the last scoped review corrections; the follow-up checks and final
installed release smoke exercise those changes. Counts above are separate runs, not an
inflated unique-test total. The only full-suite warnings were Ibis's deprecated DuckDB
`fetch_arrow_table` use.

Final local release SHA256 identities (release artifacts remain outside Git):

- Application wheel: `a092bea42d95d491ec65e2363f7f9c64a5b13ec56d7f45f26737c52dba685a57`
  (55,946 bytes).
- Glue wheel bundle: `988e33303f52de3f8fc70d02468f9b14a5f5482de738bf3a9d6d81614e73c080`
  (180,085,356 bytes).

## Independent consumer review

A separate agent performed a read-only review after the implementation review, focusing
on the plan, input contract, native Flow binding, workflow ordering, suite/runtime handoff
and saved verification evidence. It found no blocking issues and confirmed the logs
support the reported test/release results. It made no changes or additional acceptance
claims. Its remaining limits are the live prerequisites listed below.

## Acceptance limits

Bundled lake DDL remains a provisional offline profile. Actual native field/component
captures, independently reviewed lake DDL, trigger eligibility and settled observations
must be supplied before live execution. Live mode rejects incomplete/provisional inputs
before client construction. Native source types are never reconstructed from lake types.

No live Salesforce, Athena, Glue, S3 publication or deployment acceptance is claimed.
The release artifacts are built locally; canonical release publication remains a separate
explicit operation. SQL and lineage examples contain synthetic bindings only. Run-level
queries, bound parameters, Data Docs, Parquet results and credentials are excluded from Git.
