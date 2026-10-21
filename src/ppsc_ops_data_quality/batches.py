"""Construct validation populations without reading data or executing checks."""

from datetime import date, datetime

import ibis.expr.types as ir


def state_at(table: ir.Table, effective_date: date | datetime) -> ir.Table:
    """Select every version effective in the half-open interval [from, to).

    An open-ended version has a null ``valid_to``. The selection deliberately
    ignores ``is_current`` and ``loaded_at`` so unchanged older versions remain
    eligible. Physical snapshot selection belongs to the source table.
    """
    return table.filter(
        table.valid_from <= effective_date,
        (table.valid_to > effective_date) | table.valid_to.isnull(),
    )


def current_state(table: ir.Table) -> ir.Table:
    """Select versions explicitly flagged current, retaining flag inconsistencies.

    False and null flags are excluded. Additional date predicates could conceal
    an inconsistent flag; checking those inconsistencies requires the history.
    """
    return table.filter(table.is_current)


def account_reference_counts(acr_state: ir.Table, account_state: ir.Table) -> ir.Table:
    """Keep each ACR row and count its exact matches in the selected Account state.

    Null and blank Account IDs are ineligible parents. Trimming is used only to
    identify blank IDs: the join preserves the original case and whitespace of
    both identifiers. Grouping parents before the left join retains duplicate
    parent counts without multiplying child rows.
    """
    eligible_accounts = account_state.filter(
        account_state.id.notnull(),
        account_state.id.strip() != "",
    )
    parent_counts = eligible_accounts.group_by(parent_id=eligible_accounts.id).aggregate(
        matching_account_versions=eligible_accounts.count(),
    )
    joined = acr_state.left_join(
        parent_counts,
        acr_state.account_id == parent_counts.parent_id,
    )
    return joined.select(
        acr_state,
        matching_account_versions=parent_counts.matching_account_versions.fill_null(0),
    )
