"""Read schema-only Athena declarations without executing SQL or discovering data."""

import ibis
import sqlglot
from sqlglot import exp


def schema_from_ddl(ddl: str) -> ibis.Schema:
    """Convert one nullable CREATE TABLE profile to a native Ibis schema.

    Profiles contain explicit scalar columns only. Storage/partition declarations,
    CTAS, constraints and defaults need their own reviewed semantics and are rejected.
    Column spelling and decimal/temporal types are retained; no aliases or casts
    are inferred. This function does not certify a deployed Athena table.
    """
    statements = sqlglot.parse(ddl, read="athena")
    if len(statements) != 1 or not isinstance(create := statements[0], exp.Create):
        raise ValueError("Expected one schema-only CREATE TABLE declaration")
    if create.kind != "TABLE" or any(
        value for key, value in create.args.items() if key not in {"this", "kind"}
    ):
        raise ValueError("Only schema-only CREATE TABLE declarations are supported")
    schema = create.this
    if not isinstance(schema, exp.Schema) or not schema.expressions:
        raise ValueError("DDL profile requires explicit column definitions")
    if not isinstance(schema.this, exp.Table) or not schema.this.name:
        raise ValueError("DDL profile requires a table name")
    names = []
    for column in schema.expressions:
        if not isinstance(column, exp.ColumnDef) or not column.name:
            raise ValueError("DDL profile requires named columns")
        if any(value for key, value in column.args.items() if key not in {"this", "kind"}):
            raise ValueError("DDL input columns must be nullable and have no constraints/defaults")
        dtype = column.kind
        if not isinstance(dtype, exp.DataType) or dtype.this not in {
            exp.DType.TEXT,
            exp.DType.VARCHAR,
            exp.DType.CHAR,
            exp.DType.BOOLEAN,
            exp.DType.TINYINT,
            exp.DType.SMALLINT,
            exp.DType.INT,
            exp.DType.BIGINT,
            exp.DType.FLOAT,
            exp.DType.DOUBLE,
            exp.DType.DECIMAL,
            exp.DType.DATE,
            exp.DType.TIMESTAMP,
            exp.DType.BINARY,
        }:
            raise ValueError(f"Unsupported Athena input type for {column.name}")
        parameters = []
        for parameter in dtype.expressions:
            if (
                not isinstance(parameter, exp.DataTypeParam)
                or not isinstance(parameter.this, exp.Literal)
                or not parameter.this.is_int
                or any(value for key, value in parameter.args.items() if key != "this")
            ):
                raise ValueError(f"Unsupported type parameter for {column.name}")
            parameters.append(int(parameter.this.this))
        if dtype.this == exp.DType.DECIMAL:
            if (
                len(parameters) != 2
                or not 1 <= parameters[0] <= 38
                or not 0 <= parameters[1] <= parameters[0]
            ):
                raise ValueError("Athena DECIMAL requires explicit valid precision and scale")
        elif dtype.this in {exp.DType.VARCHAR, exp.DType.CHAR}:
            if parameters and (len(parameters) != 1 or parameters[0] <= 0):
                raise ValueError("String length must be one positive integer")
        elif dtype.this == exp.DType.TIMESTAMP:
            if parameters and (len(parameters) != 1 or not 0 <= parameters[0] <= 9):
                raise ValueError("Timestamp precision must be one integer from 0 to 9")
        elif parameters:
            raise ValueError(f"Unsupported type arguments for {column.name}")
        if any(value for key, value in dtype.args.items() if key not in {"this", "expressions"}):
            raise ValueError(f"Unsupported type qualifiers for {column.name}")
        names.append(column.name.casefold())
    if len(names) != len(set(names)):
        raise ValueError("DDL profile column names must be unique, including case")
    return ibis.Schema.from_sqlglot(schema, dialect="athena")
