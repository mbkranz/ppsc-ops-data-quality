"""Bind explicit history schemas to Athena names without a live backend."""

import ibis
import ibis.expr.types as ir

from ppsc_ops_data_quality.core.schemas.account import ACCOUNT_HISTORY_VALIDATION_INPUT
from ppsc_ops_data_quality.core.schemas.contact import CONTACT_HISTORY_VALIDATION_INPUT
from ppsc_ops_data_quality.core.schemas.survey_results import SURVEY_RESULT_HISTORY_VALIDATION_INPUT


def history_tables(
    *,
    account_database: str,
    contact_database: str,
    survey_result_database: str,
    account_schema: ibis.Schema = ACCOUNT_HISTORY_VALIDATION_INPUT,
    contact_schema: ibis.Schema = CONTACT_HISTORY_VALIDATION_INPUT,
    survey_result_schema: ibis.Schema = SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
) -> dict[str, ir.Table]:
    """Return unbound history relations used directly by queries.py builders.

    Defaults are documented validation-input profiles, not discovered physical
    schemas. Supply catalog-verified Ibis schemas to preserve actual precision,
    time zones and additional columns. Convert Arrow schemas with
    ibis.Schema.from_pyarrow() before passing them. No database calls, casts or
    renaming occur here. To discover types through an existing backend, use
    runtime.data_access.bind_history_tables() instead.
    """
    return {
        "Account": ibis.table(account_schema, name="history", database=account_database),
        "Contact": ibis.table(contact_schema, name="history", database=contact_database),
        "Survey_Result__c": ibis.table(
            survey_result_schema, name="history", database=survey_result_database
        ),
    }
