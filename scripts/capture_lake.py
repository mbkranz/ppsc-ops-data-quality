"""Explicit online capture of selected native Glue storage/view evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    account_id: str = Field(pattern=r"^[0-9]{12}$")
    database: str = Field(min_length=1)
    relations: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_selection(self) -> CaptureRequest:
        if self.account_id == "000000000000" or "<" in self.database:
            raise ValueError("Replace account/database placeholders before online capture")
        if len(set(self.relations)) != len(self.relations) or any(
            not name.strip() for name in self.relations
        ):
            raise ValueError("Select unique nonempty relation names")
        return self


class CaptureReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    output_path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    relations: tuple[str, ...] = Field(min_length=1)


def _json_value(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Unsupported native metadata value: {type(value).__name__}")


def capture_resources(
    request: CaptureRequest, *, glue_client: Any, output_path: Path
) -> CaptureReceipt:
    """Preserve native table formats, storage descriptors, partitions and view text.

    The supplied client owns authentication. This is read-only acquisition; it
    never runs DDL and does not turn incomplete metadata into deployable SQL.
    All selected resources are read before the atomic snapshot write.
    """
    tables = []
    for name in request.relations:
        table = glue_client.get_table(
            CatalogId=request.account_id, DatabaseName=request.database, Name=name
        )["Table"]
        if (
            table.get("Name") != name
            or table.get("DatabaseName", request.database) != request.database
        ):
            raise ValueError(f"Returned metadata does not match selected relation: {name}")
        tables.append(table)
    payload = (
        json.dumps(
            {
                "version": "apmp-resource-evidence/v1",
                "account_id": request.account_id,
                "database": request.database,
                "coverage": {
                    "complete": False,
                    "scope": "explicit selected Glue resources",
                },
                "tables": tables,
            },
            sort_keys=True,
            indent=2,
            default=_json_value,
            allow_nan=False,
        ).encode()
        + b"\n"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(dir=output_path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        temporary.replace(output_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return CaptureReceipt(
        output_path=output_path,
        sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
        relations=request.relations,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--relation", action="append", required=True, dest="relations")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", default="data-migration-dev")
    parser.add_argument("--region", required=True)
    args = parser.parse_args()
    request = CaptureRequest(
        account_id=args.account_id, database=args.database, relations=args.relations
    )
    import boto3

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    if session.client("sts").get_caller_identity()["Account"] != request.account_id:
        raise ValueError("Active AWS account does not match selected capture account")
    receipt = capture_resources(
        request, glue_client=session.client("glue"), output_path=args.output
    )
    print(receipt.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
