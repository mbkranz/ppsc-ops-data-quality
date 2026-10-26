"""Read APMP-generated table data and compose physical-to-logical Ibis aliases.

ODCS authoring, parsing and Athena DDL interpretation belong to the lake project.
This consumer uses generated native Ibis schemas; it acquires no source metadata.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import ibis
import ibis.expr.types as ir
from pydantic import BaseModel, ConfigDict, Field


class RelationLocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    catalog: str = Field(min_length=1)
    database: str = Field(min_length=1)
    relation: str = Field(min_length=1)

    @property
    def identity(self) -> str:
        return f"{self.catalog}.{self.database}.{self.relation}"


def load_inputs(directory: Path) -> dict:
    """Load the selected generated product; Git/DVC and the release pin its files."""
    payloads = {
        name: (directory / f"{name}.json").read_bytes()
        for name in ("tables", "flow", "source_catalog", "rollups")
        if (directory / f"{name}.json").exists()
    }
    inputs = json.loads(payloads["tables"])
    inputs.update(
        {
            name: json.loads(payloads[name]) if name in payloads else {}
            for name in ("flow", "source_catalog", "rollups")
        }
    )
    inputs["inputs_sha256"] = sha256(
        b"".join(name.encode() + b"\0" + content for name, content in sorted(payloads.items()))
    ).hexdigest()
    inputs["flow_sha256"] = sha256(payloads.get("flow", b"")).hexdigest()
    for dataset_id in inputs["tables"]:
        physical_schema(inputs, dataset_id)
    return inputs


def dataset_binding(inputs: dict, dataset_id: str) -> dict:
    if dataset_id not in inputs["tables"]:
        raise ValueError(f"Unknown APMP dataset selection: {dataset_id}")
    return inputs["tables"][dataset_id]


def physical_schema(inputs: dict, dataset_id: str) -> ibis.Schema:
    table = dataset_binding(inputs, dataset_id)
    schema = ibis.schema(table["fields"])
    columns = table["columns"]
    for names in (schema.names, tuple(columns.values())):
        if not names or len({name.casefold() for name in names}) != len(names):
            raise ValueError(f"Duplicate/case-colliding generated schema fields: {dataset_id}")
    if set(columns) != set(schema.names):
        raise ValueError(f"Generated schema/mapping fields disagree: {dataset_id}")
    return schema


def logical_schema(inputs: dict, dataset_id: str) -> ibis.Schema:
    table = dataset_binding(inputs, dataset_id)
    schema = physical_schema(inputs, dataset_id)
    return ibis.schema(
        {logical: schema[physical] for physical, logical in table["columns"].items()}
    )


def source_relation(
    inputs: dict, dataset_id: str, *, location: RelationLocation | None = None
) -> ir.Table:
    table = dataset_binding(inputs, dataset_id)
    selected = location or RelationLocation(
        **{name: table[name] for name in ("catalog", "database", "relation")}
    )
    physical = ibis.table(
        physical_schema(inputs, dataset_id),
        name=selected.relation,
        database=selected.database,
        catalog=selected.catalog,
    )
    return physical.select(
        **{logical: physical[name] for name, logical in table["columns"].items()}
    )


def source_fields(inputs: dict) -> frozenset[str]:
    native = {
        f"{field['EntityDefinition.QualifiedApiName']}.{field['FieldDefinition.QualifiedApiName']}"
        for field in inputs["source_catalog"].get("fields", [])
        if "EntityDefinition.QualifiedApiName" in field
        and "FieldDefinition.QualifiedApiName" in field
    }
    mapped = {
        f"{table['native_object']}.{name}"
        for table in inputs["tables"].values()
        for name in table["columns"].values()
        if name not in table["history_fields"]
    }
    return frozenset(mapped.intersection(native | set(inputs.get("rollups", {}))))
