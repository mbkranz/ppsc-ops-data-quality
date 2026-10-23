# Build and deployment implementation review

## Starting point and scope

Started from draft PR #6, `feat/ibis-query-validation-runtime`, at
`ce602d03d1df950ba2f9c3b80b341983a74ffb4b`. Changes are on
`codex/minimal-build-deploy`, targeting the PR #6 branch and preserving its work.
No merge, release publication, AWS activation or live Athena validation was
performed. The attached PPSC design-contract reference guided Python contracts.

## Implementation

- `dvc.yaml`, real `dvc.lock`, `.dvc/`, `pyproject.toml`, `uv.lock` and
  `.python-version`: requirements/dependency-wheel/application-wheel/bundle graph
  only. Exclusive outputs, locked tools and direct producers replace orchestration.
- `scripts/package_release.py` and `scripts/glue_wheels.py`: deterministic archive
  producer, validated complete runtime closure and existing-parent-safe assembly.
  No build revision input, copied Git driver or duplicate inventory manifest.
- Removed `release_manifest_uri` from the Glue model/parser/report metadata and
  deployment contracts together. Runtime config hashes and report completion
  manifests remain. Query/GX/row-condition/rollup/report behavior is unchanged.
- `scripts/release_artifact.py`, `scripts/plan_deployment.py`: exact clean Git
  revision, selected final DVC identity, embedded wheel metadata and both native
  SDK payloads. The planner resolves the fixed output instead of an arbitrary ZIP
  directory; its receipt keeps revision/lock/runtime and actual artifact hashes.
- `scripts/apply_deployment.py`: injected SDK session, validated artifact/receipt
  models, account recheck, local mutation checks, conditional immutable uploads
  of both files before explicit create/update and retained partial outcomes.
- Poe, CI/release workflow, AGENTS and runbooks: inherited environment, full-graph
  publication gate, final-only deployment retrieval, separate uncached run/status/
  catalog operations and same-byte promotion/rollback.

## Executed verification

Supported producer: Linux x86_64, Python 3.11.17, uv 0.12.23, pip 25.3,
Hatchling 1.27.0 and its locked dependencies.

`uv run --locked poe check` passes **108 tests**, lint and formatting. Required
`check-queries` and `check-synthetic` pass. The installed smoke performs index-free
installation, dependency checking, isolated import/CLI checks, compiled SQL and
native GX validation: 28 Flow plus 25 rollup expectations, 53 expectation rows and
two validation summaries, suites, native results, Data Docs and completion evidence.

Actual `dvc repro dvc.yaml`, unchanged second reproduction and local freshness
pass. Native integration compares independently forced wheel builds, checks
publication-only edits, makes a real package-version/lock edit while retaining
unchanged dependency downloads, deletes just the ZIP and forces identical
reassembly, restores an exact fixture commit from an empty local cache, and then
restores only `bundle` in a separate checkout. Corrupt remote objects, stale source,
wrong revision and changed final bytes fail. Local tests use real generated
artifacts and synthetic domain inputs, never invented DVC hashes.

SDK tests verify wrong account/role, changed bytes, immutable conflicts and failed
uploads cannot activate the job, both artifacts precede activation, and identical
update/publication is unchanged. Glue argument/config verification tests preserve
release revision and configuration SHA without a release manifest. A focused
19-test deployment rerun also passes after receipt typing changes.

## Review informed by NIOCCS and Salesforce

NIOCCS' deployment path supplied conditional S3 publication, expected owner,
byte verification and all-artifacts-before-jobs behavior. That concrete pattern
replaces Ops' previous overwriting S3 CLI copies; explicit create/update and
independent live run/catalog operations remain.

Salesforce's explicit refresh and stage-local freshness clarified that retrieval
alone cannot validate a new release. Publication checks the entire release graph
once; deployment validates the accepted final archive against the selected lock
without requiring its absent intermediates. Live validation is never a DVC stage.

Cross-repository integration found Poe's implicit environment selection could
prepare another environment inside the graph. Ops now uses the simple executor,
as NIOCCS already did. Tests explicitly retain the prepared producer environment.
Hatchling normalizes equivalent Python-constraint order, so metadata checks use
semantic `SpecifierSet` equality. Repeated installed smoke clears only its own
synthetic scratch directories; actual validation continues to preserve fresh run
IDs/evidence. No shared framework, replacement manifest or registry was introduced.

## Pending activation and rollback

The canonical DVC S3 store/credentials/retention, account/role/prefix/job bindings,
versioned runtime YAML and exact published GitHub release remain operator inputs.
Configure the protected publication workflow/OIDC environment and restrict
release-artifact status writers and mutable tags. Temporary local remote evidence
does not establish S3 availability.

Glue-compatible container and managed Glue execution remain unverified. Development
acceptance must confirm actual source types, history/deletion/temporal/timezone
semantics, exact deployed hashes, quality/error exit behavior, full Data Docs and
report completion markers, and both Athena catalog DDL results. Promote identical
release bytes after that gate. Rollback retrieves an earlier release and its Git
job template; it never rebuilds or deletes existing report evidence.

Final portability review adds explicit Python bytecode/build-metadata ignores to
DVC inputs and declares `.dvcignore` as a wheel-producer dependency. A native
integration check confirms host-specific bytecode does not stale source identity.
