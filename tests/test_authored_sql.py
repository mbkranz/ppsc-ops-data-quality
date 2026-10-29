from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
import sqlglot

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    SqlContract,
    bind_authored_select,
)
from ppsc_ops_data_quality.runtime import prepare_query


def contract(**updates):
    values = dict(
        schema_version=1,
        definition_id="comparison",
        suite_name="suite",
        dialect="athena",
        parameters={"value": {"type": "string", "nullable": False}},
        relations={
            "records": {"catalog": "lake", "database": "domain", "relation": "records_history"}
        },
        outputs={
            "expected": {
                "role": "expected",
                "rule_id": "authored/value",
                "description": "Independent authored value",
            }
        },
    )
    values.update(updates)
    return SqlContract.model_validate(values)


def test_typed_ast_binding_preserves_literal_and_provenance():
    value = "x'; DROP TABLE records; --"
    q = bind_authored_select(
        "SELECT :value AS expected FROM records",
        contract(),
        values={"value": value},
        suite_name="suite",
    )
    assert q.meta["ppsc"]["sql_contract"]["schema_version"] == 1
    assert value in [v.this for v in q.find_all(sqlglot.exp.Literal)]
    assert len(sqlglot.parse(q.sql(dialect="athena"), read="athena")) == 1
    assert q.selects[0].meta["ppsc"]["rule_id"] == "authored/value"


@pytest.mark.parametrize(
    "kind,value",
    [
        ("boolean", False),
        ("integer", 0),
        ("date", date(2026, 1, 1)),
        ("timestamp", datetime(2026, 1, 1, tzinfo=UTC)),
        ("decimal", Decimal("0.00")),
    ],
)
def test_supported_scalar_types(kind, value):
    declaration = {"type": kind, "nullable": False}
    if kind == "decimal":
        declaration.update(precision=12, scale=2)
    q = bind_authored_select(
        "SELECT :value AS expected FROM records",
        contract(parameters={"value": declaration}),
        values={"value": value},
        suite_name="suite",
    )
    assert q.meta["ppsc"]["typed_parameters"]["value"].startswith("CAST(")


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM records",
        "SELECT :value AS expected FROM records; SELECT 2",
        "SELECT * FROM records",
        "SELECT :value + 1 FROM records",
        "SELECT :value AS wrong FROM records",
        "SELECT :value AS expected FROM undeclared",
        "SELECT :value AS expected FROM lake.domain.records",
        "SELECT :other AS expected FROM records",
    ],
)
def test_rejects_ambiguous_or_undeclared_execution(sql):
    with pytest.raises(ValueError):
        bind_authored_select(sql, contract(), values={"value": "x"}, suite_name="suite")


@pytest.mark.parametrize(
    "kind,value",
    [
        ("timestamp", datetime(2026, 1, 1)),
        ("date", "2026-01-01"),
        ("integer", True),
        ("string", None),
        ("decimal", "1.001"),
        ("decimal", "10000000000.00"),
    ],
)
def test_rejects_lossy_or_ambiguous_scalars(kind, value):
    declaration = {"type": kind, "nullable": False}
    if kind == "decimal":
        declaration.update(precision=12, scale=2)
    with pytest.raises(ValueError):
        bind_authored_select(
            "SELECT :value AS expected FROM records",
            contract(parameters={"value": declaration}),
            values={"value": value},
            suite_name="suite",
        )


def test_rejects_wrong_suite_unknown_contract_and_recursive_cte():
    with pytest.raises(ValueError):
        bind_authored_select(
            "SELECT :value AS expected FROM records",
            contract(),
            values={"value": "x"},
            suite_name="other",
        )
    with pytest.raises(ValueError):
        contract(schema_version=2)
    with pytest.raises(ValueError):
        contract(dialect="duckdb")
    with pytest.raises(ValueError):
        prepare_query(sqlglot.parse_one("WITH RECURSIVE x AS (SELECT 1 AS id) SELECT id FROM x"))


def test_full_precision_decimal_and_canonical_utc_timestamp():
    declaration = {"type": "decimal", "nullable": False, "precision": 38, "scale": 0}
    value = Decimal("99999999999999999999999999999999999999")
    q = bind_authored_select(
        "SELECT :value AS expected FROM records",
        contract(parameters={"value": declaration}),
        values={"value": value},
        suite_name="suite",
    )
    assert str(value) in q.sql()
    q = bind_authored_select(
        "SELECT :value AS expected FROM records",
        contract(parameters={"value": {"type": "timestamp", "nullable": False}}),
        values={"value": datetime(2026, 1, 1, tzinfo=UTC)},
        suite_name="suite",
    )
    assert "2026-01-01 00:00:00 UTC" in q.sql(dialect="athena")
