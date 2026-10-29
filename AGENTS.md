# Repository guidelines

- Keep one obvious implementation of each query or rule.
- Use native SQLGlot SELECTs, native GX suite builders and an explicit runner. Keep Ibis only for retained authored relational/rollup expressions.
- Keep schemas, lineage, query construction, data access and execution separate.
- Preserve duplicate matches, missing parents, assigned NULLs and old unchanged versions.
- Treat schema profiles as validation inputs; confirm deployed catalog types separately.
- Python suite builders are authoritative. Serialize each registered runtime suite before validation.
- Authored SQL execution requires the explicit versioned sidecar contract in docs/query-design.md; generated SQL is never implicitly executable.
- Use Poe for operational entry points and root DVC for the four release producers only.
- Never cache live Athena/GX validation, deployment, run submission or report publication.
- Prepare locked release tools once; DVC producers call real commands without nested environment setup.
- Finalize dvc.lock from real outputs before committing. Publication retrieves without reproducing; deployment pulls only bundle.
- Keep credentials, live configuration and record-level outputs out of version control.
- Use synthetic fixtures in CI. Local checks do not establish live Athena/Glue acceptance.
- Run `uv run poe check`, `uv run poe check-queries` and `uv run poe check-synthetic` before proposing changes.

- For Python module design, substantial refactoring and architecture review, use $design-python-contracts: [installed PPSC agent design reference](.agents/skills/design-python-contracts/SKILL.md). Keep validated structured public inputs/results, explicit functions and visible workflows, and native expressions and frames. Apply it within this repository's constraints and compatibility requirements.
- Keep shared runtime and I/O domain-independent. Supply projection lineage explicitly at orchestration.
- Use YAML for runtime/environment settings; use data-migration-dev for local AWS operations (explicit overrides allowed).

- Prefer deletion and consolidation; try an existing function or direct call before adding abstractions.
- Add no packages, registries or framework layers without a demonstrated second consumer.
- Keep SQL/Ibis transformations independent of GX; suite builders consume prepared columns and workflows compose them.
- Generalize only from concrete call sites, their differing needs and precisely shared behavior.
- Assess module/line/dependency/indirection changes and the simplest viable alternative; preserve diagnostics and semantics.
