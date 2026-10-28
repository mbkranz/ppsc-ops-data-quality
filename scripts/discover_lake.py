#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "boto3>=1.42,<2",
#     "poethepoet>=0.37,<1",
#     "pyyaml>=6,<7",
# ]
#
# [tool.poe]
# executor.type = "simple"
#
# [tool.poe.tasks.aws-account]
# help = "Print the active AWS account using AWS CLI STS."
# cmd = "${APMP_PYTHON} ${APMP_SCRIPT} --worker aws-account"
# cwd = "${APMP_PROJECT}"
#
# [tool.poe.tasks.lake-config]
# help = "Resolve the active account to its configured Athena catalog/database."
# cmd = "${APMP_PYTHON} ${APMP_SCRIPT} --worker lake-config"
# cwd = "${APMP_PROJECT}"
#
# [tool.poe.tasks.discover]
# help = "Save all Athena table, column, and partition metadata."
# cmd = "${APMP_PYTHON} ${APMP_SCRIPT} --worker discover"
# cwd = "${APMP_PROJECT}"
# ///

"""Discover APMP lake metadata online; build its lineage separately, offline."""

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import boto3
import yaml
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from poethepoet.app import PoeThePoet

SNAPSHOT_VERSION = "apmp-data-lake/v1"
PROJECT = Path(__file__).resolve().parents[1] / "lake"


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise ValueError(f"Configuration key must be unique text: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def load_yaml(path: Path) -> dict:
    document = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    if not isinstance(document, dict):
        raise ValueError(f"Expected a configuration mapping: {path}")
    return document


def account_id(*, profile: str = "data-migration-dev") -> str:
    result = subprocess.run(
        [
            "aws",
            "--profile",
            profile,
            "sts",
            "get-caller-identity",
            "--query",
            "Account",
            "--output",
            "text",
            "--no-cli-pager",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()
    if not re.fullmatch(r"[0-9]{12}", result):
        raise ValueError(f"AWS CLI returned an invalid account ID: {result!r}")
    return result


def lake_config(account: str, *, project: Path = PROJECT) -> dict:
    accounts = load_yaml(project / "params.yaml").get("aws_accounts")
    if not isinstance(accounts, dict):
        raise ValueError("Project params.yaml requires aws_accounts")
    for key, value in accounts.items():
        if not re.fullmatch(r"[0-9]{12}", key) or not isinstance(value, dict):
            raise ValueError("aws_accounts requires quoted 12-digit keys and mappings")
    if account not in accounts:
        raise ValueError(
            f"No lake configured for AWS account {account}; edit {project / 'params.yaml'}"
        )
    settings = accounts[account]
    for key in ("environment", "catalog", "database"):
        if not isinstance(settings.get(key), str) or not settings[key].strip():
            raise ValueError(f"Missing or invalid lake setting: {key}")
    environment = settings["environment"]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", environment):
        raise ValueError(f"Invalid lake environment: {environment}")
    for key in ("region", "workgroup"):
        if settings.get(key) is not None and (
            not isinstance(settings[key], str) or not settings[key].strip()
        ):
            raise ValueError(f"Invalid optional lake setting: {key}")
    return dict(settings, account_id=account)


def validate_tables(tables: list[dict]) -> dict[str, int]:
    names = set()
    count = 0
    for table in tables:
        if not isinstance(table, dict):
            raise ValueError("Invalid Athena table metadata")
        name = table.get("Name")
        if not isinstance(name, str) or not name or name.casefold() in names:
            raise ValueError(f"Missing or duplicate Athena table name: {name!r}")
        names.add(name.casefold())
        columns = {}
        for group in ("Columns", "PartitionKeys"):
            values = table.get(group, [])
            if not isinstance(values, list):
                raise ValueError(f"{name}.{group} must be a list")
            for column in values:
                if not isinstance(column, dict):
                    raise ValueError(f"Invalid column in {name}.{group}")
                field = column.get("Name")
                if not isinstance(field, str) or not field or not column.get("Type"):
                    raise ValueError(f"Invalid column in {name}.{group}")
                key = field.casefold()
                if key in columns and columns[key] != column:
                    raise ValueError(f"Conflicting Athena column: {name}.{field}")
                columns[key] = column
        count += len(columns)
    return dict(tables=len(tables), fields=count)


def json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported metadata value: {type(value).__name__}")


def save_snapshot(snapshot: dict, output: Path) -> None:
    text = json.dumps(snapshot, default=json_default, sort_keys=True, allow_nan=False, indent=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text + "\n")
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def discover(
    settings: dict, output: Path, *, profile: str = "data-migration-dev", session=None
) -> dict:
    if settings["account_id"] == "000000000000" or any(
        "<" in settings[key] or ">" in settings[key] for key in ("catalog", "database")
    ):
        raise ValueError("Replace account/catalog/database placeholders before discovery")
    if session is None:
        session = boto3.Session(
            profile_name=profile,
            region_name=settings.get("region") or os.environ.get("AWS_REGION"),
        )
    if not session.region_name:
        raise ValueError("Configure an AWS region before discovery")
    client = session.client(
        "athena",
        config=Config(
            retries={"mode": "standard", "total_max_attempts": 3},
            connect_timeout=5,
            read_timeout=30,
        ),
    )
    request = dict(CatalogName=settings["catalog"], DatabaseName=settings["database"])
    if settings.get("workgroup"):
        request["WorkGroup"] = settings["workgroup"]
    tables = [
        table
        for page in client.get_paginator("list_table_metadata").paginate(**request)
        for table in page["TableMetadataList"]
    ]
    counts = validate_tables(tables)
    snapshot = dict(
        contract_version=SNAPSHOT_VERSION,
        **{key: settings[key] for key in ("account_id", "environment", "catalog", "database")},
        region=session.region_name,
        workgroup=settings.get("workgroup"),
        coverage=dict(complete=True, scope="all_tables_and_columns"),
        counts=counts,
        tables=sorted(tables, key=lambda table: table["Name"]),
    )
    save_snapshot(snapshot, output)
    return snapshot


def inline_config() -> dict:
    lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    start = lines.index("# /// script") + 1
    end = lines.index("# ///", start)
    return tomllib.loads(
        "\n".join(line.removeprefix("#").removeprefix(" ") for line in lines[start:end])
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if not argv or argv[0] != "--worker":
            # Poe reloads file configuration even when given a configuration mapping.
            with TemporaryDirectory(prefix="apmp-poe-") as temporary:
                path = Path(temporary)
                (path / "poe_tasks.json").write_text(json.dumps(inline_config()), encoding="utf-8")
                return PoeThePoet(
                    cwd=path,
                    config_name="poe_tasks.json",
                    env=dict(
                        os.environ,
                        APMP_PYTHON=sys.executable,
                        APMP_SCRIPT=str(Path(__file__).resolve()),
                        APMP_PROJECT=str(PROJECT),
                    ),
                    program_name="apmp_data_lake.py",
                )(argv)
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("task", choices=("aws-account", "lake-config", "discover"))
        parser.add_argument("--output", type=Path)
        parser.add_argument("--profile", default="data-migration-dev")
        args = parser.parse_args(argv[1:])
        account = account_id(profile=args.profile)
        if args.task == "aws-account":
            print(account)
            return 0
        settings = lake_config(account)
        if args.task == "lake-config":
            print(json.dumps(settings, sort_keys=True, indent=2))
            return 0
        output = args.output or (PROJECT / "snapshots" / settings["environment"] / "tables.json")
        snapshot = discover(settings, output, profile=args.profile)
        print(json.dumps(dict(output=str(output), **snapshot["counts"]), sort_keys=True))
        if not snapshot["tables"]:
            print("Athena database is empty; enumeration completed.", file=sys.stderr)
        return 0
    except subprocess.CalledProcessError as error:
        print(error.stderr or str(error), file=sys.stderr)
        return error.returncode
    except (
        OSError,
        ValueError,
        yaml.YAMLError,
        BotoCoreError,
        ClientError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
