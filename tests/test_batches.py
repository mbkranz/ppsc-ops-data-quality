"""Test selected rows, temporal boundaries, duplicates, and compiled SQL semantics."""

from datetime import date, datetime

import pyarrow as pa
import pytest
import sqlglot

from ppsc_ops_data_quality.batches import account_reference_counts, current_state, state_at


def rows(query, connection):
    sql = sqlglot.transpile(query, read="athena", write="duckdb")[0]
    found = connection.sql(sql).arrow().read_all().to_pylist()
    return sorted(found, key=lambda r: r.get("row_marker", r.get("id", "")))


def counts(query, connection):
    return {row["row_marker"]: row["matching_account_versions"] for row in rows(query, connection)}


def test_state_retains_old_records_and_half_open_boundaries(
    account_history, effective_date, duckdb_backend
):
    selected = rows(state_at(account_history, effective_date), duckdb_backend)
    assert {r["row_marker"] for r in selected} == {
        "old-unchanged",
        "transition-new",
        "duplicate-parent-1",
        "duplicate-parent-2",
        "unflagged-open",
        "null-flag-open",
        "null-parent",
        "empty-parent",
        "blank-parent",
        "case-sensitive-parent",
        "unpadded-parent",
        "padded-parent",
    }
    before = rows(state_at(account_history, date(2026, 10, 14)), duckdb_backend)
    assert [r["row_marker"] for r in before if r["id"] == "transition"] == ["transition-old"]


def test_child_uses_same_boundary(acr_history, effective_date, duckdb_backend):
    selected = rows(state_at(acr_history, effective_date), duckdb_backend)
    assert [r["row_marker"] for r in selected if r["id"] == "child-transition"] == [
        "child-transition-new"
    ]
    assert "future-child" not in {r["row_marker"] for r in selected}


def test_current_uses_flag_alone(account_history, duckdb_backend):
    selected = {r["row_marker"] for r in rows(current_state(account_history), duckdb_backend)}
    assert "future-parent" in selected and "flagged-closed" in selected
    assert "unflagged-open" not in selected and "null-flag-open" not in selected


def test_reference_counts_preserve_children_and_exact_identity(
    account_history, acr_history, effective_date, duckdb_backend
):
    children = state_at(acr_history, effective_date)
    result = account_reference_counts(children, state_at(account_history, effective_date))
    assert counts(result, duckdb_backend) == {
        "valid-old-parent": 1,
        "child-transition-new": 1,
        "missing-parent": 0,
        "null-reference": 0,
        "empty-reference": 0,
        "blank-reference": 0,
        "duplicate-parent": 2,
        "closed-parent": 0,
        "case-mismatch": 0,
        "case-exact": 1,
        "spacing-mismatch": 0,
        "spacing-exact": 1,
        "unpadded-exact": 1,
        "duplicate-child-1": 1,
        "duplicate-child-2": 1,
    }
    actual = rows(result, duckdb_backend)
    for row in actual:
        row.pop("matching_account_versions")
    assert actual == rows(children, duckdb_backend)


def test_current_relationship_selects_both_sides(account_history, acr_history, duckdb_backend):
    result = account_reference_counts(current_state(acr_history), current_state(account_history))
    found = counts(result, duckdb_backend)
    assert found["future-child"] == 1 and found["closed-parent"] == 0
    assert "child-transition-old" not in found


def test_timestamp_boundaries(duckdb_backend):
    boundary = datetime(2026, 10, 15, 12, 30)
    data = pa.table(
        {
            "id": ["old", "new"],
            "valid_from": [datetime(2026, 10, 15, 8), boundary],
            "valid_to": [boundary, None],
        }
    )
    duckdb_backend.from_arrow(data).create_view("timestamp_history")
    table = "SELECT * FROM timestamp_history"
    assert [r["id"] for r in rows(state_at(table, boundary), duckdb_backend)] == ["new"]


def test_empty_parent_state_and_identical_children(
    account_history, acr_history, effective_date, duckdb_backend
):
    children = state_at(acr_history, effective_date)
    empty = f"SELECT * FROM ({account_history}) WHERE FALSE"
    repeated = f"({children}) UNION ALL ({children})"
    result = account_reference_counts(repeated, empty)
    found = rows(result, duckdb_backend)
    assert len(found) == len(rows(children, duckdb_backend)) * 2
    assert {r["matching_account_versions"] for r in found} == {0}


@pytest.mark.parametrize("current", [False, True])
def test_generated_athena_sql_executes_with_same_counts(
    account_history, acr_history, effective_date, duckdb_backend, current
):
    select = current_state if current else lambda t: state_at(t, effective_date)
    expected = account_reference_counts(select(acr_history), select(account_history))
    query = expected
    actual = duckdb_backend.sql(sqlglot.transpile(query, read="athena", write="duckdb")[0])
    assert sorted(actual.arrow().read_all().to_pylist(), key=lambda r: r["row_marker"]) == rows(
        expected, duckdb_backend
    )
