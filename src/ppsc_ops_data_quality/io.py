"""Explicit lake definition and native capture input operations."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import sqlglot
import yaml
from pydantic import BaseModel, ConfigDict, Field
from sqlglot import exp


class ConfigurationLoader(yaml.SafeLoader):
    """Safe YAML with explicit, unique mapping keys (including merged keys)."""


def construct_mapping(loader: ConfigurationLoader, node: yaml.MappingNode) -> dict:
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in mapping:
            raise ValueError(f"Duplicate YAML configuration key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=True)
    return mapping


ConfigurationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
)


def load_yaml(path: Path) -> dict:
    """Load one mapping, preserving YAML date/datetime values and quoted IDs."""
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=ConfigurationLoader)
    if not isinstance(value, dict):
        raise ValueError("Configuration must be a YAML mapping")
    return value


class RelationLocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    catalog: str = Field(min_length=1)
    database: str = Field(min_length=1)
    relation: str = Field(min_length=1)

    @property
    def identity(self) -> str:
        return f"{self.catalog}.{self.database}.{self.relation}"


class ExportReceipt(BaseModel):
    path: Path
    sha256: str
    source: str


def read_ddl(path: Path) -> exp.Create:
    """Read exactly one CREATE TABLE definition; never execute it."""
    statements = sqlglot.parse(path.read_text(), read="athena")
    if len(statements) != 1 or not isinstance(statements[0], exp.Create):
        raise ValueError("Supply one CREATE TABLE DDL")
    definition = statements[0]
    if definition.kind != "TABLE" or not isinstance(definition.this, exp.Schema):
        raise ValueError("DDL must declare an explicit table column schema")
    columns = definition.this.expressions
    names = [c.name.casefold() for c in columns if isinstance(c, exp.ColumnDef)]
    if len(names) != len(columns) or not names or len(set(names)) != len(names):
        raise ValueError("DDL requires unique scalar column declarations")
    return definition


def export_ddl(definition: exp.Create, *, path: Path, source: str) -> ExportReceipt:
    """Exclusively export a selected definition and its exact content hash."""
    content = (definition.sql(dialect="athena", pretty=True) + ";\n").encode()
    with path.open("xb") as stream:
        stream.write(content)
    return ExportReceipt(path=path, sha256=sha256(content).hexdigest(), source=source)


def discover_ddl(client: Any, *, location: RelationLocation) -> exp.Create:
    """Read one selected catalog definition through a supplied Glue client."""
    table = client.get_table(DatabaseName=location.database, Name=location.relation)["Table"]
    if table.get("Name") != location.relation or table.get("TableType") == "VIRTUAL_VIEW":
        raise ValueError("Expected the selected physical table, not an unverified view")
    columns = table["StorageDescriptor"]["Columns"] + table.get("PartitionKeys", [])
    names = [c["Name"].casefold() for c in columns]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate catalog columns")
    return exp.Create(
        kind="TABLE",
        this=exp.Schema(
            this=exp.Table(
                this=exp.to_identifier(location.relation, quoted=True),
                db=exp.to_identifier(location.database, quoted=True),
                catalog=exp.to_identifier(location.catalog, quoted=True),
            ),
            expressions=[
                exp.ColumnDef(
                    this=exp.to_identifier(c["Name"], quoted=True),
                    kind=exp.DataType.build(c["Type"], dialect="athena"),
                )
                for c in columns
            ],
        ),
    )


def load_inputs(directory: Path) -> dict:
    """Load explicit lake DDL, aliases and native captures; never infer native types."""
    import ibis
    from salesforce.entities.field_definitions.schemas import to_sqlglot

    manifest_path = directory / "inputs.yaml"
    inputs = load_yaml(manifest_path)
    payloads = {"inputs.yaml": manifest_path.read_bytes()}
    for name, binding in inputs["tables"].items():
        binding.setdefault("relation", binding["native_object"].lower() + "_history")
        path = directory / binding.pop("ddl")
        definition = read_ddl(path)
        table = definition.this.this
        if (table.catalog, table.db, table.name) != tuple(
            binding[k] for k in ("catalog", "database", "relation")
        ):
            raise ValueError(f"DDL identity differs from selected relation: {name}")
        schema = ibis.Schema.from_sqlglot(definition.this, dialect="athena")
        binding["fields"] = {key: str(value) for key, value in schema.items()}
        binding["ddl_sha256"] = sha256(path.read_bytes()).hexdigest()
        payloads[path.relative_to(directory).as_posix()] = path.read_bytes()
    flow_path = directory / inputs.pop("flow_file")
    inputs["flow"] = json.loads(flow_path.read_bytes())
    inputs["flow_sha256"] = sha256(flow_path.read_bytes()).hexdigest()
    payloads[flow_path.relative_to(directory).as_posix()] = flow_path.read_bytes()
    inputs["field_definitions"] = []
    native_path = inputs.pop("field_export", None)
    if native_path:
        path = directory / native_path
        content = path.read_bytes()
        payloads[path.relative_to(directory).as_posix()] = content
        for ei, entity in enumerate(json.loads(content)):
            envelope = entity["Fields"]
            if envelope.get("done") is not True or envelope.get("nextRecordsUrl"):
                raise ValueError("Incomplete native Fields capture")
            for fi, field in enumerate(envelope["records"]):
                pointer = f"/{ei}/Fields/records/{fi}"
                candidates = [(field, pointer)]
                particles = field.get("Particles")
                if particles:
                    if particles.get("done") is not True or particles.get("nextRecordsUrl"):
                        raise ValueError("Incomplete native Particles capture")
                    candidates.extend(
                        (
                            {
                                **particle,
                                "FieldDefinition.QualifiedApiName": field["QualifiedApiName"],
                            },
                            pointer + f"/Particles/records/{pi}",
                        )
                        for pi, particle in enumerate(particles["records"])
                        if particle.get("QualifiedApiName") != field["QualifiedApiName"]
                    )
                for selected, pointer in candidates:
                    identity = (
                        entity["QualifiedApiName"]
                        + "."
                        + (
                            selected["FieldDefinition.QualifiedApiName"] + "."
                            if selected.get("IsComponent")
                            else ""
                        )
                        + selected["QualifiedApiName"]
                    )
                    if identity not in inputs["native_fields"]:
                        continue
                    column = to_sqlglot(
                        {**selected, "objectName": entity["QualifiedApiName"]},
                        source={
                            "source_sha256": sha256(content).hexdigest(),
                            "source_metadata_path": pointer,
                            "source_file": path.name,
                        },
                    )
                    inputs["field_definitions"].append(column.dump())
        if len(inputs["field_definitions"]) != len(inputs["native_fields"]):
            raise ValueError("Selected native field evidence is incomplete")
    elif inputs.get("native_fields"):
        raise ValueError("Native fields require an explicit API export")
    inputs["inputs_sha256"] = sha256(
        b"".join(k.encode() + b"\0" + v for k, v in sorted(payloads.items()))
    ).hexdigest()
    return inputs
