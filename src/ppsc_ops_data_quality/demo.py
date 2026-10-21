"""Synthetic history for an offline Flow event and settled Account rollups."""

from datetime import date, datetime

import ibis
import pyarrow as pa

from ppsc_ops_data_quality.queries import (
    ROLLUP_ACCOUNT_FIELDS,
    flow_account_query,
    rollup_account_query,
)
from ppsc_ops_data_quality.schemas import (
    ACCOUNT_HISTORY_VALIDATION_INPUT,
    CONTACT_HISTORY_VALIDATION_INPUT,
    SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
)

EVENT_ID = "synthetic_basics_event"
BEFORE_AT = datetime(2026, 10, 21, 11, 59, 59)
EXECUTION_AT = datetime(2026, 10, 21, 12)
AFTER_AT = datetime(2026, 10, 21, 12, 5)
FLOW_RUN_DATE = date(2026, 10, 21)


def comparisons(history):
    """Compose examples with independently declared BEFORE and AFTER boundaries."""
    return {
        "flow": flow_account_query(
            history,
            survey_result_id=EVENT_ID,
            account_before_at=BEFORE_AT,
            execution_at=EXECUTION_AT,
            account_after_at=AFTER_AT,
            flow_run_date=FLOW_RUN_DATE,
        ),
        "rollups": rollup_account_query(history, as_of=AFTER_AT),
    }


def history_tables(backend):
    """Create small DuckDB history tables; observed AFTER values are explicit.

    One completed Basics survey updates the Account timestamp and count. Expected
    values are computed by the existing query builders, not used to construct the
    observed rows. All identifiers are synthetic. No files or AWS services are read.
    """
    account = {field: None for field in ACCOUNT_HISTORY_VALIDATION_INPUT}
    account.update(
        Id="synthetic_account",
        PersonContactId="synthetic_contact",
        IsPersonAccount=True,
        valid_from=datetime(2026, 1, 1),
        valid_to=AFTER_AT,
        is_current=False,
        loaded_at=AFTER_AT,
    )
    account.update({field: 0 for field in ROLLUP_ACCOUNT_FIELDS})
    after = dict(
        account,
        valid_from=AFTER_AT,
        valid_to=None,
        is_current=True,
        Basics_Date_Time__c=EXECUTION_AT,
        PP1_Basics_Survey_Complete__pc=1,
    )
    contact = {
        "Id": "synthetic_contact",
        "AccountId": "synthetic_account",
        "Birthdate": date(2000, 1, 1),
        "valid_from": datetime(2026, 1, 1),
        "valid_to": None,
        "is_current": True,
        "loaded_at": AFTER_AT,
    }
    survey = {field: None for field in SURVEY_RESULT_HISTORY_VALIDATION_INPUT}
    survey.update(
        Id=EVENT_ID,
        Participant__c="synthetic_contact",
        Survey_Index_Number__c="2001",
        Completion_Status__c="Complete",
        Consent_Status__c="Yes",
        Consent_Revoked__c=False,
        Completion_Status_Timestamp__c=EXECUTION_AT,
        valid_from=EXECUTION_AT,
        valid_to=None,
        is_current=True,
        loaded_at=AFTER_AT,
    )
    history = {}
    for name, schema, rows in (
        ("Account", ACCOUNT_HISTORY_VALIDATION_INPUT, [account, after]),
        ("Contact", CONTACT_HISTORY_VALIDATION_INPUT, [contact]),
        ("Survey_Result__c", SURVEY_RESULT_HISTORY_VALIDATION_INPUT, [survey]),
    ):
        table = pa.Table.from_pylist(rows, schema=schema.to_pyarrow())
        history[name] = backend.create_table(name + "_history", ibis.memtable(table))
    return history
