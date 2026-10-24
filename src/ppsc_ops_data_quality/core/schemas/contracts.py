"""Load the provisional logical input contract; physical bindings stay explicit."""

from functools import cache
from importlib.resources import files
from pathlib import Path

from open_data_contract_standard.model import OpenDataContractStandard
from ppsc_metadata.contracts import (
    internal_reference,
    load_contract,
    property_paths,
    property_references,
    validate_contract,
)
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ForeignKey(BaseModel):
    """One ordered relational key; provenance field links have a separate meaning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_object: str = Field(min_length=1)
    source_fields: tuple[str, ...] = Field(min_length=1)
    target_object: str = Field(min_length=1)
    target_fields: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_pairs(self) -> "ForeignKey":
        if len(self.source_fields) != len(self.target_fields):
            raise ValueError("Foreign key source and target must have equal key lengths")
        for fields in (self.source_fields, self.target_fields):
            if len(set(fields)) != len(fields) or any(not field.strip() for field in fields):
                raise ValueError("Foreign key fields must be nonempty and unique")
        return self


def normalize_foreign_keys(contract: OpenDataContractStandard) -> tuple[ForeignKey, ...]:
    """Resolve object/property declarations without inventing joins or fetching references.

    Accept standard qualified property names. Explicit composite
    keys retain ordered pairs. Equivalent declarations collapse once; conflicting
    mappings of the same source key and unsupported relationships fail here.
    """
    contract = validate_contract(contract)
    references = property_references(contract)

    def resolve(value: str | list[str] | None) -> tuple[str, ...]:
        values = [value] if isinstance(value, str) else value
        if not values:
            raise ValueError("Foreign key requires explicit source and target properties")
        resolved = []
        for reference in values:
            normalized = internal_reference(reference)
            if normalized is None or normalized not in references:
                raise ValueError(f"Unbound foreign key property: {reference}")
            resolved.append(references[normalized])
        return tuple(resolved)

    result: dict[tuple[str, frozenset[str]], ForeignKey] = {}
    for obj in contract.schema_ or []:
        declarations = [(None, obj.relationships or [])]
        declarations.extend(
            (f"{obj.name}.{'.'.join(path)}", prop.relationships or [])
            for path, prop in property_paths(obj)
        )
        for owner, relationships in declarations:
            relationship_ids: set[str] = set()
            for relationship in relationships:
                if relationship.type not in {None, "foreignKey"}:
                    raise ValueError(f"Unsupported ODCS relationship type: {relationship.type!r}")
                sources = resolve(relationship.from_ if relationship.from_ is not None else owner)
                targets = resolve(relationship.to)
                if any(source.partition(".")[0] != obj.name for source in sources):
                    raise ValueError("Foreign key source must belong to its declaring object")
                if owner is not None and owner not in sources:
                    raise ValueError("Property foreign key contradicts its declaring property")
                target_objects = {target.partition(".")[0] for target in targets}
                if len(target_objects) != 1:
                    raise ValueError("Foreign key target fields must belong to one object")
                key = ForeignKey(
                    source_object=obj.name,
                    source_fields=tuple(source.partition(".")[2] for source in sources),
                    target_object=target_objects.pop(),
                    target_fields=tuple(target.partition(".")[2] for target in targets),
                )
                signature = (key.source_object, frozenset(key.source_fields))
                previous = result.get(signature)
                if previous is not None:
                    if previous.target_object != key.target_object or dict(
                        zip(previous.source_fields, previous.target_fields, strict=True)
                    ) != dict(zip(key.source_fields, key.target_fields, strict=True)):
                        raise ValueError("Contradictory duplicate foreign key declarations")
                if relationship.id is not None:
                    if relationship.id in relationship_ids:
                        raise ValueError(f"Repeated foreign key id: {relationship.id}")
                    relationship_ids.add(relationship.id)
                result.setdefault(signature, key)
    return tuple(result.values())


@cache
def validation_input_contract() -> OpenDataContractStandard:
    return load_contract(Path(str(files(__package__).joinpath("validation-inputs.odcs.yaml"))))
