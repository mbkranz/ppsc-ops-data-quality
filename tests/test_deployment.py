"""Release integrity, AWS payload compatibility and Glue entry-point behavior."""

import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import boto3
import pytest
from botocore.validate import validate_parameters

from ppsc_ops_data_quality.cli import main as cli_main
from scripts.package_release import package_release
from scripts.plan_deployment import deployment_target, plan_deployment
from scripts.release_artifact import verify_release

ROOT = Path(__file__).resolve().parents[1]


def git(root, *arguments):
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


@pytest.fixture
def release(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    root.mkdir()
    monkeypatch.chdir(root)
    (root / ".gitignore").write_text("build/\n")
    (root / "pyproject.toml").write_text(
        '[project]\nname="ppsc-ops-data-quality"\nversion="0.1.0"\nrequires-python=">=3.11,<3.14"\n'
    )
    (root / "glue/scripts").mkdir(parents=True)
    shutil.copyfile(
        ROOT / "glue/scripts/validate_history.py", root / "glue/scripts/validate_history.py"
    )
    shutil.copyfile(ROOT / "glue/job.yaml", root / "glue/job.yaml")
    directory = root / "build/release"
    (directory / "dependencies").mkdir(parents=True)
    (directory / "project").mkdir()
    with ZipFile(directory / "project/ppsc_ops_data_quality-0.1.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr(
            "ppsc_ops_data_quality-0.1.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: ppsc-ops-data-quality\nVersion: 0.1.0\nRequires-Python: >=3.11,<3.14\n",
        )
    archive = package_release(directory)
    import yaml

    (root / "dvc.yaml").write_text(
        yaml.safe_dump(
            {"stages": {"bundle": {"cmd": "synthetic", "outs": [str(archive.relative_to(root))]}}}
        )
    )
    (root / "dvc.lock").write_text(
        yaml.safe_dump(
            {
                "schema": "2.0",
                "stages": {
                    "bundle": {
                        "outs": [
                            {
                                "path": str(archive.relative_to(root)),
                                "hash": "md5",
                                "md5": hashlib.md5(archive.read_bytes()).hexdigest(),
                            }
                        ]
                    }
                },
            }
        )
    )
    git(root, "init", "-q")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "add", ".")
    git(root, "commit", "-qm", "Synthetic release")
    return root


@pytest.fixture
def environment(tmp_path):
    config = tmp_path / "environments.yaml"
    config.write_text("""environments:
  dev:
    account_id: '123456789012'
    region: us-east-1
    artifact_s3_uri: s3://example-artifacts/quality/
    glue_role: arn:aws:iam::123456789012:role/glue-quality
    job_name: quality-dev
""")
    return config


def test_bundle_reassembly_and_final_only_verification(release):
    archive = release / "build/release/bundle/dependencies.gluewheels.zip"
    original = archive.read_bytes()
    archive.unlink()
    assert package_release(release / "build/release").read_bytes() == original
    with ZipFile(archive) as bundle:
        assert len(bundle.namelist()) == 1
        assert bundle.getinfo(bundle.namelist()[0]).date_time == (1980, 1, 1, 0, 0, 0)
    shutil.rmtree(release / "build/release/project")
    shutil.rmtree(release / "build/release/dependencies")
    assert verify_release(git(release, "rev-parse", "HEAD")) == archive


def test_corrupt_or_wrong_revision_bundle_fails(release):
    revision = git(release, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="requested release"):
        verify_release("a" * 40)
    (release / "build/release/bundle/dependencies.gluewheels.zip").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="DVC lock"):
        verify_release(revision)


def test_dirty_source_fails_even_when_bundle_matches(release):
    (release / "glue/scripts/validate_history.py").write_text("changed driver")
    with pytest.raises(ValueError, match="checkout contains"):
        verify_release(git(release, "rev-parse", "HEAD"))


def test_plan_payloads_match_sdk_and_selected_release(release, environment, tmp_path):
    output = tmp_path / "plan"
    revision = git(release, "rev-parse", "HEAD")
    plan_deployment(
        config=environment,
        account="123456789012",
        environment="dev",
        revision=revision,
        output=output,
    )
    model = boto3.Session()._session.get_service_model("glue")
    for operation, filename in [("CreateJob", "create-job.json"), ("UpdateJob", "update-job.json")]:
        validate_parameters(
            json.loads((output / filename).read_text()),
            model.operation_model(operation).input_shape,
        )
    target = json.loads((output / "target.json").read_text())
    assert target["release_uri"].endswith(revision)
    assert len(target["artifacts"]) == 2
    payload = json.loads((output / "create-job.json").read_text())
    assert payload["DefaultArguments"]["--release_revision"] == revision
    assert payload["DefaultArguments"]["--python-modules-installer-option"] == "--no-index"
    assert "--release_manifest_uri" not in payload["DefaultArguments"]
    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize("failure", [None, "account", "conflict", "mutation", "put"])
def test_immutable_staging_precedes_job_activation(release, environment, tmp_path, failure):
    from types import SimpleNamespace

    from botocore.exceptions import ClientError
    from botocore.response import StreamingBody

    from scripts.apply_deployment import apply_deployment

    plan = tmp_path / "plan"
    plan_deployment(
        config=environment,
        account="123456789012",
        environment="dev",
        revision=git(release, "rev-parse", "HEAD"),
        output=plan,
    )
    target = json.loads((plan / "target.json").read_text())
    events, objects = [], {}

    def head_object(**params):
        if params["Key"] not in objects:
            raise ClientError(
                {"Error": {"Code": "404"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
                "HeadObject",
            )
        return {"ContentLength": len(objects[params["Key"]])}

    def get_object(**params):
        content = objects[params["Key"]]
        return {"Body": StreamingBody(io.BytesIO(content), len(content))}

    def put_object(**params):
        assert params["IfNoneMatch"] == "*"
        assert params["ExpectedBucketOwner"] == "123456789012"
        if failure == "put":
            raise RuntimeError("injected upload failure")
        events.append("put")
        objects[params["Key"]] = params["Body"].read()

    desired = json.loads((plan / "update-job.json").read_text())["JobUpdate"]
    glue = SimpleNamespace(
        create_job=lambda **kw: events.append("create"),
        get_job=lambda **kw: {"Job": desired},
        update_job=lambda **kw: events.append("update"),
    )
    s3 = SimpleNamespace(head_object=head_object, get_object=get_object, put_object=put_object)
    sts = SimpleNamespace(
        get_caller_identity=lambda: {
            "Account": "999999999999" if failure == "account" else "123456789012"
        }
    )
    session = SimpleNamespace(
        client=lambda service, **kw: {"sts": sts, "s3": s3, "glue": glue}[service]
    )
    if failure == "conflict":
        objects[target["artifacts"][-1]["uri"].split("/", 3)[-1]] = b"wrong bytes"
    if failure == "mutation":
        (release / "glue/scripts/validate_history.py").write_text("mutated")
    if failure:
        with pytest.raises((ValueError, RuntimeError)):
            apply_deployment(plan, "create", session=session)
        assert not events
    else:
        assert apply_deployment(plan, "create", session=session).status == "complete"
        assert events == ["put", "put", "create"]
        events.clear()
        result = apply_deployment(plan, "update", session=session)
        assert result.job == "unchanged" and events == []
        assert all(item.outcome == "unchanged" for item in result.artifacts)


@pytest.mark.parametrize(
    "account,name,error",
    [
        ("999999999999", "dev", "Unknown AWS account"),
        ("123456789012", "prod", "Unknown AWS account"),
    ],
)
def test_account_and_environment_must_agree(environment, account, name, error):
    with pytest.raises(ValueError, match=error):
        deployment_target(environment, account, name)


def test_role_account_must_match_target(environment):
    environment.write_text(
        environment.read_text().replace("iam::123456789012", "iam::999999999999")
    )
    with pytest.raises(ValueError, match="execution role"):
        deployment_target(environment, "123456789012", "dev")


def glue_driver():
    spec = importlib.util.spec_from_file_location(
        "validate_history", ROOT / "glue/scripts/validate_history.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_glue_calls_shared_runner_with_verified_config_and_provenance(monkeypatch):
    from ppsc_ops_data_quality import glue as module
    from ppsc_ops_data_quality.account_to_survey_results.workflow import ValidationOutcome

    content = re.sub(
        r"REPLACE_WITH_[A-Z_]+", "fixture", (ROOT / "params.example.yaml").read_text()
    ).encode()
    captured = {}

    def validate(config, *, run_directory, run_metadata, athena_client_factory):
        assert callable(athena_client_factory)
        captured.update(run_metadata)
        assert config.athena.region == "fixture"
        assert run_directory.name == "run"
        return ValidationOutcome(
            report_run_id="test",
            report_manifest_uri="s3://reports/test",
            success=False,
            validations={},
        )

    class S3:
        def get_object(self, **kwargs):
            assert kwargs == {"Bucket": "example-config", "Key": "runs/one.yaml"}
            return {"Body": io.BytesIO(content)}

    monkeypatch.setattr(module, "run_validation", validate)
    arguments = [
        "--config_uri",
        "s3://example-config/runs/one.yaml",
        "--config_sha256",
        hashlib.sha256(content).hexdigest(),
        "--release_revision",
        "a" * 40,
        "--JOB_NAME",
        "quality-dev",
        "--JOB_RUN_ID",
        "jr_123",
        "--glue-injected-option",
        "ignored",
    ]
    assert module.main(arguments, s3_client=S3()) == 1
    assert captured["glue_job_run_id"] == "jr_123"
    assert captured["release_revision"] == "a" * 40
    arguments[3] = "0" * 64
    with pytest.raises(ValueError, match="SHA256"):
        module.execute_glue(module.resolve_arguments(arguments), s3_client=S3())


def test_validate_cli_rejects_placeholders_before_aws(tmp_path, capsys):
    config = tmp_path / "params.yaml"
    config.write_text((ROOT / "params.example.yaml").read_text())
    assert cli_main(["validate", "--config", str(config), "--run-dir", str(tmp_path / "run")]) == 2
    assert "Replace the example" in capsys.readouterr().err
    assert not (tmp_path / "run").exists()


def test_catalog_binds_only_parquet_prefixes_and_keeps_projection(tmp_path, monkeypatch):
    from scripts.render_report_catalog import render_report_catalog

    monkeypatch.chdir(ROOT)
    config = tmp_path / "runtime.yaml"
    config.write_text(
        """athena:
  region: us-east-1
  work_group: quality
  s3_staging_dir: s3://query-results/quality/
reports:
  s3_uri: s3://reports/quality/
"""
    )
    output = tmp_path / "catalog"
    render_report_catalog(
        config=config, database="quality_reports", first_run_date="2026-10-21", output=output
    )
    sql = "\n".join(path.read_text() for path in sorted(output.glob("*.sql")))
    assert "REPLACE_WITH_" not in sql
    assert "analytics/expectations/run_date=${run_date}/" in sql
    assert "analytics/validations/run_date=${run_date}/" in sql
    assert "/runs/" not in sql
    assert "'projection.run_date.range' = '2026-10-21,NOW'" in sql
    assert (
        json.loads((output / "target.json").read_text())["context"]["Database"] == "quality_reports"
    )


@pytest.mark.parametrize(
    "outcome,code", [(True, 0), (False, 1), ("error", None), ("diagnostic", 0)]
)
def test_account_workflow_runs_both_suites_and_closes_engine(tmp_path, monkeypatch, outcome, code):
    import re
    from types import SimpleNamespace

    from ppsc_ops_data_quality.account_to_survey_results import workflow as job
    from ppsc_ops_data_quality.account_to_survey_results.workflow import (
        load_validation_configuration,
    )
    from ppsc_ops_data_quality.runtime import query_asset_sql

    config = tmp_path / "params.yaml"
    config.write_text(
        re.sub(r"REPLACE_WITH_[A-Z_]+", "fixture", (ROOT / "params.example.yaml").read_text())
    )
    if outcome == "diagnostic":
        import yaml

        values = yaml.safe_load(config.read_text())
        values["require_repeatable_reads"] = False
        values["data_versions"] = {key: {"mode": "mutable"} for key in values["locations"]}
        config.write_text(yaml.safe_dump(values))
    # This test isolates orchestration; native capture compatibility has separate tests.
    from ppsc_ops_data_quality.account_to_survey_results.queries import (
        metadata_inputs as fixture_inputs,
    )

    fixture = fixture_inputs()
    for binding in fixture["tables"].values():
        binding["provisional"] = False
    fixture["field_definitions"] = [{"fixture": True}]
    monkeypatch.setattr(job, "metadata_inputs", lambda *_: fixture)
    monkeypatch.setattr(job, "check_native_columns", lambda inputs: None)
    original_query = job.flow_account_query

    def compose(*args, inputs, **kwargs):
        return original_query(*args, inputs={**inputs, "field_definitions": []}, **kwargs)

    monkeypatch.setattr(job, "flow_account_query", compose)
    closed = []
    import sqlalchemy as sa

    engine = SimpleNamespace(
        engine=sa.create_engine("sqlite://"), close=lambda: closed.append(True)
    )
    source = SimpleNamespace(get_execution_engine=lambda: engine)
    context = SimpleNamespace(
        data_sources=SimpleNamespace(add_sql=lambda **kwargs: source),
        suites=SimpleNamespace(add=lambda suite: suite),
    )
    monkeypatch.setattr(job.gx, "get_context", lambda **kwargs: context)
    prepared = []

    def prepare(
        context,
        source,
        query,
        suite,
        *,
        name,
        metadata,
        sql_path,
        projection_lineage,
        table_versions,
    ):
        assert projection_lineage
        assert len(table_versions) == (
            0 if outcome == "diagnostic" else (3 if name == "flow" else 2)
        )
        prepared.append((name, suite))
        return SimpleNamespace(
            name=name,
            data=SimpleNamespace(
                data_asset=SimpleNamespace(
                    query=query_asset_sql(
                        query, projection_lineage=projection_lineage, table_versions=table_versions
                    )
                )
            ),
        ), {}

    def execute(context, definitions, **kwargs):
        assert [definition.name for definition in definitions] == ["flow", "rollups"]
        assert kwargs["run_metadata"]["release_revision"] == "a" * 40
        assert kwargs["run_metadata"]["configuration_sha256"]
        assert len(kwargs["run_metadata"]["catalog_preflight"]) == 3
        assert kwargs["run_metadata"]["repeatability_established"] is (outcome != "diagnostic")
        assert kwargs["run_metadata"]["validation_mode"] == (
            "diagnostic" if outcome == "diagnostic" else "stable_inputs"
        )
        if outcome == "diagnostic":
            assert kwargs["run_metadata"]["stable_input_assertions"] == "unestablished"
            assert kwargs["run_metadata"]["lake_acceptance"] == "unestablished"
        assert kwargs["sources"]["flow"]["source_tables"] == [
            "fixture.fixture.account_history",
            "fixture.fixture.contact_history",
            "fixture.fixture.survey_results_history",
        ]
        assert len(kwargs["sources"]["flow"]["source_tables"]) == 3
        assert len(kwargs["sources"]["rollups"]["source_tables"]) == 2
        assert kwargs["s3_uri"] == "s3://fixture/ppsc-data-quality/"
        if outcome == "error":
            raise RuntimeError("publication failed")
        reports = kwargs["run_directory"]
        reports.mkdir(parents=True)
        (reports / "manifest.json").write_text(json.dumps({"run_id": "synthetic_run"}))
        return {
            definition.name: SimpleNamespace(success=outcome, statistics={})
            for definition in definitions
        }

    catalog_tables = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "src/ppsc_ops_data_quality/account_to_survey_results/metadata/observed.json"
        ).read_text()
    )["tables"]

    class Athena:
        def get_table_metadata(self, **kwargs):
            table = next(item for item in catalog_tables if item["Name"] == kwargs["TableName"])
            self.selected = {**table, "Parameters": {"table_type": "ICEBERG"}}
            return {"TableMetadata": self.selected}

        def start_query_execution(self, **kwargs):
            assert "FOR VERSION AS OF 123456789" in kwargs["QueryString"]
            return {"QueryExecutionId": "snapshot-schema"}

        def get_query_execution(self, **kwargs):
            return {"QueryExecution": {"Status": {"State": "SUCCEEDED"}}}

        def get_query_results(self, **kwargs):
            # Query result columns retain the selected order, not catalog order.
            from ppsc_ops_data_quality.account_to_survey_results.queries import physical_schema

            inputs = job.metadata_inputs()
            dataset_id = next(
                key
                for key, binding in inputs["tables"].items()
                if binding["relation"] == self.selected["Name"]
            )
            by_name = {item["Name"]: item for item in self.selected["Columns"]}
            return {
                "ResultSet": {
                    "ResultSetMetadata": {
                        "ColumnInfo": [
                            by_name[name] for name in physical_schema(inputs, dataset_id).names
                        ]
                    }
                }
            }

    client = Athena()
    monkeypatch.setattr(job, "prepare_validation", prepare)
    monkeypatch.setattr(job, "run_validations_with_reports", execute)
    if outcome == "error":
        with pytest.raises(RuntimeError, match="publication failed"):
            job.run_validation(
                load_validation_configuration(config),
                run_directory=tmp_path / "run",
                athena_client=client,
                run_metadata={"release_revision": "a" * 40},
            )
    else:
        assert (
            job.run_validation(
                load_validation_configuration(config),
                run_directory=tmp_path / "run",
                athena_client=client,
                run_metadata={"release_revision": "a" * 40},
            ).exit_code
            == code
        )
    assert len(prepared) == 2
    assert closed == [True]


def test_yaml_job_template_configures_hosting_and_rejects_unquoted_accounts(
    release, environment, tmp_path, monkeypatch
):
    import yaml

    target = yaml.safe_load(environment.read_text())
    target["environments"]["dev"]["account_id"] = 123456789012
    environment.write_text(yaml.safe_dump(target))
    with pytest.raises(ValueError, match="Quote account IDs"):
        deployment_target(environment, "123456789012", "dev")
    target["environments"]["dev"]["account_id"] = "123456789012"
    environment.write_text(yaml.safe_dump(target))
    template = yaml.safe_load((ROOT / "glue/job.yaml").read_text())
    template.update(
        Timeout=15, SecurityConfiguration="verified-security", Connections={"Connections": ["vpc"]}
    )
    (release / "glue/job.yaml").write_text(yaml.safe_dump(template))
    git(release, "add", ".")
    git(release, "commit", "-qm", "Custom native hosting")
    output = tmp_path / "custom-plan"
    plan_deployment(
        config=environment,
        account="123456789012",
        environment="dev",
        revision=git(release, "rev-parse", "HEAD"),
        output=output,
    )
    payload = json.loads((output / "create-job.json").read_text())
    assert payload["Timeout"] == 15
    assert payload["SecurityConfiguration"] == "verified-security"
    assert payload["Connections"] == {"Connections": ["vpc"]}
