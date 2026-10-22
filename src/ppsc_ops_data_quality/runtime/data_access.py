"""Catalog access kept outside pure query construction."""

import ibis.expr.types as ir


def bind_history_tables(
    backend,
    *,
    account_database: str,
    contact_database: str,
    survey_result_database: str,
) -> dict[str, ir.Table]:
    """Bind each object's Athena history table using its actual catalog schema.

    Map lowercase columns to Salesforce API names upstream when needed. For a
    combined-history table supply three explicitly object-scoped relations instead.
    """
    return {
        "Account": backend.table("history", database=account_database),
        "Contact": backend.table("history", database=contact_database),
        "Survey_Result__c": backend.table("history", database=survey_result_database),
    }
