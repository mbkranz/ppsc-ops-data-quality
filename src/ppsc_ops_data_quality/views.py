"""Optional publishing of a final Ibis query as an Athena view.

The normal validation path is queries.py -> gx_queries.py -> built-in GX suites.
Use this module only when a shared catalog object is useful to other consumers.
Publishing never participates in snapshot or comparison expression construction.
"""

import re
from collections.abc import Mapping

import ibis
import ibis.expr.types as ir
from sqlglot import exp

from ppsc_ops_data_quality.core.queries.sql import to_sqlglot


def create_view_sql(
    query: ir.Table,
    *,
    name: str,
    database: str | None = None,
    projection_lineage: Mapping[str, Mapping[str, object]] | None = None,
) -> str:
    """Emit Athena CREATE OR REPLACE VIEW for a complete, annotated query.

    Provenance: Athena CREATE VIEW syntax. A view is logical and recomputes its
    query when referenced; publishing neither materializes nor freezes its rows.
    Restrict identifiers to ordinary Athena catalog names; values in the SELECT
    have already been authored as Ibis literals. No SQL is executed here.
    """
    for label, value in (("name", name), ("database", database)):
        if label == "database" and value is None:
            continue
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError(f"{label} must be an ordinary Athena identifier")
    target = exp.Table(
        this=exp.to_identifier(name, quoted=True),
        db=exp.to_identifier(database, quoted=True) if database else None,
    )
    return (
        exp.Create(
            this=target,
            kind="VIEW",
            replace=True,
            expression=to_sqlglot(query, projection_lineage=projection_lineage),
        ).sql(dialect="athena", pretty=True)
        + ";"
    )


def create_view(
    connection,
    query: ir.Table,
    *,
    name: str,
    database: str | None = None,
    projection_lineage: Mapping[str, Mapping[str, object]] | None = None,
) -> ir.Table:
    """Publish through an existing Athena DB-API connection; return its Ibis name.

    Calling this function explicitly executes DDL. Exceptions propagate and the
    cursor closes on failure. The returned relation references the created view
    with the query's schema. No credentials or connection configuration are made.
    """
    sql = create_view_sql(
        query, name=name, database=database, projection_lineage=projection_lineage
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
    finally:
        cursor.close()
    return ibis.table(query.schema(), name=name, database=database)
