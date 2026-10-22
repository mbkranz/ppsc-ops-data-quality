# Repository guidelines

- Keep one obvious implementation of each query or rule.
- Use composable Ibis expressions, native GX suite builders and an explicit runner.
- Keep schemas, lineage, query construction, data access and execution separate.
- Preserve duplicate matches, missing parents, assigned NULLs and old unchanged versions.
- Treat schema profiles as validation inputs; confirm deployed catalog types separately.
- Python suite builders are authoritative. Serialize each registered runtime suite before validation.
- Keep authored SQL-file execution deferred until the metadata/comment contract in runtime/TODO.md is agreed.
- Use Poe for operational entry points. Add DVC only for a real deterministic build DAG.
- Keep credentials, live configuration and record-level outputs out of version control.
- Use synthetic fixtures in CI. Local checks do not establish live Athena/Glue acceptance.
- Run `uv run poe check`, `uv run poe check-queries` and `uv run poe check-synthetic` before proposing changes.

- Follow the PPSC agent design reference: validated structured public inputs/results, explicit functions and visible workflows; keep native expressions and frames.
- Keep core domain-independent. Supply projection lineage explicitly at orchestration.
- Use YAML for runtime/environment settings; use data-migration-dev for local AWS operations (explicit overrides allowed).
