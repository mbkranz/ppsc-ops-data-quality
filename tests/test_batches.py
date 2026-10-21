"""Verify the selected records and violation grain with synthetic DuckDB data."""

from datetime import date, datetime

import ibis
import pytest

from ppsc_ops_data_quality.batches import (
    account_reference_counts,
    current_state,
    state_at,
)


def test_state_at_retains_old_unchanged_and_inconsistent_flag_rows(account_history, effective_date):
    selected = state_at(account_history, effective_date)
    markers = set(selected.row_marker.execute())

    assert markers == {
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
    assert selected.columns == account_history.columns


@pytest.mark.parametrize(
    ("selected_date", "expected_version"),
    [
        (date(2026, 10, 14), "transition-old"),
        (date(2026, 10, 15), "transition-new"),
    ],
)
def test_state_at_uses_half_open_replacement_bounds(
    account_history, selected_date, expected_version
):
    selected = state_at(account_history, selected_date)
    transition = selected.filter(selected.id == "transition")

    assert list(transition.row_marker.execute()) == [expected_version]


def test_state_at_applies_the_same_boundary_to_child_versions(acr_history, effective_date):
    selected = state_at(acr_history, effective_date)
    transition = selected.filter(selected.id == "child-transition")

    assert list(transition.row_marker.execute()) == ["child-transition-new"]
    assert "future-child" not in set(selected.row_marker.execute())


def test_state_at_supports_timestamp_boundaries(duckdb_backend):
    boundary = datetime(2026, 10, 15, 12, 30)
    table = duckdb_backend.create_table(
        "timestamp_history",
        ibis.memtable(
            [
                ("old", datetime(2026, 10, 15, 8), boundary),
                ("new", boundary, None),
            ],
            schema={"id": "string", "valid_from": "timestamp", "valid_to": "timestamp"},
        ),
    )

    assert list(state_at(table, boundary).id.execute()) == ["new"]


def test_current_state_uses_only_the_current_flag(account_history):
    markers = set(current_state(account_history).row_marker.execute())

    assert markers == {
        "old-unchanged",
        "transition-new",
        "duplicate-parent-1",
        "duplicate-parent-2",
        "future-parent",
        "flagged-closed",
        "null-parent",
        "empty-parent",
        "blank-parent",
        "case-sensitive-parent",
        "unpadded-parent",
        "padded-parent",
    }


def test_reference_counts_preserve_children_and_exact_identity(
    account_history, acr_history, effective_date
):
    accounts = state_at(account_history, effective_date)
    children = state_at(acr_history, effective_date)
    result = account_reference_counts(children, accounts)
    rows = result.order_by("row_marker").to_pyarrow().to_pylist()

    assert {row["row_marker"]: row["matching_account_versions"] for row in rows} == {
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
    assert result.columns == (*children.columns, "matching_account_versions")
    assert result.schema()["matching_account_versions"].is_integer()
    assert result.select(children.columns).order_by("row_marker").to_pyarrow().to_pylist() == (
        children.order_by("row_marker").to_pyarrow().to_pylist()
    )


def test_reference_counts_do_not_deduplicate_identical_child_rows(
    account_history, acr_history, effective_date
):
    accounts = state_at(account_history, effective_date)
    children = state_at(acr_history, effective_date)
    duplicate = children.filter(children.row_marker == "valid-old-parent")
    repeated_children = children.union(duplicate, distinct=False)
    result = account_reference_counts(repeated_children, accounts)

    assert result.count().execute() == children.count().execute() + 1
    repeated = result.filter(result.row_marker == "valid-old-parent")
    assert list(repeated.matching_account_versions.execute()) == [1, 1]


def test_reference_counts_keep_children_when_parent_state_is_empty(
    account_history, acr_history, effective_date
):
    children = state_at(acr_history, effective_date)
    result = account_reference_counts(children, account_history.limit(0))

    assert result.count().execute() == children.count().execute()
    assert set(result.matching_account_versions.execute()) == {0}


def test_current_relationship_uses_current_flags_on_both_sides(account_history, acr_history):
    result = account_reference_counts(current_state(acr_history), current_state(account_history))
    counts = {
        row["row_marker"]: row["matching_account_versions"]
        for row in result.to_pyarrow().to_pylist()
    }

    assert counts["future-child"] == 1
    assert counts["closed-parent"] == 0
    assert counts["child-transition-new"] == 1
    assert "child-transition-old" not in counts


@pytest.mark.parametrize("current", [False, True])
def test_compiled_athena_query_preserves_fixture_counts_in_duckdb(
    duckdb_backend, account_history, acr_history, effective_date, current
):
    """Check a SQL dialect round trip locally; live Athena acceptance is separate."""
    account_source = ibis.table(account_history.schema(), name="account_history")
    acr_source = ibis.table(acr_history.schema(), name="acr_history")
    if current:
        accounts = current_state(account_source)
        children = current_state(acr_source)
        expected = account_reference_counts(
            current_state(acr_history), current_state(account_history)
        )
    else:
        accounts = state_at(account_source, effective_date)
        children = state_at(acr_source, effective_date)
        expected = account_reference_counts(
            state_at(acr_history, effective_date), state_at(account_history, effective_date)
        )
    query = ibis.to_sql(account_reference_counts(children, accounts), dialect="athena")
    actual = duckdb_backend.sql(query, dialect="athena")

    assert actual.order_by("row_marker").to_pyarrow().to_pylist() == (
        expected.order_by("row_marker").to_pyarrow().to_pylist()
    )
