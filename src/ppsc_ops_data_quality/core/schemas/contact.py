"""ODCS-derived Contact validation input; raw nulls remain observable.

The checked-in contract is provisional. Physical Athena bindings and history
semantics require local verification; this module executes no data.
"""

import ibis
from ppsc_metadata.schemas import ibis_schema

from .contracts import validation_input_contract
from .history import HISTORY_METADATA

CONTACT_VALIDATION_INPUT = ibis_schema(validation_input_contract(), "Contact")
CONTACT_HISTORY_VALIDATION_INPUT = ibis.schema(
    {**CONTACT_VALIDATION_INPUT.fields, **HISTORY_METADATA.fields}
)
CONTACT_SNAPSHOT_VALIDATION_INPUT = CONTACT_HISTORY_VALIDATION_INPUT
