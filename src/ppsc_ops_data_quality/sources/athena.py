"""Read a bounded Athena table definition into a native, nullable Ibis schema.

The DDL remains the physical evidence. This adapter reads queryable column
names and types; it does not recreate storage, authorize deployment, or infer a
view/query output. File access and relation selection stay with the caller.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ibis


class UnsupportedSchemaError(ValueError):
    """A selected type or declaration cannot be represented faithfully."""


def athena_schema(ddl: str, *, fields: tuple[str, ...] | None = None) -> ibis.Schema:
    """Read one schema-bearing Athena CREATE TABLE, including Hive partitions.

    Selected field names use their exact declared spelling. Athena name
    collisions are rejected case-insensitively. Unselected unsupported types
    remain in native DDL evidence without blocking a supported projection.
    Raw validation inputs, including nested fields, always remain nullable.
    """
    import ibis
    import ibis.expr.datatypes as dt
    import sqlglot
    from sqlglot import exp
    from sqlglot.errors import ParseError

    try:
        statements = sqlglot.parse(ddl, read="athena", error_level="RAISE")
    except ParseError as exc:
        raise UnsupportedSchemaError(f"Invalid Athena table definition: {exc}") from exc
    if len(statements) != 1:
        raise UnsupportedSchemaError("Supply exactly one Athena CREATE TABLE statement")
    statement = statements[0]
    if (
        not isinstance(statement, exp.Create)
        or statement.kind != "TABLE"
        or not isinstance(statement.this, exp.Schema)
        or statement.expression is not None
    ):
        raise UnsupportedSchemaError(
            "Supply schema-bearing CREATE TABLE; views/CTAS/queries need a verified output schema"
        )
    columns = list(statement.this.expressions)
    if not columns or any(not isinstance(col, exp.ColumnDef) for col in columns):
        raise UnsupportedSchemaError("CREATE TABLE needs explicit column definitions")
    iceberg = any(
        str(prop.this).strip("'\"").casefold() == "table_type"
        and str(prop.args.get("value")).strip("'\"").casefold() == "iceberg"
        for prop in (statement.args.get("properties") or exp.Properties()).expressions
    )
    declared = {col.name.casefold() for col in columns}
    for partition in statement.find_all(exp.PartitionedByProperty):
        if not isinstance(partition.this, exp.Schema):
            raise UnsupportedSchemaError("Partition declarations need explicit native evidence")
        for item in partition.this.expressions:
            if isinstance(item, exp.ColumnDef):
                columns.append(item)
            elif iceberg:
                # Iceberg transforms refer to data columns; they are not input columns.
                references = (
                    [item] if isinstance(item, exp.Identifier) else list(item.find_all(exp.Column))
                )
                if not references or any(col.name.casefold() not in declared for col in references):
                    raise UnsupportedSchemaError(
                        "Iceberg partition references an undeclared column"
                    )
            else:
                raise UnsupportedSchemaError("Hive partition columns require declared types")
    names = [col.name for col in columns]
    if any(not name for name in names) or len({n.casefold() for n in names}) != len(names):
        raise ValueError("Duplicate or case-colliding Athena column/partition names")
    selected = names if fields is None else list(fields)
    if (
        not selected
        or len({n.casefold() for n in selected}) != len(selected)
        or any(name not in names for name in selected)
    ):
        raise ValueError("Select nonempty, unique declared Athena fields with exact names")
    definitions = {col.name: col for col in columns}
    supported = {
        "BOOLEAN",
        "TINYINT",
        "SMALLINT",
        "INT",
        "BIGINT",
        "FLOAT",
        "DOUBLE",
        "DECIMAL",
        "TEXT",
        "VARCHAR",
        "CHAR",
        "BINARY",
        "VARBINARY",
        "DATE",
        "TIMESTAMP",
        "TIMESTAMPTZ",
        "TIMESTAMPLTZ",
        "ARRAY",
        "MAP",
        "STRUCT",
    }
    for name in selected:
        column = definitions[name]
        kind = column.args.get("kind")
        if not isinstance(kind, exp.DataType):
            raise UnsupportedSchemaError(f"{name}: missing Athena datatype")
        for nested in kind.walk():
            if isinstance(nested, exp.DataType) and nested.this.name not in supported:
                raise UnsupportedSchemaError(f"{name}: unsupported Athena datatype {nested.sql()}")
            if isinstance(nested, exp.ColumnDef) and not isinstance(
                nested.args.get("kind"), exp.DataType
            ):
                raise UnsupportedSchemaError(f"{name}: unresolved nested field {nested.name}")
        for struct in kind.find_all(exp.DataType):
            if struct.this.name == "STRUCT":
                nested_names = [col.name.casefold() for col in struct.expressions]
                if len(set(nested_names)) != len(nested_names):
                    raise UnsupportedSchemaError(f"{name}: case-colliding nested field names")
    try:
        schema = ibis.Schema.from_sqlglot(
            exp.Schema(expressions=[definitions[name].copy() for name in selected]),
            dialect="athena",
        )
    except Exception as exc:
        raise UnsupportedSchemaError(f"Selected Athena types cannot be converted: {exc}") from exc

    def nullable(dtype):
        if dtype.is_unknown() or dtype.is_null():
            raise UnsupportedSchemaError("Unresolved selected Athena datatype")
        if dtype.is_array():
            return dt.Array(nullable(dtype.value_type), nullable=True)
        if dtype.is_map():
            return dt.Map(nullable(dtype.key_type), nullable(dtype.value_type), nullable=True)
        if dtype.is_struct():
            return dt.Struct(
                {name: nullable(value) for name, value in dtype.items()}, nullable=True
            )
        return dtype.copy(nullable=True)

    return ibis.schema([(name, nullable(dtype)) for name, dtype in schema.items()])
