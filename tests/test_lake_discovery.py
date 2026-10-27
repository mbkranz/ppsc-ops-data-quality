"""The isolated discovery script and offline adapter preserve complete metadata."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import boto3
import pytest
import yaml
from botocore.stub import Stubber

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/discover_lake.py"
SPEC = importlib.util.spec_from_file_location("apmp_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(script)


def settings():
    return dict(
        account_id="111111111111",
        environment="qa2",
        region="us-east-1",
        catalog="lake",
        database="apmp",
        workgroup="primary",
    )


def lake_files(directory):
    directory.mkdir(parents=True, exist_ok=True)
    selected = settings()
    snapshot = dict(
        contract_version=script.SNAPSHOT_VERSION,
        **selected,
        coverage=dict(complete=True, scope="all_tables_and_columns"),
        counts=dict(tables=2, fields=5),
        tables=[
            dict(
                Name="participants",
                TableType="EXTERNAL_TABLE",
                Columns=[
                    dict(Name="name", Type="string"),
                    dict(Name="participant_id", Type="string"),
                    dict(Name="unmatched", Type="string"),
                ],
                PartitionKeys=[dict(Name="day", Type="date")],
            ),
            dict(Name="other", Columns=[dict(Name="unmatched", Type="string")]),
        ],
    )
    paths = {
        "lake/snapshot.json": directory / "snapshot.json",
        "lake/mappings.yaml": directory / "params.yaml",
        "lake/catalog.yaml": directory / "catalog.yaml",
    }
    script.save_snapshot(snapshot, paths["lake/snapshot.json"])
    paths["lake/mappings.yaml"].write_text(
        yaml.safe_dump(
            dict(
                aws_accounts={
                    selected["account_id"]: {
                        key: value
                        for key, value in selected.items()
                        if key not in {"account_id", "org"}
                    }
                },
                table_mappings={
                    "participants": dict(object="Account", fields={"participant_id": "Id"})
                },
            )
        )
    )
    paths["lake/catalog.yaml"].write_text((ROOT / "lake/catalog.yaml").read_text())
    return paths


def test_inline_tasks_are_isolated_and_work_from_another_directory(tmp_path):
    metadata = script.inline_config()
    assert metadata["requires-python"] == ">=3.12"
    assert {dep.split(">")[0] for dep in metadata["dependencies"]} == {
        "boto3",
        "poethepoet",
        "pyyaml",
    }
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert all(name in result.stdout for name in ("aws-account", "lake-config", "discover"))
    assert "pull-lineage" not in result.stdout
    fake = tmp_path / "aws"
    fake.write_text(
        f"#!{sys.executable}\nimport sys\nassert sys.argv[1:] == ['--profile', 'data-migration-dev', 'sts', 'get-caller-identity', '--query', 'Account', '--output', 'text', '--no-cli-pager']\nprint('111111111111')\n"
    )
    fake.chmod(0o755)
    env = dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"])
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "aws-account"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.rstrip().endswith("111111111111")
    assert sys.executable in result.stdout


@pytest.mark.parametrize("value", ["", "None", "123", "abc123456789"])
def test_account_id_rejects_malformed_identity(monkeypatch, value):
    call = Mock(return_value=subprocess.CompletedProcess([], 0, value, ""))
    monkeypatch.setattr(script.subprocess, "run", call)
    with pytest.raises(ValueError, match="invalid account"):
        script.account_id()
    assert call.call_args.kwargs["check"] is True
    assert call.call_args.kwargs["timeout"] == 30


def test_lake_config_resolves_without_defaulting(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    paths = lake_files(project)
    assert not (tmp_path / "params.yaml").exists()
    assert script.lake_config("111111111111", project=project) == settings()
    with pytest.raises(ValueError, match="No lake configured"):
        script.lake_config("222222222222", project=project)
    with paths["lake/mappings.yaml"].open("a") as stream:
        stream.write("\naws_accounts: {}\n")
    with pytest.raises(ValueError, match="unique text"):
        script.lake_config("111111111111", project=project)


def test_standalone_project_needs_no_salesforce_code_or_root_config(tmp_path):
    project = tmp_path / "standalone"
    lake_files(project / "lake")
    (project / "scripts").mkdir()
    isolated_script = project / "scripts" / SCRIPT.name
    shutil.copyfile(SCRIPT, isolated_script)
    fake = tmp_path / "aws"
    fake.write_text(f"#!{sys.executable}\nprint('111111111111')\n")
    fake.chmod(0o755)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib.abc
import runpy
import sys

class RejectSalesforce(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"salesforce", "scripts"}:
            raise AssertionError(f"Standalone lake imported {fullname}")

sys.meta_path.insert(0, RejectSalesforce())
sys.argv = [sys.argv[1], "--worker", "lake-config"]
runpy.run_path(sys.argv[0], run_name="__main__")
""",
            str(isolated_script),
        ],
        cwd=tmp_path,
        env=dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"]),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert json.loads(result.stdout) == settings()


@pytest.mark.parametrize("environment", ["../outside", "/absolute", "with spaces"])
def test_lake_environment_is_a_safe_standalone_name(tmp_path, environment):
    paths = lake_files(tmp_path)
    config = yaml.safe_load(paths["lake/mappings.yaml"].read_text())
    config["aws_accounts"]["111111111111"]["environment"] = environment
    paths["lake/mappings.yaml"].write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="Invalid lake environment"):
        script.lake_config("111111111111", project=tmp_path)


def athena_session():
    session = boto3.Session(
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        region_name="us-east-1",
    )
    client = session.client("athena")
    return Mock(region_name="us-east-1", client=Mock(return_value=client)), client


def test_discovery_exhausts_pages_and_keeps_partition_metadata(tmp_path):
    session, client = athena_session()
    params = dict(CatalogName="lake", DatabaseName="apmp", WorkGroup="primary")
    with Stubber(client) as stub:
        stub.add_response(
            "list_table_metadata",
            dict(
                TableMetadataList=[
                    dict(
                        Name="z",
                        Columns=[dict(Name="name", Type="string")],
                        CreateTime=datetime(2026, 1, 1, tzinfo=UTC),
                    )
                ],
                NextToken="next",
            ),
            params,
        )
        stub.add_response(
            "list_table_metadata",
            dict(
                TableMetadataList=[
                    dict(
                        Name="a",
                        Columns=[],
                        PartitionKeys=[dict(Name="day", Type="date")],
                    )
                ]
            ),
            dict(params, NextToken="next"),
        )
        output = tmp_path / "tables.json"
        result = script.discover(settings(), output, session=session)
        stub.assert_no_pending_responses()
    saved = json.loads(output.read_text())
    assert "org" not in saved
    assert result["counts"] == dict(tables=2, fields=2)
    assert [table["Name"] for table in saved["tables"]] == ["a", "z"]
    assert saved["tables"][0]["PartitionKeys"][0]["Type"] == "date"
    assert saved["tables"][1]["CreateTime"] == "2026-01-01T00:00:00+00:00"
    assert session.client.call_args.args == ("athena",)
    config = session.client.call_args.kwargs["config"]
    assert config.connect_timeout == 5
    assert config.retries["total_max_attempts"] == 3


def test_failed_later_page_preserves_previous_snapshot(tmp_path):
    session, client = athena_session()
    output = tmp_path / "tables.json"
    output.write_text("previous")
    params = dict(CatalogName="lake", DatabaseName="apmp", WorkGroup="primary")
    with Stubber(client) as stub:
        stub.add_response(
            "list_table_metadata", dict(TableMetadataList=[], NextToken="next"), params
        )
        stub.add_client_error(
            "list_table_metadata",
            service_error_code="AccessDeniedException",
            expected_params=dict(params, NextToken="next"),
        )
        with pytest.raises(client.exceptions.ClientError):
            script.discover(settings(), output, session=session)
    assert output.read_text() == "previous"
    assert list(tmp_path.iterdir()) == [output]


def test_empty_database_is_complete_and_placeholder_never_calls_aws(tmp_path):
    session, client = athena_session()
    with Stubber(client) as stub:
        stub.add_response(
            "list_table_metadata",
            dict(TableMetadataList=[]),
            dict(CatalogName="lake", DatabaseName="apmp", WorkGroup="primary"),
        )
        result = script.discover(settings(), tmp_path / "tables.json", session=session)
    assert result["counts"] == dict(tables=0, fields=0)
    assert result["coverage"]["complete"]
    with pytest.raises(ValueError, match="placeholders"):
        script.discover(
            dict(settings(), catalog="<catalog>"),
            tmp_path / "tables.json",
            session=Mock(),
        )


@pytest.mark.parametrize(
    "tables",
    [
        [dict(Name="x"), dict(Name="X")],
        [
            dict(
                Name="x",
                Columns=[dict(Name="id", Type="string"), dict(Name="ID", Type="int")],
            )
        ],
        [dict(Name="x", Columns=[None])],
    ],
)
def test_invalid_inventories_fail_explicitly(tables):
    with pytest.raises(ValueError):
        script.validate_tables(tables)


@pytest.mark.parametrize(
    "failure",
    [
        FileNotFoundError("aws"),
        subprocess.TimeoutExpired("aws", 30),
        subprocess.CalledProcessError(7, "aws", stderr="denied"),
    ],
)
def test_worker_reports_aws_failures(monkeypatch, capsys, failure):
    monkeypatch.setattr(script, "account_id", Mock(side_effect=failure))
    assert script.main(["--worker", "discover"]) == (
        7 if isinstance(failure, subprocess.CalledProcessError) else 1
    )
    assert capsys.readouterr().err


@pytest.mark.parametrize("profile", ["data-migration-dev", "explicit-review-profile"])
def test_discovery_identity_and_session_use_the_same_explicit_profile(
    tmp_path, monkeypatch, profile
):
    identity = Mock(return_value=subprocess.CompletedProcess([], 0, "111111111111", ""))
    monkeypatch.setattr(script.subprocess, "run", identity)
    client = Mock()
    client.get_paginator.return_value.paginate.return_value = [{"TableMetadataList": []}]
    session = Mock(region_name="us-east-1")
    session.client.return_value = client
    factory = Mock(return_value=session)
    monkeypatch.setattr(script.boto3, "Session", factory)
    monkeypatch.setattr(script, "lake_config", lambda _: settings())
    args = ["--worker", "discover", "--output", str(tmp_path / "selected.json")]
    if profile != "data-migration-dev":
        args += ["--profile", profile]
    assert script.main(args) == 0
    assert identity.call_args.args[0][:3] == ["aws", "--profile", profile]
    factory.assert_called_once_with(profile_name=profile, region_name="us-east-1")
