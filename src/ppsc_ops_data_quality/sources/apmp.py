"""Construct physical relations and explicit aliases from verified APMP inputs.

This adapter selects no organization, application, environment or local path.
It performs no discovery. File verification belongs to load_metadata_bundle.
"""

from __future__ import annotations

import json

import ibis
import ibis.expr.types as ir
import yaml
from ppsc_metadata.artifacts import MetadataBundle
from ppsc_metadata.lake import DatasetBinding, LakeBindings
from ppsc_metadata.schemas import athena_schema
from pydantic import BaseModel, ConfigDict, Field


class RelationLocation(BaseModel):
    """An explicitly selected physical location; it cannot redefine a schema."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    catalog: str = Field(min_length=1)
    database: str = Field(min_length=1)
    relation: str = Field(min_length=1)

    @property
    def identity(self) -> str:
        return f"{self.catalog}.{self.database}.{self.relation}"


def lake_bindings(inputs: MetadataBundle) -> LakeBindings:
    selected = [item for item in inputs.manifest.artifacts if item.role == "bindings"]
    if len(selected) != 1:
        raise ValueError("Select exactly one verified APMP bindings artifact")
    return LakeBindings.model_validate(yaml.safe_load(inputs.artifacts[selected[0].path]))


def dataset_binding(inputs: MetadataBundle, dataset_id: str) -> DatasetBinding:
    bindings = lake_bindings(inputs)
    if dataset_id not in bindings.datasets:
        raise ValueError(f"Unknown APMP dataset selection: {dataset_id}")
    return bindings.datasets[dataset_id]


def physical_schema(inputs: MetadataBundle, dataset_id: str) -> ibis.Schema:
    """Read only selected physical fields, retaining raw NULLs and type fidelity."""
    binding = dataset_binding(inputs, dataset_id)
    if binding.kind == "table":
        if not binding.ddl_path or binding.ddl_path not in inputs.artifacts:
            raise ValueError(f"Missing verified Athena definition for {dataset_id}")
        return athena_schema(inputs.artifacts[binding.ddl_path], fields=tuple(binding.columns))
    if not binding.schema_path or binding.schema_path not in inputs.artifacts:
        raise ValueError(f"Selected view {dataset_id} requires its verified output schema")
    if not binding.ddl_path or binding.ddl_path not in inputs.artifacts:
        raise ValueError(f"Selected view {dataset_id} requires its verified SQL definition")
    values = json.loads(inputs.artifacts[binding.schema_path])
    # Generated ordered fields are bound to one dataset alongside hashed view SQL.
    # A valid column list from another view is not interchangeable evidence.
    if not isinstance(values, dict) or values.get("dataset_id") != dataset_id:
        raise ValueError(f"Selected view output-schema dataset identity mismatch: {dataset_id}")
    pairs = values.get("fields")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError(
            f"Selected view output schema requires ordered generated fields: {dataset_id}"
        )
    if any(
        not isinstance(item, list)
        or len(item) != 2
        or not all(isinstance(value, str) and value for value in item)
        for item in pairs
    ):
        raise ValueError(
            f"Selected view schema fields require name/native-Ibis-type pairs: {dataset_id}"
        )
    names = [item[0].casefold() for item in pairs]
    if len(set(names)) != len(names):
        raise ValueError(
            f"Selected view output schema has duplicate/case-colliding fields: {dataset_id}"
        )
    schema = ibis.schema(pairs)
    missing = set(binding.columns).difference(schema.names)
    if missing:
        raise ValueError(f"Selected view fields absent from generated schema: {sorted(missing)}")
    return ibis.schema({name: schema[name] for name in binding.columns})


def logical_schema(inputs: MetadataBundle, dataset_id: str) -> ibis.Schema:
    binding = dataset_binding(inputs, dataset_id)
    schema = physical_schema(inputs, dataset_id)
    return ibis.schema({logical: schema[physical] for physical, logical in binding.columns.items()})


def source_relation(
    inputs: MetadataBundle,
    dataset_id: str,
    *,
    location: RelationLocation | None = None,
) -> ir.Table:
    """Build the real physical table before projecting physical-to-native aliases."""
    binding = dataset_binding(inputs, dataset_id)
    selected = location or RelationLocation(
        catalog=binding.catalog, database=binding.database, relation=binding.relation
    )
    physical = ibis.table(
        physical_schema(inputs, dataset_id),
        name=selected.relation,
        database=selected.database,
        catalog=selected.catalog,
    )
    return physical.select(
        **{logical: physical[physical_name] for physical_name, logical in binding.columns.items()}
    )


def source_fields(inputs: MetadataBundle) -> frozenset[str]:
    """Return explicitly selected native field identities, never inferred joins."""
    mapped = {
        f"{binding.native_object}.{logical}"
        for binding in lake_bindings(inputs).datasets.values()
        for logical in binding.columns.values()
        if logical not in binding.history_fields
    }
    native = {
        f"{field['EntityDefinition.QualifiedApiName']}.{field['FieldDefinition.QualifiedApiName']}"
        for field in inputs.source_catalog.get("fields", [])
        if "EntityDefinition.QualifiedApiName" in field
        and "FieldDefinition.QualifiedApiName" in field
    }
    # A separately selected native rollup artifact identifies its output field.
    # Workbook-derived rollups have no entry here and gain no native certification.
    return frozenset(mapped.intersection(native | set(inputs.rollups)))
