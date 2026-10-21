"""Test selected rows, temporal boundaries, duplicates, and compiled SQL semantics."""

from datetime import date, datetime

import pyarrow as pa
import pytest
import sqlglot

from ppsc_ops_data_quality.batches import current_state, state_at, survey_result_account_counts


def rows(query, connection):
    sql = sqlglot.transpile(query, read="athena", write="duckdb")[0]
    found = connection.sql(sql).arrow().read_all().to_pylist()
    return sorted(found, key=lambda r: r.get("row_marker", r.get("id", "")))


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


def test_child_uses_same_boundary(survey_history, effective_date, duckdb_backend):
    selected = rows(state_at(survey_history, effective_date), duckdb_backend)
    assert [r["row_marker"] for r in selected if r["id"] == "transition-survey"] == [
        "survey-transition-new"
    ]
    assert "future-survey" not in {r["row_marker"] for r in selected}


def test_current_uses_flag_alone(account_history, duckdb_backend):
    selected = {r["row_marker"] for r in rows(current_state(account_history), duckdb_backend)}
    assert "future-parent" in selected and "flagged-closed" in selected
    assert "unflagged-open" not in selected and "null-flag-open" not in selected


def test_reference_counts_preserve_surveys_and_both_exact_hops(
    account_history, contact_history, survey_history, effective_date, duckdb_backend
):
    surveys = state_at(survey_history, effective_date)
    result = survey_result_account_counts(
        surveys,
        state_at(contact_history, effective_date),
        state_at(account_history, effective_date),
    )
    actual = rows(result, duckdb_backend)
    metrics = {
        r["row_marker"]: (
            r["matching_contact_versions"],
            r["missing_account_references"],
            r["matching_account_versions"],
        )
        for r in actual
    }
    assert metrics == {
        "valid-old-parent": (1, 0, 1),
        "another-survey-same-account": (1, 0, 1),
        "survey-transition-new": (1, 0, 1),
        "missing-account": (1, 0, 0),
        "null-account-reference": (1, 1, 0),
        "empty-account-reference": (1, 1, 0),
        "blank-account-reference": (1, 1, 0),
        "duplicate-account": (1, 0, 2),
        "closed-account": (1, 0, 0),
        "case-account-mismatch": (1, 0, 0),
        "case-account-exact": (1, 0, 1),
        "spacing-account-mismatch": (1, 0, 0),
        "spacing-account-exact": (1, 0, 1),
        "missing-participant": (0, 0, 0),
        "null-participant": (0, 0, 0),
        "empty-participant": (0, 0, 0),
        "blank-participant": (0, 0, 0),
        "duplicate-participant": (2, 0, 2),
        "closed-participant": (0, 0, 0),
        "case-participant-mismatch": (0, 0, 0),
        "case-participant-exact": (1, 0, 1),
        "spacing-participant-mismatch": (0, 0, 0),
        "spacing-participant-exact": (1, 0, 1),
        "no-direct-account-shortcut": (0, 0, 0),
    }
    for row in actual:
        for field in (
            "matching_contact_versions",
            "missing_account_references",
            "matching_account_versions",
        ):
            row.pop(field)
    assert actual == rows(surveys, duckdb_backend)


def test_current_relationship_selects_all_three_sources(
    account_history, contact_history, survey_history, duckdb_backend
):
    result = survey_result_account_counts(
        current_state(survey_history),
        current_state(contact_history),
        current_state(account_history),
    )
    found = {row["row_marker"]: row for row in rows(result, duckdb_backend)}
    assert found["future-survey"]["matching_contact_versions"] == 1
    assert found["future-survey"]["matching_account_versions"] == 1
    assert found["closed-participant"]["matching_contact_versions"] == 0
    assert "survey-transition-old" not in found


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


@pytest.mark.parametrize("empty_side", ["contact", "account"])
def test_empty_parent_state_and_identical_surveys(
    account_history, contact_history, survey_history, effective_date, duckdb_backend, empty_side
):
    surveys = state_at(survey_history, effective_date)
    contacts = state_at(contact_history, effective_date)
    accounts = state_at(account_history, effective_date)
    if empty_side == "contact":
        contacts = f"SELECT * FROM ({contacts}) WHERE FALSE"
    else:
        accounts = f"SELECT * FROM ({accounts}) WHERE FALSE"
    repeated = f"({surveys}) UNION ALL ({surveys})"
    result = rows(survey_result_account_counts(repeated, contacts, accounts), duckdb_backend)
    assert len(result) == len(rows(surveys, duckdb_backend)) * 2
    assert {r["matching_account_versions"] for r in result} == {0}
    if empty_side == "contact":
        assert {r["matching_contact_versions"] for r in result} == {0}
    else:
        assert any(r["matching_contact_versions"] == 2 for r in result)


@pytest.mark.parametrize("day, expected_account_count", [(14, 0), (15, 1)])
def test_same_effective_selection_is_applied_to_every_hop(
    account_history, contact_history, survey_history, duckdb_backend, day, expected_account_count
):
    effective = date(2026, 10, day)
    result = survey_result_account_counts(
        state_at(survey_history, effective),
        state_at(contact_history, effective),
        state_at(account_history, effective),
    )
    transition = [row for row in rows(result, duckdb_backend) if row["id"] == "transition-survey"]
    assert len(transition) == 1
    assert transition[0]["matching_contact_versions"] == 1
    assert transition[0]["matching_account_versions"] == expected_account_count
