"""Synthetic histories with observable version and relationship edge cases."""

from datetime import date, datetime

import ibis
import pytest


@pytest.fixture
def duckdb_backend():
    backend = ibis.duckdb.connect()
    yield backend
    backend.disconnect()


@pytest.fixture
def effective_date():
    return date(2026, 10, 15)


@pytest.fixture
def account_history(duckdb_backend):
    base = {
        "valid_from": date(2026, 6, 25),
        "valid_to": None,
        "is_current": True,
        "loaded_at": datetime(2026, 6, 26),
    }
    rows = [
        dict(base, row_marker="old-unchanged", id="old"),
        dict(
            base,
            row_marker="transition-old",
            id="transition",
            valid_to=date(2026, 10, 15),
            is_current=False,
        ),
        dict(
            base,
            row_marker="transition-new",
            id="transition",
            valid_from=date(2026, 10, 15),
            loaded_at=datetime(2026, 10, 15),
        ),
        dict(base, row_marker="duplicate-parent-1", id="duplicate"),
        dict(
            base,
            row_marker="duplicate-parent-2",
            id="duplicate",
            valid_from=date(2026, 10, 1),
            loaded_at=datetime(2026, 10, 1),
        ),
        dict(
            base,
            row_marker="closed-parent",
            id="closed",
            valid_to=date(2026, 10, 14),
            is_current=False,
        ),
        dict(
            base,
            row_marker="future-parent",
            id="future",
            valid_from=date(2026, 10, 20),
            loaded_at=datetime(2026, 10, 20),
        ),
        dict(
            base,
            row_marker="flagged-closed",
            id="flagged-closed",
            valid_to=date(2026, 10, 14),
        ),
        dict(base, row_marker="unflagged-open", id="unflagged", is_current=False),
        dict(base, row_marker="null-flag-open", id="null-flag", is_current=None),
        dict(base, row_marker="null-parent", id=None),
        dict(base, row_marker="empty-parent", id=""),
        dict(base, row_marker="blank-parent", id="  "),
        dict(base, row_marker="case-sensitive-parent", id="CaseID"),
        dict(base, row_marker="unpadded-parent", id="exact"),
        dict(base, row_marker="padded-parent", id="exact "),
    ]
    schema = {
        "row_marker": "string",
        "id": "string",
        "valid_from": "date",
        "valid_to": "date",
        "is_current": "boolean",
        "loaded_at": "timestamp",
    }
    return duckdb_backend.create_table("account_history", ibis.memtable(rows, schema=schema))


@pytest.fixture
def acr_history(duckdb_backend):
    base = {
        "valid_from": date(2026, 6, 25),
        "valid_to": None,
        "is_current": True,
        "loaded_at": datetime(2026, 6, 26),
    }
    rows = [
        dict(base, row_marker="valid-old-parent", id="child-old", account_id="old"),
        dict(
            base,
            row_marker="child-transition-old",
            id="child-transition",
            account_id="closed",
            valid_to=date(2026, 10, 15),
            is_current=False,
        ),
        dict(
            base,
            row_marker="child-transition-new",
            id="child-transition",
            account_id="transition",
            valid_from=date(2026, 10, 15),
            loaded_at=datetime(2026, 10, 15),
        ),
        dict(base, row_marker="missing-parent", id="child-missing", account_id="absent"),
        dict(base, row_marker="null-reference", id="child-null", account_id=None),
        dict(base, row_marker="empty-reference", id="child-empty", account_id=""),
        dict(base, row_marker="blank-reference", id="child-blank", account_id="  "),
        dict(base, row_marker="duplicate-parent", id="child-ambiguous", account_id="duplicate"),
        dict(base, row_marker="closed-parent", id="child-closed", account_id="closed"),
        dict(base, row_marker="case-mismatch", id="child-case-mismatch", account_id="caseid"),
        dict(base, row_marker="case-exact", id="child-case-exact", account_id="CaseID"),
        dict(base, row_marker="spacing-mismatch", id="child-spacing-mismatch", account_id="old "),
        dict(base, row_marker="spacing-exact", id="child-spacing-exact", account_id="exact "),
        dict(base, row_marker="unpadded-exact", id="child-unpadded", account_id="exact"),
        dict(base, row_marker="duplicate-child-1", id="repeated-child", account_id="old"),
        dict(base, row_marker="duplicate-child-2", id="repeated-child", account_id="old"),
        dict(
            base,
            row_marker="future-child",
            id="future-child",
            account_id="future",
            valid_from=date(2026, 10, 20),
            loaded_at=datetime(2026, 10, 20),
        ),
    ]
    schema = {
        "row_marker": "string",
        "id": "string",
        "account_id": "string",
        "valid_from": "date",
        "valid_to": "date",
        "is_current": "boolean",
        "loaded_at": "timestamp",
    }
    return duckdb_backend.create_table("acr_history", ibis.memtable(rows, schema=schema))
