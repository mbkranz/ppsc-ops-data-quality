"""Provisional Contact schemas derived from the pinned APMP handoff."""

from .inputs import provisional_schema

CONTACT_VALIDATION_INPUT = provisional_schema("Contact", include_history=False)
CONTACT_HISTORY_VALIDATION_INPUT = provisional_schema("Contact", include_history=True)
CONTACT_SNAPSHOT_VALIDATION_INPUT = CONTACT_HISTORY_VALIDATION_INPUT
