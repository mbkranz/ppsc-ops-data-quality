"""Adapt a final Ibis comparison to a native GX SQL Query Asset.

Provenance: GX Core 1.24 QueryAsset/add_batch_definition_whole_table APIs.
The SELECT wrapper accommodates compiled CTEs and leading lineage comments:
GX requires query text to begin with SELECT followed by whitespace. SQLGlot
retains the existing annotated projection nodes inside that wrapper.

GX batch parameters select configured partitions. BEFORE/execution/AFTER times
belong to the Ibis query builder and are not arbitrary GX batch parameters.
"""

from collections.abc import Mapping

import ibis.expr.types as ir
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results import to_sqlglot


def query_asset_sql(comparison: ir.Table) -> str:
    """Return one Athena SELECT, with lineage comments and no terminal semicolon.

    Compose Ibis first. to_sqlglot() annotates the compiled comparison; wrapping
    it then preserves those annotations. No SQL string substitution is performed.
    The SQL text carries comments; structured meta remains in the annotated AST
    and canonical lineage mapping rather than being serialized into SQL.
    """
    annotated = to_sqlglot(comparison)
    query = exp.select("*").from_(annotated.subquery(alias="comparison"))
    return query.sql(dialect="athena", pretty=True)


def query_batch_definition(
    data_source,
    comparison: ir.Table,
    *,
    name: str,
    metadata: Mapping[str, object] | None = None,
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
        query=query_asset_sql(comparison),
        batch_metadata=dict(metadata or {}),
    )
    return asset.add_batch_definition_whole_table(name="whole_comparison")
