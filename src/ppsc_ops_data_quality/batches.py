"""Reusable Narwhals populations; no connections, execution, or GX rules."""

from datetime import date, datetime

import narwhals as nw


def state_at(table: nw.LazyFrame, effective_date: date | datetime) -> nw.LazyFrame:
    """Retain all rows effective in [valid_from, valid_to), including old records."""
    return table.filter(
        nw.col("valid_from") <= effective_date,
        (nw.col("valid_to") > effective_date) | nw.col("valid_to").is_null(),
    )


def current_state(table: nw.LazyFrame) -> nw.LazyFrame:
    """Use the current flag alone, retaining inconsistent dates for investigation."""
    return table.filter(nw.col("is_current"))


def account_reference_counts(acr_state: nw.LazyFrame, account_state: nw.LazyFrame) -> nw.LazyFrame:
    """Count exact eligible parents without multiplying or deduplicating children."""
    parents = (
        account_state.filter(~nw.col("id").is_null(), nw.col("id").str.strip_chars(" ") != "")
        .group_by("id")
        .agg(nw.len().alias("matching_account_versions"))
    )
    return acr_state.join(parents, left_on="account_id", right_on="id", how="left").with_columns(
        nw.col("matching_account_versions").fill_null(0)
    )
