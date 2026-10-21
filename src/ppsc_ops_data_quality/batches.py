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


def account_reference_counts(acr_state: str, account_state: str) -> str:
    """Preserve child grain and count exact, nonblank parent matches."""
    return f"""
        WITH accounts AS ({account_state}), children AS ({acr_state}),
        parents AS (
            SELECT id, COUNT(*) AS matching_account_versions
            FROM accounts WHERE id IS NOT NULL AND TRIM(id) <> '' GROUP BY id
        )
        SELECT children.*, COALESCE(parents.matching_account_versions, 0)
            AS matching_account_versions
        FROM children LEFT JOIN parents ON children.account_id = parents.id
    """
