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
- Run `uv run poe check`, `uv run poe preview` and `uv run poe demo` before proposing changes.
