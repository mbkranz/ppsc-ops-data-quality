"""Explicit backend discovery; runtime validation uses verified APMP schemas."""

from collections.abc import Mapping

import ibis.expr.types as ir

from ppsc_ops_data_quality.sources.apmp import RelationLocation


def bind_history_tables(
    backend,
    *,
    bindings: dict,
    locations: Mapping[str, RelationLocation],
) -> dict[str, ir.Table]:
    """Read the supplied physical relations and execute their declared aliases.

    This explicit discovery helper makes no claim about compatibility or data
    stability. The Athena validation entry point runs catalog preflight separately.
    """
    if set(locations) != set(bindings):
        raise ValueError("Locations must match the selected APMP dataset IDs")
    result = {}
    for dataset_id, binding in bindings.items():
        location = locations[dataset_id]
        physical = backend.table(location.relation, database=(location.catalog, location.database))
        result[binding["native_object"]] = physical.select(
            **{logical: physical[name] for name, logical in binding["columns"].items()}
        )
    return result
