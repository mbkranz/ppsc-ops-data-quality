"""Shared SCD2 metadata for the timestamp-grain query input profile.

Provenance: ppsc-athena-gx-sample/batches.py, HISTORY_COLUMNS, October 17, 2026:
valid_from, valid_to, is_current, loaded_at. That sample used DATE validity bounds;
the event-query examples require timestamp-grain bounds to represent intra-day
BEFORE/execution/AFTER states. Timestamp validity here is an explicit profile,
not a claim that the deployed history tables have this physical schema.

All fields are nullable to retain invalid data for validation. Time-zone and
precision are unspecified until the actual catalog binding is inspected. For
DATE-grain history, override both bounds with 'date' in the object history schema.
No partition keys, object discriminators or tombstone fields are invented here.
"""

import ibis

HISTORY_METADATA = ibis.schema(
    {
        "valid_from": "timestamp",
        "valid_to": "timestamp",
        "is_current": "boolean",
        "loaded_at": "timestamp",
    }
)
