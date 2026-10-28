"""Prepare native GX validations over Ibis comparisons compiled for Athena."""

from collections.abc import Mapping
from pathlib import Path

import great_expectations as gx
import ibis.expr.types as ir
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope

from ppsc_ops_data_quality.gx_queries import query_batch_definition
from ppsc_ops_data_quality.sources.apmp import RelationLocation


def query_source_tables(query_sql: str, *, locations: Mapping[str, RelationLocation]) -> list[str]:
    """Report only selected physical sources actually read by the submitted query."""
    selected = {
        (location.catalog, location.database, location.relation): location.identity
        for location in locations.values()
    }
    used = set()
    for scope in traverse_scope(sqlglot.parse_one(query_sql, read="athena")):
        for node, source in scope.selected_sources.values():
            if not isinstance(node, exp.Table) or isinstance(source, Scope):
                continue  # CTEs and derived aliases are not physical data sources.
            identity = (node.catalog, node.db, node.name)
            if identity not in selected:
                raise ValueError(
                    f"Validation query references an unselected physical relation: {node.sql(dialect='athena')}"
                )
            used.add(identity)
    return [identity for key, identity in selected.items() if key in used]


def prepare_validation(
    context,
    data_source,
    comparison: ir.Table,
    suite: gx.ExpectationSuite,
    *,
    name: str,
    metadata: Mapping[str, object] | None = None,
    projection_lineage: Mapping[str, Mapping[str, object]] | None = None,
    table_versions: Mapping[tuple[str, str, str], str] | None = None,
    sql_path: str | Path | None = None,
) -> tuple[gx.ValidationDefinition, dict]:
    """Return (ValidationDefinition, batch parameters) for one Athena comparison.

    Provenance: GX 1.24 QueryAsset -> whole-query BatchDefinition ->
    ValidationDefinition. query_batch_definition() performs Ibis compilation
    and SQLGlot lineage attachment. No SQL files are read for execution.

    Supply an existing SQL Data Source and a suite registered in the same Context.
    The SQL Data Source must use the configured Athena SQLAlchemy connection;
    credentials, schema bindings, temporal parameters and source pins belong to
    the caller. Unique run-scoped names prevent conflicting asset replacement.

    sql_path optionally saves the exact SELECT assigned to the Query Asset for
    audit/review. GX's actual metric queries may wrap that SELECT. No batch is
    fetched here, no views are created and Context configuration is not invented.
    The caller owns the Context, connection and result-store lifecycle.
    """
    batch_definition = query_batch_definition(
        data_source,
        comparison,
        name=name,
        metadata=metadata,
        projection_lineage=projection_lineage,
        table_versions=table_versions,
    )
    if sql_path is not None:
        path = Path(sql_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(batch_definition.data_asset.query, encoding="utf-8")
    definition = context.validation_definitions.add(
        gx.ValidationDefinition(name=name, data=batch_definition, suite=suite)
    )
    return definition, {}
