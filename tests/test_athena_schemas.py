"""The shared Athena reader preserves selected types and raw invalid values."""

import ibis
import ibis.expr.datatypes as dt
import pyarrow as pa
import pytest

from ppsc_ops_data_quality.sources.athena import UnsupportedSchemaError, athena_schema


def test_native_scalar_profile_preserves_widths_precision_lengths_and_timezones():
    result = athena_schema("""CREATE EXTERNAL TABLE `Lake` (
      flag BOOLEAN, i8 TINYINT, i16 SMALLINT, i32 INT, i64 BIGINT,
      f32 FLOAT, f64 DOUBLE, amount DECIMAL(20,7), name VARCHAR(17),
      code CHAR(5), blob BINARY, day DATE, moment TIMESTAMP(6),
      zoned TIMESTAMP(3) WITH TIME ZONE
    ) STORED AS PARQUET LOCATION 's3://fixture-only/lake'""")
    assert [str(result[n]) for n in ("i8", "i16", "i32", "i64")] == [
        "int8",
        "int16",
        "int32",
        "int64",
    ]
    assert result["f32"] == dt.float32 and result["f64"] == dt.float64
    assert result["amount"] == dt.Decimal(20, 7)
    assert str(result["name"]) == "string(17)"
    assert str(result["code"]) == "string(5)"
    assert result["blob"] == dt.binary and result["day"] == dt.date
    assert result["moment"] == dt.Timestamp(scale=6)
    assert result["zoned"] == dt.Timestamp(timezone="UTC", scale=3)
    assert all(dtype.nullable for dtype in result.types)


def test_hive_partition_columns_are_queryable_once_and_conflicts_rejected():
    result = athena_schema(
        "CREATE EXTERNAL TABLE x (id STRING) PARTITIONED BY (delivery DATE, batch INT) STORED AS PARQUET"
    )
    assert result.names == ("id", "delivery", "batch")
    assert result["delivery"] == dt.date
    with pytest.raises(ValueError, match="case-colliding"):
        athena_schema("CREATE TABLE x (Id STRING) PARTITIONED BY (id INT)")


def test_iceberg_hidden_transforms_never_become_input_columns():
    ddl = """CREATE TABLE events (id STRING, logged TIMESTAMP, region STRING)
      PARTITIONED BY (bucket(16,id), day(logged), region)
      TBLPROPERTIES ('table_type'='ICEBERG')"""
    assert athena_schema(ddl).names == ("id", "logged", "region")
    with pytest.raises(UnsupportedSchemaError, match="undeclared"):
        athena_schema(ddl.replace("day(logged)", "day(missing)"))
    with pytest.raises(UnsupportedSchemaError, match="Hive partition"):
        athena_schema(ddl.replace("'ICEBERG'", "'OTHER'"))


def test_nested_field_order_names_and_nullable_raw_values_survive():
    result = athena_schema("""CREATE TABLE x (
      id STRING NOT NULL,
      payload STRUCT<`MixedCase`:INT, items:ARRAY<MAP<STRING,DECIMAL(10,2)>>>
    )""")
    assert result["id"].nullable
    assert result["payload"].names == ("MixedCase", "items")
    assert result["payload"]["MixedCase"] == dt.int32
    assert result["payload"]["items"].value_type.value_type == dt.Decimal(10, 2)
    con = ibis.duckdb.connect()
    try:
        table = con.create_table(
            "raw_nulls",
            ibis.memtable(
                pa.Table.from_pylist([{"id": None}], schema=pa.schema([("id", pa.string())]))
            ),
        )
        assert table.id.isnull().sum().execute() == 1
    finally:
        con.disconnect()


@pytest.mark.parametrize(
    "ddl",
    [
        "SELECT 1",
        "CREATE VIEW x AS SELECT 1 AS id",
        "CREATE TABLE x AS SELECT 1 AS id",
        "CREATE TABLE x(id STRING); CREATE TABLE y(id INT)",
        "CREATE TABLE x (id)",
        "CREATE TABLE x(id STRING, Id INT)",
        "CREATE TABLE x(a ARRAY<JSON>)",
        "CREATE TABLE x(a STRUCT<id:INT,ID:STRING>)",
    ],
)
def test_unsupported_or_ambiguous_selected_definitions_fail(ddl):
    with pytest.raises((ValueError, UnsupportedSchemaError)):
        athena_schema(ddl)


def test_selected_projection_does_not_require_unrelated_supported_types():
    ddl = "CREATE TABLE x(id STRING, opaque JSON, amount DECIMAL(9,2))"
    assert athena_schema(ddl, fields=("amount", "id")).names == ("amount", "id")
    with pytest.raises(UnsupportedSchemaError, match="unsupported"):
        athena_schema(ddl)
    for fields in [("missing",), ("id", "id"), ()]:
        with pytest.raises(ValueError, match="unique declared Athena"):
            athena_schema(ddl, fields=fields)
