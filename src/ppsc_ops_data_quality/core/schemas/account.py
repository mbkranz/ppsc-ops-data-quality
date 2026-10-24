"""ODCS-derived Account validation input; raw nulls remain observable.

The checked-in contract is provisional. Physical Athena bindings and history
semantics require local verification; this module executes no data.
"""

import ibis
from ppsc_metadata.schemas import ibis_schema

from .contracts import validation_input_contract
from .history import HISTORY_METADATA

ACCOUNT_VALIDATION_INPUT = ibis_schema(validation_input_contract(), "Account")
ACCOUNT_HISTORY_VALIDATION_INPUT = ibis.schema(
    {**ACCOUNT_VALIDATION_INPUT.fields, **HISTORY_METADATA.fields}
)
ACCOUNT_SNAPSHOT_VALIDATION_INPUT = ACCOUNT_HISTORY_VALIDATION_INPUT
