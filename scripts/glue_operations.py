"""Run and inspect a planned Glue release with explicit SDK calls and receipts."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

import boto3
from botocore.config import Config
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    plan: Path
    config_uri: str = Field(pattern=r"^s3://[^/]+/.+")
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("config_uri")
    @classmethod
    def validate_uri(cls, value: str) -> str:
        from urllib.parse import urlsplit

        uri = urlsplit(value)
        if uri.query or uri.fragment or ".." in uri.path.split("/"):
            raise ValueError("Runtime configuration requires an explicit S3 object URI")
        return value


class RunReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    job_name: str
    status: Literal["submitted", "unknown"]
    run_id: str | None = Field(
        default=None, pattern=r"^[A-Za-z0-9_-]+$", serialization_alias="JobRunId"
    )
    error: str | None = None

    @model_validator(mode="after")
    def validate_submission(self):
        if self.status == "submitted" and (self.run_id is None or self.error is not None):
            raise ValueError("A submitted run requires its returned run ID")
        if self.status == "unknown" and (self.run_id is not None or not self.error):
            raise ValueError("An unknown submission requires the error and no claimed run ID")
        return self


class StatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    plan: Path
    run_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")


class RunStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    job_name: str
    run_id: str
    state: str = Field(serialization_alias="State")
    outcome: Literal["running", "succeeded", "failed", "unknown"]
    error: str | None = Field(default=None, serialization_alias="Error")
    started: datetime | None = Field(default=None, serialization_alias="Started")
    completed: datetime | None = Field(default=None, serialization_alias="Completed")
    log_group: str | None = Field(default=None, serialization_alias="LogGroup")


def checked_target(plan: Path, *, session: boto3.Session) -> dict:
    target = json.loads((plan / "target.json").read_text(encoding="utf-8"))
    if session.client("sts").get_caller_identity()["Account"] != target["account_id"]:
        raise ValueError("AWS account differs from deployment plan")
    return target


def start_glue_run(request: RunRequest, *, session: boto3.Session) -> RunReceipt:
    target = checked_target(request.plan, session=session)
    expected = json.loads((request.plan / "update-job.json").read_text(encoding="utf-8"))[
        "JobUpdate"
    ]
    glue = session.client(
        "glue", region_name=target["region"], config=Config(retries={"total_max_attempts": 1})
    )
    live = glue.get_job(JobName=target["job_name"])["Job"]
    if any(live.get(key) != value for key, value in expected.items()):
        raise ValueError("Glue job differs from the selected deployment plan")
    try:
        response = glue.start_job_run(
            JobName=target["job_name"],
            Arguments={
                "--config_uri": request.config_uri,
                "--config_sha256": request.config_sha256,
            },
        )
        receipt = RunReceipt(
            job_name=target["job_name"], status="submitted", run_id=response["JobRunId"]
        )
    except Exception as exc:
        # A lost SDK response cannot establish whether AWS accepted the submission.
        receipt = RunReceipt(job_name=target["job_name"], status="unknown", error=str(exc))
    runs = request.plan / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (request.plan / "run.json").write_text(
        receipt.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8"
    )
    if receipt.run_id:
        (runs / f"{receipt.run_id}.json").write_text(
            receipt.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8"
        )
    return receipt


def get_glue_status(request: StatusRequest, *, session: boto3.Session) -> RunStatus:
    target = checked_target(request.plan, session=session)
    glue = session.client("glue", region_name=target["region"])
    run = glue.get_job_run(JobName=target["job_name"], RunId=request.run_id)["JobRun"]
    state = run["JobRunState"]
    failed = {"FAILED", "TIMEOUT", "STOPPED", "ERROR", "EXPIRED"}
    receipt = RunStatus(
        job_name=target["job_name"],
        run_id=request.run_id,
        state=state,
        outcome=(
            "failed"
            if state in failed
            else "succeeded"
            if state == "SUCCEEDED"
            else "running"
            if state in {"STARTING", "RUNNING", "STOPPING", "WAITING"}
            else "unknown"
        ),
        error=run.get("ErrorMessage"),
        started=run.get("StartedOn"),
        completed=run.get("CompletedOn"),
        log_group=run.get("LogGroupName"),
    )
    runs = request.plan / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{request.run_id}.status.json").write_text(
        receipt.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    start = commands.add_parser("run")
    start.add_argument("--config-uri", required=True)
    start.add_argument("--config-sha256", required=True)
    status = commands.add_parser("status")
    status.add_argument("--run-id", required=True)
    for command in (start, status):
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--profile", default="data-migration-dev")
    args = vars(parser.parse_args())
    session = boto3.Session(profile_name=args.pop("profile"))
    operation = args.pop("operation")
    if operation == "run":
        receipt = start_glue_run(RunRequest(**args), session=session)
        success = receipt.status == "submitted"
    else:
        receipt = get_glue_status(StatusRequest(**args), session=session)
        success = receipt.outcome in {"running", "succeeded"}
    print(receipt.model_dump_json(indent=2, by_alias=True))
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
