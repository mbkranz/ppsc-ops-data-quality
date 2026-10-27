"""Optional offline Salesforce authoring; producer dependencies are never runtime inputs."""

import argparse
import hashlib
import inspect
import json
from datetime import date
from importlib.metadata import distribution
from pathlib import Path
from typing import Literal

import ibis
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlglot import exp

from ppsc_ops_data_quality.core.configuration import load_yaml
from ppsc_ops_data_quality.core.schemas import schema_from_ddl

PRODUCER_REVISION = "a534c63353680e41d12e3b55997a125ba703c675"


class AuthoringRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fields_file: Path
    objects: dict[str, tuple[str, ...]]
    flow_file: Path | None = None
    selection_file: Path | None = None
    flow_run_date: date | None = None
    record_ddl: Path | None = None
    lookup_ddls: dict[str, Path] = Field(default_factory=dict)

    @model_validator(mode="after")
    def explicit_selection(self) -> "AuthoringRequest":
        if not self.objects or any(
            not obj.strip()
            or not fields
            or len(set(fields)) != len(fields)
            or any(not field.strip() for field in fields)
            for obj, fields in self.objects.items()
        ):
            raise ValueError("Select nonempty objects and unique fields explicitly")
        if any(
            (
                self.flow_file,
                self.selection_file,
                self.record_ddl,
                self.lookup_ddls,
                self.flow_run_date,
            )
        ) and not all((self.flow_file, self.selection_file, self.record_ddl, self.flow_run_date)):
            raise ValueError(
                "Flow authoring requires flow_file, selection_file, record_ddl and explicit flow_run_date"
            )
        return self


class AuthoringReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["salesforce-authoring/v1"] = "salesforce-authoring/v1"
    inputs: dict[str, str]
    request: AuthoringRequest
    invocation_directory: Path
    producer_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    producer_version: str = Field(min_length=1)
    producer_code: dict[str, str]
    outputs: dict[str, str]
    execution_role: Literal["Logical authoring references only; not runtime SQL inputs"] = (
        "Logical authoring references only; not runtime SQL inputs"
    )


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _producer_identity() -> tuple[str, str]:
    package = distribution("ppsc-salesforce")
    origin = json.loads(package.read_text("direct_url.json") or "{}")
    revision = origin.get("vcs_info", {}).get("commit_id")
    if revision != PRODUCER_REVISION:
        raise ValueError("Use the author-salesforce task's pinned producer environment")
    return revision, package.version


def produce_references(request: AuthoringRequest, *, output: Path) -> AuthoringReceipt:
    """Generate candidate DDL, evidence and optional named Flow SQL into a fresh directory.

    Selection is caller-authored. The compiler fails for missing selected fields
    or required lookup/formula inputs; this operation never guesses relationships,
    source snapshots or physical types. Review the complete required input closure.
    """
    from salesforce.entities.field_definitions.schemas import to_sqlglot

    if output.exists():
        raise FileExistsError(output)
    producer_revision, producer_version = _producer_identity()
    rows = json.loads(request.fields_file.read_text())
    if not isinstance(rows, list):
        raise ValueError("fields_file must contain a JSON list of flattened native field rows")
    source = {
        "source_file": str(request.fields_file),
        "source_sha256": _digest(request.fields_file),
    }
    generated = {
        "request.json": json.dumps(
            {
                "request": request.model_dump(mode="json"),
                "invocation_directory": str(Path.cwd()),
            },
            indent=2,
        )
        + "\n"
    }
    field_evidence = {}
    for obj, fields in request.objects.items():
        columns = []
        for field in fields:
            matches = [
                (index, row)
                for index, row in enumerate(rows)
                if row.get("EntityDefinition.QualifiedApiName", row.get("objectName")) == obj
                and row.get(
                    "EntityParticle.QualifiedApiName",
                    row.get("QualifiedApiName", row.get("FieldDefinition.QualifiedApiName")),
                )
                == field
            ]
            if len(matches) != 1:
                raise ValueError(f"Expected one selected native field: {obj}.{field}")
            index, row = matches[0]
            column = to_sqlglot(row, source={**source, "source_paths": [f"/{index}"]})
            columns.append(column)
            field_evidence[f"{obj}.{field}"] = column.meta["ppsc"]
        query = exp.Create(
            this=exp.Schema(this=exp.to_table(obj), expressions=columns), kind="TABLE"
        )
        ddl = query.sql(dialect="athena", pretty=True) + ";\n"
        schema_from_ddl(ddl)
        # Output names derive from an ordinal, never unsanitized object/path text.
        generated[f"object-{len(generated):03d}.sql"] = ddl
    generated["fields.json"] = json.dumps(field_evidence, indent=2) + "\n"
    paths = [request.fields_file]
    producer = {
        "field_schemas": _digest(Path(inspect.getfile(to_sqlglot))),
        "authoring_script": _digest(Path(__file__)),
    }
    if request.flow_file is not None:
        from salesforce.entities.flows.queries import FlowRequest, flow_lineage, flow_queries

        flow = json.loads(request.flow_file.read_text())
        selected = FlowRequest.model_validate(load_yaml(request.selection_file))
        native = flow["Metadata"]
        record = ibis.table(schema_from_ddl(request.record_ddl.read_text()), name="Event_Before")
        lookups = {
            name: ibis.table(schema_from_ddl(path.read_text()), name=f"Lookup_{index}")
            for index, (name, path) in enumerate(request.lookup_ddls.items())
        }
        queries = flow_queries(
            record,
            lookups,
            native,
            selected,
            flow_run_date=ibis.literal(request.flow_run_date),
            eligibility=lambda _: ibis.literal(True),
        )
        evidence = flow_lineage(
            native,
            selected,
            source={
                "source_file": str(request.flow_file),
                "source_sha256": _digest(request.flow_file),
                "flow_version_id": flow.get("Id"),
                "eligibility": "caller-selected true for logical template",
            },
        )
        generated["flow-lineage.json"] = json.dumps(evidence, indent=2) + "\n"
        for index, (name, expression) in enumerate(queries.items()):
            generated[f"query-{index:03d}.sql"] = (
                "-- Logical authoring template: eligibility=true; caller supplied inspection DATE.\n"
                + str(ibis.to_sql(expression, dialect="athena"))
                + ";\n"
            )
            generated[f"query-{index:03d}.json"] = (
                json.dumps(
                    {
                        "name": name,
                        "role": "logical-template",
                        "schema": dict(expression.schema().items()),
                    },
                    default=str,
                    indent=2,
                )
                + "\n"
            )
        producer["flow_queries"] = _digest(Path(inspect.getfile(flow_queries)))
        paths += [
            request.flow_file,
            request.selection_file,
            request.record_ddl,
            *request.lookup_ddls.values(),
        ]
    output.mkdir(parents=True, exist_ok=False)
    for name, content in generated.items():
        (output / name).write_text(content, encoding="utf-8")
    receipt = AuthoringReceipt(
        inputs={str(path): _digest(path) for path in paths},
        request=request,
        invocation_directory=Path.cwd(),
        producer_revision=producer_revision,
        producer_version=producer_version,
        producer_code=producer,
        outputs={name: _digest(output / name) for name in generated},
    )
    (output / "manifest.json").write_text(receipt.model_dump_json(indent=2) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = AuthoringRequest.model_validate(load_yaml(args.config))
    print(produce_references(request, output=args.output).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
