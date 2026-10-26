"""Ordered relational bindings; source field provenance does not imply a join."""

from ppsc_metadata.lake import LakeBindings, RelationshipBinding

ForeignKey = RelationshipBinding


def normalize_foreign_keys(bindings: LakeBindings) -> tuple[RelationshipBinding, ...]:
    """Validate explicit relationships without ODCS property-reference normalization."""
    return LakeBindings.model_validate(bindings.model_dump()).relationships
