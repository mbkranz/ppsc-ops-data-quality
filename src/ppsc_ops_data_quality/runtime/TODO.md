# TODO: Authored SQL-file execution

Add a separate execution path for checks intentionally authored in `.sql` files.
Current adapters accept Ibis tables only; optional SQL output files are audit
artifacts and are never read back for execution.

Before implementing a loader, define and review:

- A versioned metadata convention: structured header comment, sidecar manifest,
  or another explicit format. Decide whether column-level comments carry field
  lineage. Do not treat arbitrary SQL comments as validation definitions.
- Required identifiers: check/definition ID, suite reference, dialect, source
  objects/fields, expected/observed roles and original metadata IDs where present.
- Stable association of metadata with projected columns, including aliases,
  quoted identifiers, CTEs and joins. Define behavior when an alias is renamed or
  metadata is missing, duplicated or contradictory.
- Typed parameter binding for snapshots, event IDs and source-version pins;
  distinguish value parameters from table/catalog bindings. Avoid ad hoc string
  replacement and do not infer execution times from comments.
- Supported file contents: one comparison SELECT per file initially; explicit
  treatment of CTEs and terminal semicolons. Keep DDL/view publishing separate.
- Metadata preservation: ordinary SQL text does not serialize arbitrary SQLGlot
  `.meta`. Specify how recognized annotations are parsed into the AST, copied to
  native GX metadata, validated and preserved on export. Include round-trip tests.
- Run audit requirements: original file/hash, bound SQL, parameters, declared
  dialect, code/source versions and validation results. Keep generated SQL clearly
  distinguished from intentionally authored source SQL.

Implement and test the agreed convention before adding `runtime/sql_files.py`.
Do not silently route an Ibis adapter's string input to a SQL-file loader.
