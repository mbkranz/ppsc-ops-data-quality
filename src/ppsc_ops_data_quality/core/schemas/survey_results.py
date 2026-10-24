"""ODCS-derived Survey_Result__c validation input; raw nulls remain observable.

The checked-in contract is provisional. Physical Athena bindings and history
semantics require local verification; this module executes no data.
"""

import ibis
from ppsc_metadata.schemas import ibis_schema

from .contracts import validation_input_contract
from .history import HISTORY_METADATA

SURVEY_RESULT_VALIDATION_INPUT = ibis_schema(validation_input_contract(), "Survey_Result__c")
SURVEY_RESULT_HISTORY_VALIDATION_INPUT = ibis.schema(
    {**SURVEY_RESULT_VALIDATION_INPUT.fields, **HISTORY_METADATA.fields}
)
SURVEY_RESULT_SNAPSHOT_VALIDATION_INPUT = SURVEY_RESULT_HISTORY_VALIDATION_INPUT
