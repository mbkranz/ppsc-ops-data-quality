"""Plain Ibis expressions for business-effective SCD2 history snapshots.

Provenance: ppsc-athena-gx-sample/batches.py (October 17, 2026),
state_predicate()/state_sql(): current means is_current = TRUE; historical state
uses [valid_from, valid_to). The original sample described this as a proposed ETL
contract. Confirm the interval and deletion semantics against the producer.

All matching versions survive, including overlaps. This function builds a query;
it creates no views, materialized tables or Iceberg physical time-travel binding.
"""

from datetime import UTC, date, datetime, time

import ibis
import ibis.expr.types as ir


def snapshot(
    history: ir.Table,
    *,
    as_of: date | datetime | None = None,
    valid_from: str = "valid_from",
    valid_to: str = "valid_to",
    is_current: str = "is_current",
) -> ir.Table:
    """Return the SCD2 snapshot as a composable, schema-preserving Ibis table.

    Lineage: translates the prior state_predicate() into Ibis without changing
    its half-open interval semantics. as_of=None selects is_current == TRUE;
    otherwise valid_from <= as_of AND (valid_to > as_of OR valid_to IS NULL).
    All source columns and all matching versions survive. NULL bounds/flags
    follow SQL's three-valued logic. A NULL valid_from never matches as_of.

    Date history requires a date. Timestamp history accepts a datetime, or a
    date interpreted at midnight in the column's time zone. Naive timestamps
    require naive datetimes; zoned timestamps require aware datetimes. Values
    are never truncated to dates. Column names can be mapped explicitly.

    This is business-effective state, not an immutable materialized snapshot.
    Late corrections to history can change results even with a fixed as_of.
    Deletion/tombstone semantics remain those of the history producer.
    """
    schema = history.schema()
    if as_of is None:
        if is_current not in schema or not schema[is_current].is_boolean():
            raise ValueError(f"Current history requires boolean {is_current!r}")
        query = history.filter(history[is_current] == True)
    else:
        if not isinstance(as_of, date):
            raise TypeError("as_of must be a date, datetime, or None")
        if valid_from not in schema or valid_to not in schema:
            raise ValueError(
                "History requires valid_from and valid_to columns (or explicit mappings)"
            )
        dtype = schema[valid_from]
        if dtype != schema[valid_to] or not (dtype.is_date() or dtype.is_timestamp()):
            raise ValueError("Validity bounds must have identical date or timestamp types")
        if dtype.is_date():
            if isinstance(as_of, datetime):
                raise TypeError("Date history requires date as_of; refusing to discard time")
            point = ibis.literal(as_of, type=dtype)
        else:
            if not isinstance(as_of, datetime):
                # Ibis interprets a naive literal in the requested column time zone.
                as_of = datetime.combine(as_of, time.min)
                if dtype.timezone:
                    from zoneinfo import ZoneInfo

                    as_of = as_of.replace(tzinfo=ZoneInfo(dtype.timezone))
            aware = as_of.tzinfo is not None and as_of.utcoffset() is not None
            if bool(dtype.timezone) != aware:
                raise ValueError("as_of timezone awareness must match the timestamp columns")
            if aware:
                as_of = as_of.astimezone(UTC)
            point = ibis.literal(as_of, type=dtype)
        query = history.filter(
            (history[valid_from] <= point)
            & ((history[valid_to] > point) | history[valid_to].isnull())
        )
    return query
