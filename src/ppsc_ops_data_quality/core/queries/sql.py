"""Compile Ibis to Athena SQL and optionally annotate explicit field lineage."""

from collections.abc import Mapping
from copy import deepcopy
from re import fullmatch

import ibis.expr.types as ir
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope


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

    All Ibis composition happens first. Named Ibis relations supply readable SQL
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
