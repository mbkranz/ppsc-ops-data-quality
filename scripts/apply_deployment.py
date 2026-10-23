"""Stage immutable release bytes before explicitly creating or updating a Glue job."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, ConfigDict, Field

from scripts.package_release import sha256
from scripts.release_artifact import verify_release


class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: Path
    uri: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size: int = Field(ge=0, le=5 * 1024**3)


class StagedArtifact(Artifact):
    outcome: Literal["uploaded", "unchanged"]


class DeploymentReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    status: Literal["staging", "complete", "failed"] = "staging"
    artifacts: list[StagedArtifact] = Field(default_factory=list)
    job: Literal["pending", "created", "updated", "unchanged"] = "pending"
    error: str | None = None


def verify_local(artifact: Artifact) -> None:
    if (
        artifact.source.stat().st_size != artifact.size
        or sha256(artifact.source) != artifact.sha256
    ):
        raise ValueError("Local artifact changed after deployment planning")


def object_status(s3, artifact: Artifact, *, account: str) -> str:
    uri = urlsplit(artifact.uri)
    params = {"Bucket": uri.netloc, "Key": uri.path.lstrip("/"), "ExpectedBucketOwner": account}
    try:
        current = s3.head_object(**params, ChecksumMode="ENABLED")
    except ClientError as error:
        if error.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
            return "missing"
        raise
    if current["ContentLength"] != artifact.size:
        raise ValueError(f"Different content already occupies release key: {artifact.uri}")
    body = s3.get_object(**params)["Body"]
    try:
        digest = hashlib.sha256()
        for chunk in body.iter_chunks(chunk_size=1024**2):
            digest.update(chunk)
    finally:
        body.close()
    if digest.hexdigest() != artifact.sha256:
        raise ValueError(f"Different content already occupies release key: {artifact.uri}")
    return "unchanged"


def stage_artifact(s3, artifact: Artifact, *, account: str) -> str:
    verify_local(artifact)
    if object_status(s3, artifact, account=account) == "unchanged":
        return "unchanged"
    uri = urlsplit(artifact.uri)
    try:
        with artifact.source.open("rb") as body:
            s3.put_object(
                Bucket=uri.netloc,
                Key=uri.path.lstrip("/"),
                ExpectedBucketOwner=account,
                Body=body,
                ContentLength=artifact.size,
                IfNoneMatch="*",
                ChecksumAlgorithm="SHA256",
                ChecksumSHA256=base64.b64encode(bytes.fromhex(artifact.sha256)).decode(),
            )
    except ClientError as error:
        if error.response["ResponseMetadata"]["HTTPStatusCode"] != 412:
            raise
        # A competing upload is safe only if it produced the same bytes.
        if object_status(s3, artifact, account=account) != "unchanged":
            raise ValueError("Concurrent release upload did not complete") from error
    return "uploaded"


def apply_deployment(
    plan: Path, operation: Literal["create", "update"], *, session: boto3.Session
) -> DeploymentReceipt:
    if operation not in {"create", "update"}:
        raise ValueError("operation must be create or update")
    target = json.loads((plan / "target.json").read_text())
    archive = verify_release(target["revision"])
    if sha256(Path("dvc.lock")) != target["lock_sha256"]:
        raise ValueError("Release lock changed after deployment planning")
    artifacts = [Artifact.model_validate(item) for item in target["artifacts"]]
    if {item.source.resolve() for item in artifacts} != {
        archive,
        Path("glue/scripts/validate_history.py").resolve(),
    }:
        raise ValueError("Deployment plan must stage the selected archive and Git driver")
    for artifact in artifacts:
        verify_local(artifact)
        uri = urlsplit(artifact.uri)
        if uri.scheme != "s3" or artifact.uri != f"{target['release_uri']}/{artifact.source.name}":
            raise ValueError("Artifact destination differs from selected release")
    account = session.client("sts").get_caller_identity()["Account"]
    if account != target["account_id"]:
        raise ValueError("AWS account differs from deployment plan")
    s3, glue = (session.client(service, region_name=target["region"]) for service in ("s3", "glue"))
    receipt = DeploymentReceipt(revision=target["revision"])
    try:
        # Inspect every key before writing any object.
        for artifact in artifacts:
            object_status(s3, artifact, account=account)
        for artifact in artifacts:
            outcome = stage_artifact(s3, artifact, account=account)
            receipt.artifacts.append(StagedArtifact(**artifact.model_dump(), outcome=outcome))
        payload = json.loads((plan / f"{operation}-job.json").read_text())
        if operation == "create":
            glue.create_job(**payload)
            receipt.job = "created"
        else:
            live = glue.get_job(JobName=target["job_name"])["Job"]
            if all(live.get(key) == value for key, value in payload["JobUpdate"].items()):
                receipt.job = "unchanged"
            else:
                glue.update_job(**payload)
                receipt.job = "updated"
        receipt.status = "complete"
        return receipt
    except Exception as error:
        receipt.status = "failed"
        receipt.error = f"{type(error).__name__}: {error}"
        raise
    finally:
        (plan / "deployment.json").write_text(receipt.model_dump_json(indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--operation", choices=["create", "update"], required=True)
    parser.add_argument("--profile", default="data-migration-dev")
    args = parser.parse_args()
    print(
        apply_deployment(
            args.plan, args.operation, session=boto3.Session(profile_name=args.profile)
        ).model_dump_json(indent=2)
    )
