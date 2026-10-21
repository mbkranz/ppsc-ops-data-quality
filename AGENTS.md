# Repository guidelines

- Keep one obvious implementation of each query or rule.
- Use Narwhals functions for shared relational logic, native GX suite builders for rules,
  and an explicit runner. Add modules only for implemented requirements.
- Keep configuration, data access, batch selection, and suites separate.
- Preserve old unchanged records, duplicate parents, and explicit null semantics.
- Keep graph and notebook evidence in authoring; validation runs committed code.
- Use Poe for command entry points. Add DVC only for a real deterministic build DAG.
- Keep credentials, live bindings, and record-level outputs out of version control.
- Use synthetic fixtures in CI. Local tests do not establish live Athena acceptance.
- Run `uv run poe check` and a documented dry run before proposing changes.
