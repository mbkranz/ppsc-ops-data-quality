# Canonical expected/observed queries and dotted GX labels

PR #14 follow-up to `fa87c659faafa1f37c83e7ead8372b737bacb693`.

## Contract and implementation

Expected Flow outputs and observed Account snapshots expose canonical `Id` and field
names. Assignment/determinism and lookup diagnostics remain separate evidence. The
expected builder takes BEFORE/execution inputs without an AFTER argument. It only
renames the native compiler's final projection, preserving its expressions, CTE sequence,
graph and provenance. No Salesforce dependency change is needed.

Rollup aggregation finishes before the independent observation join. The expected
relation retains zero-child results and source-parent uniqueness evidence. The full
outer comparison retains unmatched observations and duplicate occurrences without
observation-row numbering or grouping by observed field values. An observed-only row
has absent expected values (NULL), rather than an artificial aggregate over a missing
source row; existing missing-identity checks still fail it. The duplicate/missing-parent
regression explicitly includes this observed-only case.

The GX comparison projection alone introduces literal dotted column labels. Native
column-pair checks consume `expected.<field>` / `observed.<field>`; canonical input
relations are not mutated. Account identity labels become `expected.Id` / `observed.Id`;
check IDs remain stable. Generic comparisons use `expected.key.<name>` and
`observed.key.<name>` to distinguish keys from values.

No modules, packages, custom metrics, registries or execution layers were added. Existing
composition operations still bind temporal roles and hand final native SELECTs to the
shared runtime. Direct comparison callers supply correctly scoped inputs.

## Review findings and resolutions

- The first extraction added a redundant canonical SELECT wrapper and increased Flow SQL
  to 260,992 UTF-8 bytes. Renaming the native final projection directly reduced it to
  251,644 bytes (previous PR version: 249,381). Both the base-query guard and full GX
  statement guard remain enabled. No live Athena size/performance acceptance is implied.
- Stable identity-check IDs were initially affected by renamed columns. An explicit
  two-entry mapping preserves their existing IDs; regression checks cover both suites.
- Moving rollup aggregation must not collapse identical observations. The existing
  independent duplicate/source-parent tests execute the new shape and preserve exact
  comparison multiplicity; observation identities no longer enter the aggregate.
- Reading SQLGlot projection metadata initializes empty metadata on nodes. The new
  no-mutation regression caught this; the comparison now copies the expected tree
  before reading lineage and reuses that copy in its CTE.
- Optional required/must-be-null columns supplied on canonical expected state also
  receive dotted labels; the expected-only boundary regression covers both roles.
- Dotted aliases must be quoted as single output identifiers. Real SQLite GX validation
  verifies equal pairs, both-NULL exclusion, one-sided NULL failures, changed values and
  duplicate-key failures through the unchanged runtime.
- A separate expected-only test removes all AFTER records and confirms expected output
  remains identical while the joined comparison reports the missing observation. It also
  checks canonical names, copied lineage and no mutation of the expected SQLGlot input.

All 54 base suite checks (29 Flow, 25 rollup) were compared with the committed predecessor:
IDs, expectation types and every serialized kwarg match after only the approved column
renames. A second comparison enabled required/must-be-null policies and both optional
row-count checks: all 58 resulting check definitions also matched after label mapping.
The normal synthetic configuration still has 56 checks.

## Verification

The final product source passed the sequential Linux x86_64 gate on Python 3.11.17,
uv 0.12.23 and pip 25.3 with the committed dependency lock:

| Check | Result |
| --- | --- |
| `poe check` | Lint/format passed; 186 tests passed, including real release reproducibility/retrieval integration |
| `poe check-queries` | Passed |
| `poe check-synthetic` | 56/56 native expectations passed |
| `poe render-queries` | Regenerated SQL, lineage and native suite artifacts |
| `poe build-release --backend local` | Complete; fresh installed smoke passed, including compilation and 56/56 expectations |
| `dvc status dvc.yaml --quiet` | Exit 0 after final build; lock matches actual outputs |
| Wheel inspection | All nine application Python modules match final source byte-for-byte; bundled Salesforce wheel unchanged |
| Additional observed-only fixture check | Passed after extending the existing rollup fixture during the full run; production source was unchanged |

The only full-suite warnings were Ibis's DuckDB `fetch_arrow_table` deprecation.
Intermediate superseded runs are not claimed as acceptance results. The no-mutation
failure was fixed before the final full gate. Verification uses synthetic/offline inputs;
no live Athena, Salesforce, Glue deployment or S3 release publication is claimed.

Final local release SHA256 identities (artifacts remain outside Git):


- `ppsc_ops_data_quality-0.1.0-py3-none-any.whl`: `ba71348d53f30aa6c255dcb84d59943efe0b4ba97184c5750fc72726f8b7f2bf` (56,544 bytes).

- `dependencies.gluewheels.zip`: `339c7e324657ba90b0c9f170c83929540f30da96392851c2d7e619a4b7d21cd2` (180,085,955 bytes).
