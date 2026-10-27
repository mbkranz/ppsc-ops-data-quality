"""DDL profiles are explicit, nullable and never executed or silently truncated."""

import ibis
import pytest

from ppsc_ops_data_quality.core.schemas import schema_from_ddl


def test_ddl_retains_types_names_and_raw_nulls():
    schema = schema_from_ddl(
        "CREATE TABLE input (`Id` STRING, `value.raw` DECIMAL(12,2), `at` TIMESTAMP, `date` DATE, `count` BIGINT, `valid` BOOLEAN)"
    )
    assert schema == ibis.schema(
        {
            "Id": "string",
            "value.raw": "decimal(12,2)",
            "at": "timestamp",
            "date": "date",
            "count": "int64",
            "valid": "boolean",
        }
    )
    assert all(t.nullable for t in schema.types)


@pytest.mark.parametrize(
    "ddl",
    [
        "SELECT 1",
        "CREATE TABLE t AS SELECT 1 AS a",
        "CREATE TABLE t (a INT); SELECT 1",
        "CREATE VIEW v AS SELECT 1",
        "CREATE TABLE t (a INT, A INT)",
        "CREATE TABLE t (a INT NOT NULL)",
        "CREATE TABLE t (a INT DEFAULT 0)",
        "CREATE TABLE t (a INT PRIMARY KEY)",
        "CREATE TABLE t (a INT) PARTITIONED BY (p STRING)",
        "CREATE TABLE t (a INT) LOCATION 's3://example/input/'",
        "CREATE TABLE t (a TIME)",
        "CREATE TABLE t (a ARRAY<INT>)",
        "CREATE TABLE t (a DECIMAL(39,2))",
        "CREATE TABLE t (a DECIMAL(3,4))",
        "CREATE TABLE t (a DECIMAL)",
        "CREATE TABLE t (a INT(7))",
        "CREATE TABLE t (a BOOLEAN(3))",
        "CREATE TABLE t (a BINARY(3))",
        "CREATE TABLE t (a FLOAT(10,2))",
        "CREATE TABLE t (a VARCHAR(0))",
        "CREATE TABLE t (a CHAR(0))",
        "CREATE TABLE t (a TIMESTAMP(10))",
    ],
)
def test_unsupported_or_ambiguous_profiles_are_rejected(ddl):
    with pytest.raises((ValueError, ibis.common.exceptions.IbisTypeError)):
        schema_from_ddl(ddl)


def test_supported_type_parameters_survive_native_conversion():
    schema = schema_from_ddl(
        "CREATE TABLE t (amount DECIMAL(12,2), label VARCHAR(255), at TIMESTAMP(6))"
    )
    assert schema["amount"] == ibis.dtype("decimal(12,2)")
    assert schema["label"] == ibis.dtype("string(255)")
    assert schema["at"] == ibis.dtype("timestamp(6)")
