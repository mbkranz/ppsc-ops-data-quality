"""Verify a release and render AWS CLI payloads without making network calls."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import boto3
from botocore.validate import validate_parameters

from ppsc_ops_data_quality.core.configuration import load_yaml
from scripts.package_release import sha256, verify_bundle


def deployment_target(config: Path, account: str, environment: str):
    targets = load_yaml(config)["environments"]
    accounts = [target["account_id"] for target in targets.values()]
    if any(not isinstance(account_id, str) for account_id in accounts):
        raise ValueError("Quote account IDs in YAML configuration")
    if len(accounts) != len(set(accounts)):
        raise ValueError("Deployment accounts must be unique")
    matches = [
        (name, target) for name, target in targets.items() if target["account_id"] == account
    ]
    if len(matches) != 1 or not re.fullmatch(r"\d{12}", account):
        raise ValueError("Unknown AWS account; configure the STS identity before deployment")
    name, target = matches[0]
    if name not in {"dev", "prod"} or name != environment:
        raise ValueError("Environment conflicts with active AWS account")
    if "REPLACE_WITH_" in json.dumps(target):
        raise ValueError("Replace deployment configuration placeholders")
    if not re.fullmatch(
        rf"arn:aws(?:-us-gov|-cn)?:iam::{account}:role/[^\s]+", target["glue_role"]
    ):
        raise ValueError("Glue execution role must belong to the selected AWS account")
    uri = urlsplit(target["artifact_s3_uri"])
    if (
        uri.scheme != "s3"
        or not uri.netloc
        or uri.query
        or uri.fragment
        or not uri.path.strip("/")
        or ".." in uri.path.split("/")
    ):
        raise ValueError("Artifact destination must be an explicit S3 prefix")
    return target


def plan_deployment(*, config, account, environment, bundle, output):
    target = deployment_target(config, account, environment)
    manifest_path = bundle / "manifest.json"
    manifest = verify_bundle(bundle)
    prefix = f"{target['artifact_s3_uri'].rstrip('/')}/releases/{sha256(manifest_path)}"
    job = load_yaml(Path("glue/job.yaml"))
    if {"Role", "Command"}.intersection(job):
        raise ValueError("Job template must not override the release command or execution role")
    job.update(
        Role=target["glue_role"],
        Command={
            "Name": "glueetl",
            "PythonVersion": "3",
            "ScriptLocation": f"{prefix}/validate_history.py",
        },
    )
    job.setdefault("DefaultArguments", {}).update(
        {
            "--additional-python-modules": f"{prefix}/dependencies.gluewheels.zip",
            "--release_revision": manifest["revision"],
            "--release_manifest_uri": f"{prefix}/manifest.json",
        }
    )
    if job["GlueVersion"] != manifest["runtime"]["glue_version"]:
        raise ValueError("Job template Glue version conflicts with release runtime")
    if job["DefaultArguments"].get("--python-modules-installer-option") != "--no-index":
        raise ValueError("Released wheel installation must remain offline (--no-index)")
    model = boto3.Session()._session.get_service_model("glue")
    validate_parameters(
        {"Name": target["job_name"], **job}, model.operation_model("CreateJob").input_shape
    )
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in {
        "create-job": {"Name": target["job_name"], **job},
        "update-job": {"JobName": target["job_name"], "JobUpdate": job},
        "target": {
            **target,
            "release_uri": prefix,
            "revision": manifest["revision"],
            "bundle": str(bundle.resolve()),
            "manifest_sha256": sha256(manifest_path),
        },
    }.items():
        (output / f"{name}.json").write_text(json.dumps(payload, indent=2) + "\n")
    # Only declared artifacts; completion manifest is uploaded last by Poe.
    (output / "uploads.tsv").write_text(
        "".join(
            f"{(bundle / name).resolve()}\t{prefix}/{name}\n"
            for name in [*sorted(manifest["files"]), "manifest.json"]
        )
    )
    print(
        json.dumps(
            {
                "job_name": target["job_name"],
                "region": target["region"],
                "release_uri": prefix,
                "output": str(output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--environment", choices=["dev", "prod"], required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    plan_deployment(**vars(parser.parse_args()))
