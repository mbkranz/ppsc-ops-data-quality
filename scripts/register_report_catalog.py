"""Submit the two rendered catalog statements and retain partial query evidence."""

import argparse
import json
from pathlib import Path
from typing import Literal

import boto3
from pydantic import BaseModel, ConfigDict, Field, model_validator

from scripts.glue_operations import checked_target


class CatalogRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    plan: Path
    catalog: Path


class CatalogSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    statement: str
    query_id: str = Field(min_length=1)


class CatalogReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: Literal["submitting", "submitted", "failed"] = "submitting"
    queries: list[CatalogSubmission] = Field(default_factory=list, max_length=2)
    error: str | None = None

    @model_validator(mode="after")
    def validate_submission(self):
        if self.status == "submitted" and (len(self.queries) != 2 or self.error is not None):
            raise ValueError("Submitted catalog requires both query IDs")
        if self.status == "failed" and not self.error:
            raise ValueError("Failed catalog submission requires its error")
        return self


def register_report_catalog(request: CatalogRequest, *, session: boto3.Session) -> CatalogReceipt:
    checked_target(request.plan, session=session)
    target = json.loads((request.catalog / "target.json").read_text(encoding="utf-8"))
    statements = [
        (name, (request.catalog / name).read_text(encoding="utf-8"))
        for name in ("00.sql", "01.sql")
    ]
    if any(not sql.strip() for _, sql in statements):
        raise ValueError("Both rendered catalog statements must be nonempty")
    athena = session.client("athena", region_name=target["region"])
    queries = []
    path = request.catalog / "submission.json"
    for name, sql in statements:
        try:
            response = athena.start_query_execution(
                QueryString=sql,
                WorkGroup=target["work_group"],
                QueryExecutionContext=target["context"],
                ResultConfiguration=target["results"],
            )
            queries.append(CatalogSubmission(statement=name, query_id=response["QueryExecutionId"]))
        except Exception as exc:
            receipt = CatalogReceipt(status="failed", queries=queries, error=str(exc))
            path.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
            return receipt
        receipt = CatalogReceipt(queries=queries)
        path.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
    receipt = CatalogReceipt(status="submitted", queries=queries)
    path.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--profile", default="data-migration-dev")
    args = vars(parser.parse_args())
    session = boto3.Session(profile_name=args.pop("profile"))
    receipt = register_report_catalog(CatalogRequest(**args), session=session)
    print(receipt.model_dump_json(indent=2))
    if receipt.status != "submitted":
        raise SystemExit(1)
