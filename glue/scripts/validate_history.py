"""Glue 5.0 driver: install the release bundle, then validate history via Athena."""

import argparse
import hashlib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

import boto3

from ppsc_ops_data_quality.runtime.job import validate_athena


def main(argv=None, *, s3_client=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config_uri", required=True)
    parser.add_argument("--config_sha256", required=True)
    parser.add_argument("--release_revision", required=True)
    parser.add_argument("--release_manifest_uri", required=True)
    parser.add_argument("--JOB_NAME", required=True)
    parser.add_argument("--JOB_RUN_ID", required=True)
    args, _ = parser.parse_known_args(argv)  # Glue injects additional system options.
    location = urlsplit(args.config_uri)
    if location.scheme != "s3" or not location.netloc or not location.path.strip("/"):
        raise ValueError("config_uri must identify an S3 object")
    if location.query or location.fragment:
        raise ValueError("config_uri must not include a query or fragment")
    client = s3_client if s3_client is not None else boto3.client("s3")
    response = client.get_object(Bucket=location.netloc, Key=location.path.lstrip("/"))
    body = response["Body"]
    try:
        content = body.read()
    finally:
        body.close()
    config_hash = hashlib.sha256(content).hexdigest()
    if config_hash != args.config_sha256:
        raise ValueError("Runtime configuration SHA256 does not match submitted run")
    with TemporaryDirectory(prefix="ppsc-dq-") as directory:
        root = Path(directory)
        config_path = root / "params.toml"
        config_path.write_bytes(content)
        return validate_athena(
            config_path,
            root / "run",
            run_metadata={
                "config_uri": args.config_uri,
                "config_sha256": config_hash,
                "release_revision": args.release_revision,
                "release_manifest_uri": args.release_manifest_uri,
                "glue_job_name": args.JOB_NAME,
                "glue_job_run_id": args.JOB_RUN_ID,
            },
        )


if __name__ == "__main__":
    try:
        code = main()
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        code = 2
    # Glue has SUCCEEDED/FAILED rather than distinct data/execution failure states.
    # The published native results and manifest distinguish those outcomes.
    raise SystemExit(code)
