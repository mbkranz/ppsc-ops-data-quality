"""Glue argument handling and bootstrap; Athena execution does not initialize Spark."""

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import boto3
from pydantic import BaseModel, ConfigDict, Field

from .configuration import load_validation_configuration
from .resources import ConfigurationResource, read_configuration
from .validation import ValidationOutcome, run_validation


class GlueArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    configuration: ConfigurationResource
    release_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    job_name: str = Field(min_length=1)
    job_run_id: str = Field(min_length=1)


def resolve_arguments(argv: list[str] | None = None) -> GlueArguments:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "config_uri",
        "config_sha256",
        "release_revision",
        "JOB_NAME",
        "JOB_RUN_ID",
    ):
        parser.add_argument(f"--{name}", required=True)
    args, _ = parser.parse_known_args(argv)  # Glue injects additional system options.
    return GlueArguments(
        configuration=ConfigurationResource(uri=args.config_uri, sha256=args.config_sha256),
        release_revision=args.release_revision,
        job_name=args.JOB_NAME,
        job_run_id=args.JOB_RUN_ID,
    )


def execute_glue(request: GlueArguments, *, s3_client: Any) -> ValidationOutcome:
    resource = read_configuration(request.configuration, s3_client=s3_client)
    with TemporaryDirectory(prefix="ppsc-dq-") as directory:
        root = Path(directory)
        config_path = root / "params.yaml"
        config_path.write_bytes(resource.content)
        configuration = load_validation_configuration(config_path)
        if any("profile" in key.lower() for key in configuration.athena.connection_options):
            raise ValueError("Glue configuration must use its execution role, not a local profile")
        return run_validation(
            configuration,
            run_directory=root / "run",
            athena_client_factory=lambda: boto3.client(
                "athena", region_name=configuration.athena.region
            ),
            run_metadata={
                "config_uri": resource.uri,
                "config_sha256": resource.sha256,
                "release_revision": request.release_revision,
                "glue_job_name": request.job_name,
                "glue_job_run_id": request.job_run_id,
            },
        )


def main(argv: list[str] | None = None, *, s3_client: Any = None) -> int:
    try:
        request = resolve_arguments(argv)
        client = s3_client if s3_client is not None else boto3.client("s3")
        outcome = execute_glue(request, s3_client=client)
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(outcome.model_dump_json(indent=2))
    return outcome.exit_code
