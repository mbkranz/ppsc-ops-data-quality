"""Evaluate an Ibis comparison in DuckDB, then validate its pandas result in GX."""

from collections.abc import Mapping
from pathlib import Path

import great_expectations as gx
import ibis.expr.types as ir


def prepare_validation(
    context,
    data_source,
    backend,
    comparison: ir.Table,
    suite: gx.ExpectationSuite,
    *,
    name: str,
    metadata: Mapping[str, object] | None = None,
    sql_path: str | Path | None = None,
) -> tuple[gx.ValidationDefinition, dict]:
    """Return (ValidationDefinition, {'dataframe': result}) for local validation.

    Provenance: Ibis DuckDB execution -> pandas -> native GX DataFrame Asset.
    data_source is an existing GX pandas source and suite is registered in the
    same Context. backend is the caller's ibis.duckdb connection. Bind fixtures
    or local Parquet relations before composing comparison; no production table
    names are silently redirected. This path collects the full comparison into
    local memory and is intended for bounded development/CI data.

    Compilation uses the DuckDB backend, never Athena SQL or SQL transpilation.
    sql_path optionally records compiled comparison SQL. The backend can wrap it
    for fetching results; this audit file does not persist its source fixture data.
    The native GX suite retains field/branch lineage in its expectation metadata.
    No SQL file is read, no DuckDB SQLAlchemy GX source is used, and no connection
    or Context is created or closed here. Execution errors propagate to the caller.
    """
    if backend.name != "duckdb":
        raise ValueError("The DuckDB adapter requires an Ibis DuckDB backend")
    if sql_path is not None:
        path = Path(sql_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(backend.compile(comparison, limit=None), encoding="utf-8")
    frame = backend.execute(comparison, limit=None)
    asset = data_source.add_dataframe_asset(name=name, batch_metadata=dict(metadata or {}))
    batch_definition = asset.add_batch_definition_whole_dataframe(name="whole_comparison")
    definition = context.validation_definitions.add(
        gx.ValidationDefinition(name=name, data=batch_definition, suite=suite)
    )
    return definition, {"dataframe": frame}
