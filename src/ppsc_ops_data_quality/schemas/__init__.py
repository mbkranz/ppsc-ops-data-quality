"""Ibis schemas for query inputs and validation-report projections.

Source constants are complete for their named validation-input projections;
physical Athena schemas have not been inspected. Derived query/view schemas
are exposed by schemas.derived and inferred from the actual expression builders.
Arrow is an interchange format; lineage remains in its separate mapping module.
"""

from .account import (
    ACCOUNT_HISTORY_VALIDATION_INPUT,
    ACCOUNT_SNAPSHOT_VALIDATION_INPUT,
    ACCOUNT_VALIDATION_INPUT,
)
from .contact import (
    CONTACT_HISTORY_VALIDATION_INPUT,
    CONTACT_SNAPSHOT_VALIDATION_INPUT,
    CONTACT_VALIDATION_INPUT,
)
from .history import HISTORY_METADATA
from .survey_results import (
    SURVEY_RESULT_HISTORY_VALIDATION_INPUT,
    SURVEY_RESULT_SNAPSHOT_VALIDATION_INPUT,
    SURVEY_RESULT_VALIDATION_INPUT,
)
from .tables import history_tables
from .validation_reports import EXPECTATION_RUN_RESULTS, VALIDATION_RUN_RESULTS

__all__ = [
    "ACCOUNT_VALIDATION_INPUT",
    "ACCOUNT_HISTORY_VALIDATION_INPUT",
    "ACCOUNT_SNAPSHOT_VALIDATION_INPUT",
    "CONTACT_VALIDATION_INPUT",
    "CONTACT_HISTORY_VALIDATION_INPUT",
    "CONTACT_SNAPSHOT_VALIDATION_INPUT",
    "SURVEY_RESULT_VALIDATION_INPUT",
    "SURVEY_RESULT_HISTORY_VALIDATION_INPUT",
    "SURVEY_RESULT_SNAPSHOT_VALIDATION_INPUT",
    "HISTORY_METADATA",
    "history_tables",
    "EXPECTATION_RUN_RESULTS",
    "VALIDATION_RUN_RESULTS",
]
