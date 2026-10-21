"""Shared SQL populations; check predicates belong in gx/<subject>/*.sql."""

from datetime import date, datetime


def state_at(table: str, effective_date: date | datetime) -> str:
    """Select the full state in [valid_from, valid_to), retaining old records."""
    kind = "TIMESTAMP" if isinstance(effective_date, datetime) else "DATE"
    value = effective_date.isoformat(sep=" ") if kind == "TIMESTAMP" else effective_date.isoformat()
    boundary = f"{kind} '{value}'"
    return (
        f"SELECT * FROM ({table}) AS history WHERE valid_from <= {boundary} "
        f"AND (valid_to > {boundary} OR valid_to IS NULL)"
    )


def current_state(table: str) -> str:
    """Use the flag alone; do not conceal inconsistent dates."""
    return f"SELECT * FROM ({table}) AS history WHERE is_current = TRUE"


def survey_result_account_counts(surveys: str, contacts: str, accounts: str) -> str:
    """Count both reference hops without multiplying or deduplicating survey rows.

    Aggregate Accounts by exact ID before joining Contacts, then aggregate Contacts
    by exact ID before joining surveys. Account findings apply only when one
    Contact resolves; duplicate Contacts remain their own integrity finding.
    """
    return f"""SELECT * FROM (
        WITH accounts AS ({accounts}), contacts AS ({contacts}), surveys AS ({surveys}),
        account_counts AS (
            SELECT id, COUNT(*) AS matching_account_versions
            FROM accounts WHERE id IS NOT NULL AND TRIM(id) <> '' GROUP BY id
        ),
        contact_counts AS (
            SELECT contacts.id, COUNT(*) AS matching_contact_versions,
                SUM(CASE WHEN contacts.account_id IS NULL OR TRIM(contacts.account_id) = ''
                    THEN 1 ELSE 0 END) AS missing_account_references,
                SUM(COALESCE(account_counts.matching_account_versions, 0))
                    AS matching_account_versions
            FROM contacts LEFT JOIN account_counts ON contacts.account_id = account_counts.id
            WHERE contacts.id IS NOT NULL AND TRIM(contacts.id) <> ''
            GROUP BY contacts.id
        )
        SELECT surveys.*,
            COALESCE(contact_counts.matching_contact_versions, 0) AS matching_contact_versions,
            COALESCE(contact_counts.missing_account_references, 0) AS missing_account_references,
            COALESCE(contact_counts.matching_account_versions, 0) AS matching_account_versions
        FROM surveys LEFT JOIN contact_counts ON surveys.participant_id = contact_counts.id
        ) AS survey_result_to_account
    """
