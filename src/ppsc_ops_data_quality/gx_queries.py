"""Adapt a final Ibis comparison to a native GX SQL Query Asset.

Provenance: GX Core 1.24 QueryAsset/add_batch_definition_whole_table APIs.
The shared renderer returns a SELECT-first query with explicit projections.
GX requires query text to begin with SELECT followed by whitespace.

GX batch parameters select configured partitions. BEFORE/execution/AFTER times
belong to the Ibis query builder and are not arbitrary GX batch parameters.
"""

from collections.abc import Mapping

import ibis.expr.types as ir

from ppsc_ops_data_quality.core.queries.sql import to_sqlglot


def query_asset_sql(
    comparison: ir.Table, *, projection_lineage: Mapping[str, Mapping[str, object]] | None = None
) -> str:
    """Return one Athena SELECT, with lineage comments and no terminal semicolon.

    Compose Ibis first. to_sqlglot() resolves and annotates the final projections.
    Shared CTEs remain inside a named input relation with an explicit SELECT list.
    No SQL string substitution is performed.
    The SQL text carries comments; structured meta remains in the annotated AST
    and canonical lineage mapping rather than being serialized into SQL.
    """
    query = to_sqlglot(comparison, projection_lineage=projection_lineage)
    sql = query.sql(dialect="athena", pretty=False)
    # https://docs.aws.amazon.com/athena/latest/ug/service-limits.html
    if len(sql.encode("utf-8")) > 262_144:
        raise ValueError("Comparison SQL exceeds Athena's 262144-byte query limit")
    return sql


def query_batch_definition(
    data_source,
    comparison: ir.Table,
    *,
    name: str,
    metadata: Mapping[str, object] | None = None,
    projection_lineage: Mapping[str, Mapping[str, object]] | None = None,
):
    """Register a native Query Asset and return its whole-query Batch Definition.

    data_source is an existing GX SQL Data Source using the Athena SQLAlchemy
    connection. Use a run-scoped ephemeral Context or a unique asset name for
    distinct SQL bindings; existing assets are never silently overwritten.
    Metadata records run facts; it does not bind SQL parameters or filter rows.

    The caller explicitly retrieves/validates the batch. No custom expectations,
    temporary tables, view DDL, context creation or checkpoint setup is performed.
    A whole-query batch does not guarantee one SQL execution for all expectations.
    """
    asset = data_source.add_query_asset(
        name=name,
        query=query_asset_sql(comparison, projection_lineage=projection_lineage),
        batch_metadata=dict(metadata or {}),
    )
    return asset.add_batch_definition_whole_table(name="whole_comparison")
