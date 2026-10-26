"""Build explicitly selected APMP history relations without a live backend."""

from collections.abc import Mapping

import ibis.expr.types as ir
from ppsc_metadata.artifacts import MetadataBundle

from ppsc_ops_data_quality.sources.apmp import RelationLocation, lake_bindings, source_relation


def history_tables(
    *,
    inputs: MetadataBundle,
    locations: Mapping[str, RelationLocation] | None = None,
) -> dict[str, ir.Table]:
    """Project real physical names through the supplied reviewed or provisional input set.

    No schema, database or relation is invented here. Offline examples deliberately
    supply their pinned fixture bundle. Runtime separately verifies the exact
    selection, live catalog compatibility and chosen data versions before GX.
    """
    bindings = lake_bindings(inputs)
    if locations is not None and set(locations) != set(bindings.datasets):
        raise ValueError("Locations must match the selected APMP dataset IDs")
    return {
        binding.native_object: source_relation(
            inputs, dataset_id, location=locations[dataset_id] if locations is not None else None
        )
        for dataset_id, binding in bindings.datasets.items()
    }
