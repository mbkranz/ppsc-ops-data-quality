"""Provisional Account schemas derived from the pinned APMP handoff."""

from .inputs import provisional_schema

ACCOUNT_VALIDATION_INPUT = provisional_schema("Account", include_history=False)
ACCOUNT_HISTORY_VALIDATION_INPUT = provisional_schema("Account", include_history=True)
ACCOUNT_SNAPSHOT_VALIDATION_INPUT = ACCOUNT_HISTORY_VALIDATION_INPUT
