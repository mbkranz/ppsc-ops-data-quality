"""Ordered Ibis assignments and independent source-bound presence predicates."""

from collections.abc import Mapping, Sequence

import ibis
import ibis.expr.types as ir


def conditional_values(
    before: Mapping[str, ir.Value],
    assignments: Sequence[tuple[ir.BooleanValue, Mapping[str, ir.Value]]],
) -> dict[str, ir.Value]:
    """Retain BEFORE when unassigned; an assigned NULL remains NULL."""
    result = {}
    for field, previous in before.items():
        branches = [(guard, values[field]) for guard, values in assignments if field in values]
        result[field] = (ibis.cases(*branches, else_=previous) if branches else previous).name(
            field
        )
    return result


def presence_requirements(
    *,
    required: Mapping[str, ir.BooleanValue] | None = None,
    must_be_null: Mapping[str, ir.BooleanValue] | None = None,
) -> dict[str, ir.BooleanValue]:
    """A false required predicate does not invent a nullness requirement."""
    result = {}
    for values, suffix in ((required, "required"), (must_be_null, "must_be_null")):
        for field, predicate in (values or {}).items():
            if not field or not isinstance(predicate, ir.BooleanValue):
                raise ValueError("Presence requirements need named Boolean expressions")
            name = f"expected__{field}_{suffix}"
            result[name] = predicate.name(name)
    return result
