"""Domain-independent Ibis schemas for validation-input projections.

Source constants are complete for their named validation-input projections;
physical Athena schemas have not been inspected. Derived query/view schemas
are exposed by account_to_survey_results.schemas and inferred from the actual expression builders.
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
]
