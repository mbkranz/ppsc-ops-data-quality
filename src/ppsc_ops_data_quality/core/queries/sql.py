"""Compile Ibis to Athena SQL and optionally annotate explicit field lineage."""

from collections.abc import Mapping
from copy import deepcopy
from re import fullmatch

import ibis.expr.types as ir
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope


def _resolve_final_projection(query: exp.Query) -> exp.Query:
    """Remove a column-only projection over an aggregate without regrouping rows."""
    if not isinstance(query, exp.Select) or any(
        value for key, value in query.args.items() if key not in ("expressions", "from_", "with_")
    ):
        return query
    source = query.args.get("from_")
    if source is None or not isinstance(source.this, exp.Subquery):
        return query
    subquery = source.this
    inner = subquery.this
    if (
        not isinstance(inner, exp.Select)
        or not inner.args.get("group")
        or inner.args.get("with_")
        or inner.args.get("order")
        or inner.args.get("distinct")
        or inner.args.get("having")
        or inner.args.get("qualify")
    ):
        return query
    projections = {projection.alias_or_name: projection for projection in inner.selects}
    resolved = []
    for projection in query.selects:
        column = projection.unalias()
        if (
            not isinstance(column, exp.Column)
            or column.table != subquery.alias
            or column.name not in projections
        ):
            return query
        resolved.append(
            exp.alias_(
                projections[column.name].unalias().copy(), projection.alias_or_name, quoted=True
            )
        )
    # Ibis groups by SELECT ordinals. Resolve them before changing projection order.
    group = inner.args["group"]
    group.set(
        "expressions",
        [
            inner.selects[int(value.this) - 1].unalias().copy()
            if isinstance(value, exp.Literal) and value.is_int
            else value
            for value in group.expressions
        ],
    )
    inner.set("expressions", resolved)
    inner.set("with_", query.args.get("with_"))
    return inner


def _inline_ctes(query: exp.Query) -> exp.Query:
    """Keep a SELECT-first query without adding an otherwise redundant GX wrapper."""
    with_clause = query.args.get("with_")
    if with_clause is None:
        return query
    if with_clause.args.get("recursive"):
        raise ValueError("Recursive CTEs cannot be rendered as a SELECT-first Query Asset")
    # Resolve references by scope, not by spelling: a CTE may share a physical
    # table's name, including inside its own non-recursive definition.
    for scope in traverse_scope(query):
        for alias, (node, source) in scope.selected_sources.items():
            if isinstance(node, exp.Table) and isinstance(source, Scope) and source.is_cte:
                node.replace(
                    exp.Subquery(
                        this=source.expression.copy(),
                        alias=exp.TableAlias(this=exp.to_identifier(alias, quoted=True)),
                    )
                )
    query.set("with_", None)
    return query


def _name_relation_aliases(query: exp.Query) -> None:
    """Replace compiler aliases with source names without crossing SQL scopes."""
    scopes = list(traverse_scope(query))
    reserved = {name.casefold() for scope in scopes for name in scope.selected_sources}
    source_names: dict[Scope, str] = {}
    for scope in scopes:
        for alias, (node, source) in list(scope.selected_sources.items()):
            name = node.name if isinstance(node, exp.Table) else source_names.get(source, "Rows")
            source_names.setdefault(scope, name)
            if not fullmatch(r"t\d+", alias):
                continue
            candidate = name
            suffix = 2
            while candidate.casefold() in reserved:
                candidate = f"{name}_{suffix}"
                suffix += 1
            reserved.add(candidate.casefold())
            relation = node if isinstance(node, exp.Table) else node.parent
            if not isinstance(relation, (exp.Table, exp.Subquery)):
                raise ValueError(f"Unsupported SQL relation for alias {alias!r}")
            relation.set("alias", exp.TableAlias(this=exp.to_identifier(candidate, quoted=True)))
            for column in scope.columns:
                if column.table == alias:
                    column.set("table", exp.to_identifier(candidate, quoted=True))
            scope.rename_source(alias, candidate)
            scope.clear_cache()


def to_sqlglot(
    expression: ir.Table, *, projection_lineage: Mapping[str, Mapping[str, object]] | None = None
) -> exp.Query:
    """Compile the completed Ibis query to Athena's AST, then annotate projections.

    All Ibis composition happens first. Query-local CTEs become derived tables,
    so the result starts with SELECT without a SELECT-* wrapper. A column-only
    projection over an aggregate is folded into its original grouping, exposing
    the conditional aggregate expressions without merging or deduplicating groups.
    Named Ibis relations supply readable SQL
    source aliases; numeric suffixes disambiguate repeated references. Stable
    output aliases connect the final SELECT list to authoritative lineage.
    Branch provenance is nested metadata;
    compiler-generated WHEN positions and table aliases are never used as keys.

    Unknown/custom projected fields are left unannotated. The query-level record
    lists annotated and unannotated outputs. This helper returns the AST: render
    it with query.sql(dialect="athena"), rather than recompiling the Ibis table.
    Native AST copy()/dump()/load() retain the annotations. SQL text does not.
    """
    from ibis.backends.sql.compilers.athena import compiler

    query = compiler.to_sqlglot(expression)
    # Ibis can emit tuple-valued window arguments. SQLGlot's serializer expects
    # list containers for AST children; normalize them without rewriting the SQL.
    for node in query.walk():
        for key, value in list(node.args.items()):
            if isinstance(value, tuple):
                node.set(key, list(value))
    _name_relation_aliases(query)
    query = _resolve_final_projection(query)
    query = _inline_ctes(query)
    if projection_lineage is None:
        return query
    annotated = []
    unannotated = []
    sources = []
    for projection in query.selects:
        name = projection.alias_or_name
        lineage = projection_lineage.get(name)
        if lineage is None:
            unannotated.append(name)
            continue
        metadata = deepcopy(lineage)
        projection.meta["ppsc"] = metadata
        original_sources = metadata.get("source_entities", [])
        sources.extend(original_sources)
        comment = metadata["description"]
        if original_sources:
            comment += "; source: " + ", ".join(original_sources)
        projection.add_comments([comment])
        annotated.append(name)
    query.meta["ppsc"] = {
        "entity_type": "ExpectedValuesQuery",
        "dialect": "athena",
        "annotated_fields": annotated,
        "unannotated_fields": unannotated,
        "source_entities": list(dict.fromkeys(sources)),
    }
    return query
