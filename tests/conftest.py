"""Synthetic histories with observable version and relationship edge cases."""

from datetime import date, datetime

import duckdb
import pyarrow as pa
import pytest


@pytest.fixture
def duckdb_backend():
    backend = duckdb.connect()
    yield backend
    backend.close()


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
        "row_marker": pa.string(),
        "id": pa.string(),
        "valid_from": pa.date32(),
        "valid_to": pa.date32(),
        "is_current": pa.bool_(),
        "loaded_at": pa.timestamp("us"),
    }
    data = pa.Table.from_pylist(rows, schema=pa.schema(schema))
    duckdb_backend.from_arrow(data).create_view("account_history")
    return "SELECT * FROM account_history"


@pytest.fixture
def contact_history(duckdb_backend):
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
    rows.extend(
        [
            dict(
                base,
                row_marker="closed-contact",
                id="closed-contact",
                account_id="old",
                valid_to=date(2026, 10, 14),
                is_current=False,
            ),
            dict(base, row_marker="null-contact-id", id=None, account_id="old"),
            dict(base, row_marker="blank-contact-id", id="  ", account_id="old"),
            dict(base, row_marker="case-contact", id="ContactCase", account_id="old"),
            dict(base, row_marker="padded-contact", id="exact-contact ", account_id="old"),
        ]
    )
    schema = {
        "row_marker": pa.string(),
        "id": pa.string(),
        "account_id": pa.string(),
        "valid_from": pa.date32(),
        "valid_to": pa.date32(),
        "is_current": pa.bool_(),
        "loaded_at": pa.timestamp("us"),
    }
    data = pa.Table.from_pylist(rows, schema=pa.schema(schema))
    duckdb_backend.from_arrow(data).create_view("contact_history")
    return "SELECT * FROM contact_history"


@pytest.fixture
def survey_history(duckdb_backend):
    base = {
        "valid_from": date(2026, 6, 25),
        "valid_to": None,
        "is_current": True,
        "loaded_at": datetime(2026, 6, 26),
    }
    references = {
        "valid-old-parent": "child-old",
        "another-survey-same-account": "child-old",
        "missing-account": "child-missing",
        "null-account-reference": "child-null",
        "empty-account-reference": "child-empty",
        "blank-account-reference": "child-blank",
        "duplicate-account": "child-ambiguous",
        "closed-account": "child-closed",
        "case-account-mismatch": "child-case-mismatch",
        "case-account-exact": "child-case-exact",
        "spacing-account-mismatch": "child-spacing-mismatch",
        "spacing-account-exact": "child-spacing-exact",
        "missing-participant": "absent",
        "null-participant": None,
        "empty-participant": "",
        "blank-participant": "  ",
        "duplicate-participant": "repeated-child",
        "closed-participant": "closed-contact",
        "case-participant-mismatch": "contactcase",
        "case-participant-exact": "ContactCase",
        "spacing-participant-mismatch": "exact-contact",
        "spacing-participant-exact": "exact-contact ",
        "no-direct-account-shortcut": "old",
    }
    rows = [
        dict(base, row_marker=marker, id=marker, participant_id=reference)
        for marker, reference in references.items()
    ]
    rows += [
        dict(
            base,
            row_marker="survey-transition-old",
            id="transition-survey",
            participant_id="child-transition",
            valid_to=date(2026, 10, 15),
            is_current=False,
        ),
        dict(
            base,
            row_marker="survey-transition-new",
            id="transition-survey",
            participant_id="child-transition",
            valid_from=date(2026, 10, 15),
        ),
        dict(
            base,
            row_marker="future-survey",
            id="future-survey",
            participant_id="future-child",
            valid_from=date(2026, 10, 20),
        ),
    ]
    schema = pa.schema(
        {
            "row_marker": pa.string(),
            "id": pa.string(),
            "participant_id": pa.string(),
            "valid_from": pa.date32(),
            "valid_to": pa.date32(),
            "is_current": pa.bool_(),
            "loaded_at": pa.timestamp("us"),
        }
    )
    data = pa.Table.from_pylist(rows, schema=schema)
    duckdb_backend.from_arrow(data).create_view("survey_history")
    return "SELECT * FROM survey_history"
