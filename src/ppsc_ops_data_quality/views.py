"""Explicit run-scoped query views; native SQL trees and bounded Athena effects."""

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
from typing import Any, Self

from pydantic import Field, model_validator
from sqlglot import ErrorLevel, exp

from ppsc_ops_data_quality.io import RelationLocation
from ppsc_ops_data_quality.runtime import Configuration, execute_athena_query


class ViewConfiguration(Configuration):
    database: str = Field(pattern=r"^[a-z][a-z0-9_]{0,62}$")
    prefix: str = Field(default="ppsc_dq_query", pattern=r"^[a-z][a-z0-9_]{0,62}$")
    timeout_seconds: int = Field(default=60, ge=1, le=3600)


class ViewRequest(Configuration):
    location: RelationLocation
    timeout_seconds: int = Field(default=60, ge=1, le=3600)

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        import re

        if not all(
            re.fullmatch(r"[a-z][a-z0-9_]{0,254}", value)
            for value in (self.location.database, self.location.relation)
        ):
            raise ValueError("Query view database/name must be safe lowercase identifiers")
        return self


class ViewReceipt(Configuration):
    location: RelationLocation
    query_id: str = Field(min_length=1)
    definition_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    definition_utf8_bytes: int = Field(gt=0, le=262_144)


def _view_columns(query: exp.Select) -> list[str]:
    if not isinstance(query, exp.Select):
        raise TypeError("Query view requires a SELECT")
    names = query.named_selects
    if (
        not names
        or len(names) != len(query.selects)
        or len({n.casefold() for n in names}) != len(names)
        or any(
            not n or p.is_star or not isinstance(p, (exp.Column, exp.Alias))
            for n, p in zip(names, query.selects, strict=True)
        )
    ):
        raise ValueError("Query view requires explicit unique output columns")
    return names


def extract_cte_view(
    comparison: exp.Select, *, cte_name: str, location: RelationLocation
) -> tuple[exp.Select, exp.Select]:
    """Extract one explicit top-level relation, replacing only its definition.

    The selected CTE must be self-contained. Its entire explicit projection becomes
    the view interface; no generated row number is rejoined across query boundaries.
    The source AST and per-output metadata are preserved without mutation.
    """
    from sqlglot.optimizer.scope import Scope, traverse_scope

    result = comparison.copy()
    selected = [cte for cte in result.ctes if cte.alias_or_name == cte_name]
    if len(selected) != 1 or not isinstance(selected[0].this, exp.Select):
        raise ValueError("Select one explicit top-level SELECT CTE for the view")
    definition = selected[0].this.copy()
    names = _view_columns(definition)
    siblings = {cte.alias_or_name.casefold() for cte in result.ctes}
    for scope in traverse_scope(definition):
        if scope.parent is None and any(c.table for c in scope.external_columns):
            raise ValueError("Query view cannot have correlated external columns")
        for node, source in scope.selected_sources.values():
            if (
                isinstance(node, exp.Table)
                and not isinstance(source, Scope)
                and not node.db
                and not node.catalog
                and node.name.casefold() in siblings
            ):
                raise ValueError("Query view depends on another outer CTE")
    reference = exp.select(*[exp.column(name, quoted=True) for name in names]).from_(
        exp.table_(location.relation, db=location.database, catalog=location.catalog, quoted=True)
    )
    reference.meta.update(deepcopy(definition.meta))
    for output, original in zip(reference.selects, definition.selects, strict=True):
        output.meta.update(deepcopy(original.meta))
    selected[0].set("this", reference)
    result.meta.setdefault("ppsc", {})["query_view"] = {
        "relation": location.identity,
        "cte": cte_name,
        "outputs": names,
    }
    return definition, result


def create_view_sql(query: exp.Select, request: ViewRequest) -> str:
    """Render one non-replacing CREATE VIEW, size-checked before any external effect."""
    location = request.location
    _view_columns(query)
    ddl = exp.Create(
        this=exp.table_(location.relation, db=location.database, quoted=True),
        kind="VIEW",
        expression=query.copy(),
    )
    sql = ddl.sql(
        dialect="athena", comments=False, pretty=False, unsupported_level=ErrorLevel.RAISE
    )
    if len(sql.encode("utf-8")) > 262_144:
        raise ValueError("CREATE VIEW exceeds Athena's 262144-byte query limit")
    return sql


def create_query_view(
    query: exp.Select,
    request: ViewRequest,
    *,
    athena_client: Any,
    query_options: Mapping[str, Any],
) -> ViewReceipt:
    """Create one new view and wait; no replacement, cache or materialization."""
    sql = create_view_sql(query, request)
    options = dict(query_options)
    options["QueryExecutionContext"] = {
        "Catalog": request.location.catalog,
        "Database": request.location.database,
    }
    query_id = execute_athena_query(
        athena_client,
        sql,
        query_options=options,
        timeout_seconds=request.timeout_seconds,
        operation="CREATE query view",
    )
    return ViewReceipt(
        location=request.location,
        query_id=query_id,
        definition_sha256=sha256(sql.encode()).hexdigest(),
        definition_utf8_bytes=len(sql.encode()),
    )


def drop_query_view(
    receipt: ViewReceipt,
    *,
    athena_client: Any,
    query_options: Mapping[str, Any],
    timeout_seconds: int,
) -> str:
    """Drop only a successfully created view selected by its receipt; return query ID."""
    location = receipt.location
    sql = exp.Drop(
        this=exp.table_(location.relation, db=location.database, quoted=True), kind="VIEW"
    ).sql(dialect="athena")
    options = dict(query_options)
    options["QueryExecutionContext"] = {
        "Catalog": location.catalog,
        "Database": location.database,
    }
    return execute_athena_query(
        athena_client,
        sql,
        query_options=options,
        timeout_seconds=timeout_seconds,
        operation="DROP query view",
    )
