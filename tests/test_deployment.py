"""Release integrity, AWS payload compatibility and Glue entry-point behavior."""

import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path
from zipfile import ZipFile

import boto3
import pytest
from botocore.validate import validate_parameters

from ppsc_ops_data_quality.cli import main as cli_main
from scripts.package_release import package_release, sha256, verify_bundle
from scripts.plan_deployment import deployment_target, plan_deployment

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def release(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    release = tmp_path / "release"
    (release / "wheels").mkdir(parents=True)
    (release / "project").mkdir()
    (release / "wheels" / "dependency-1-py3-none-any.whl").write_bytes(b"dependency wheel fixture")
    (release / "project" / "ppsc_ops_data_quality-0.1.0-py3-none-any.whl").write_bytes(
        b"project wheel fixture"
    )
    (release / "requirements.txt").write_text("dependency==1\n")
    package_release(release, "a" * 40)
    return release


@pytest.fixture
def environment(tmp_path):
    config = tmp_path / "environments.yaml"
    config.write_text(
        """environments:
  dev:
    account_id: '123456789012'
    region: us-east-1
    artifact_s3_uri: s3://example-artifacts/quality/
    glue_role: arn:aws:iam::123456789012:role/glue-quality
    job_name: quality-dev
"""
    )
    return config


def test_bundle_is_stable_and_contains_all_declared_wheels(release):
    bundle = release / "bundle"
    manifest = verify_bundle(bundle)
    assert manifest["revision"] == "a" * 40
    with ZipFile(bundle / "dependencies.gluewheels.zip") as archive:
        assert sorted(archive.namelist()) == sorted(manifest["wheels"])
        for name in archive.namelist():
            assert hashlib.sha256(archive.read(name)).hexdigest() == manifest["wheels"][name]
            assert archive.getinfo(name).date_time == (1980, 1, 1, 0, 0, 0)
    with pytest.raises(FileExistsError):
        package_release(release, "a" * 40)


@pytest.mark.parametrize("filename", ["validate_history.py", "dependencies.gluewheels.zip"])
def test_modified_release_artifacts_are_rejected(release, filename):
    (release / "bundle" / filename).write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_bundle(release / "bundle")


def test_changed_manifest_is_rejected_after_planning(release):
    bundle = release / "bundle"
    expected = sha256(bundle / "manifest.json")
    with (bundle / "manifest.json").open("a") as stream:
        stream.write(" ")
    with pytest.raises(ValueError, match="changed after"):
        verify_bundle(bundle, expected_manifest_sha256=expected)


def test_plan_payloads_match_the_glue_sdk_and_manifest(release, environment, tmp_path):
    output = tmp_path / "plan"
    plan_deployment(
        config=environment,
        account="123456789012",
        environment="dev",
        bundle=release / "bundle",
        output=output,
    )
    model = boto3.Session()._session.get_service_model("glue")
    for operation, filename in [("CreateJob", "create-job.json"), ("UpdateJob", "update-job.json")]:
        validate_parameters(
            json.loads((output / filename).read_text()),
            model.operation_model(operation).input_shape,
        )
    target = json.loads((output / "target.json").read_text())
    assert target["release_uri"].endswith(sha256(release / "bundle" / "manifest.json"))
    payload = json.loads((output / "create-job.json").read_text())
    assert payload["GlueVersion"] == "5.0"
    assert payload["DefaultArguments"]["--python-modules-installer-option"] == "--no-index"
    assert payload["DefaultArguments"]["--additional-python-modules"].endswith(".gluewheels.zip")
    uploads = (output / "uploads.tsv").read_text().splitlines()
    assert len(uploads) == 4
    assert uploads[-1].endswith("/manifest.json")
    assert all(Path(line.split("\t")[0]).is_file() for line in uploads)
    with pytest.raises(FileExistsError):
        plan_deployment(
            config=environment,
            account="123456789012",
            environment="dev",
            bundle=release / "bundle",
            output=output,
        )


@pytest.mark.parametrize(
    "account,name,error",
    [
        ("999999999999", "dev", "Unknown AWS account"),
        ("123456789012", "prod", "Environment conflicts"),
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
    from ppsc_ops_data_quality.runtime import glue as module
    from ppsc_ops_data_quality.runtime.validation import ValidationOutcome

    content = re.sub(
        r"REPLACE_WITH_[A-Z_]+", "fixture", (ROOT / "params.example.yaml").read_text()
    ).encode()
    captured = {}

    def validate(config, *, run_directory, run_metadata):
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
        "--release_manifest_uri",
        "s3://example-release/manifest.json",
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


@pytest.mark.parametrize("outcome,code", [(True, 0), (False, 1), ("error", None)])
def test_shared_athena_job_runs_both_suites_and_closes_engine(tmp_path, monkeypatch, outcome, code):
    import re
    from types import SimpleNamespace

    from ppsc_ops_data_quality.runtime import validation as job
    from ppsc_ops_data_quality.runtime.configuration import load_validation_configuration

    config = tmp_path / "params.yaml"
    config.write_text(
        re.sub(r"REPLACE_WITH_[A-Z_]+", "fixture", (ROOT / "params.example.yaml").read_text())
    )
    closed = []
    engine = SimpleNamespace(close=lambda: closed.append(True))
    source = SimpleNamespace(get_execution_engine=lambda: engine)
    context = SimpleNamespace(
        data_sources=SimpleNamespace(add_sql=lambda **kwargs: source),
        suites=SimpleNamespace(add=lambda suite: suite),
    )
    monkeypatch.setattr(job.gx, "get_context", lambda **kwargs: context)
    prepared = []

    def prepare(context, source, query, suite, *, name, metadata, sql_path, projection_lineage):
        assert projection_lineage
        prepared.append((name, suite))
        return SimpleNamespace(
            name=name, data=SimpleNamespace(data_asset=SimpleNamespace(query="SELECT 1"))
        ), {}

    def execute(context, definitions, **kwargs):
        assert [definition.name for definition in definitions] == ["flow", "rollups"]
        assert kwargs["run_metadata"]["release_revision"] == "a" * 40
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

    monkeypatch.setattr(job, "prepare_validation", prepare)
    monkeypatch.setattr(job, "run_validations_with_reports", execute)
    if outcome == "error":
        with pytest.raises(RuntimeError, match="publication failed"):
            job.run_validation(
                load_validation_configuration(config),
                run_directory=tmp_path / "run",
                run_metadata={"release_revision": "a" * 40},
            )
    else:
        assert (
            job.run_validation(
                load_validation_configuration(config),
                run_directory=tmp_path / "run",
                run_metadata={"release_revision": "a" * 40},
            ).exit_code
            == code
        )
    assert len(prepared) == 2
    assert closed == [True]


def test_poe_tasks_apply_profiles_and_preserve_run_status(
    release, environment, tmp_path, monkeypatch
):
    """Run real Poe tasks against a fake AWS CLI; never use real credentials."""
    import os
    import subprocess
    import sys

    plan = tmp_path / "plan"
    binaries = tmp_path / "bin"
    binaries.mkdir()
    log = tmp_path / "aws.jsonl"
    executable = binaries / "aws"
    executable.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
assert args[:1] == ['--profile'], args
profile, args = args[1], args[2:]
assert profile == os.environ['EXPECTED_PROFILE'], (profile, args)
with open(os.environ['AWS_TEST_LOG'], 'a') as stream:
    stream.write(json.dumps({'profile': profile, 'args': args}) + '\\n')
if args[:2] == ['sts', 'get-caller-identity']:
    print(os.environ.get('AWS_TEST_ACCOUNT', '123456789012'))
elif args[:2] == ['glue', 'get-job']:
    print(json.dumps(json.loads(Path(os.environ['AWS_TEST_PLAN'], 'update-job.json').read_text())['JobUpdate']))
elif args[:2] == ['glue', 'start-job-run']:
    print('{"JobRunId": "jr_synthetic"}')
elif args[:2] == ['glue', 'get-job-run']:
    print(json.dumps({'State': os.environ.get('AWS_TEST_STATE', 'SUCCEEDED')}))
elif args[:2] in (['s3', 'cp'], ['glue', 'create-job'], ['glue', 'update-job']):
    print('{}')
else:
    raise AssertionError(args)
""")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(binaries) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("AWS_TEST_PLAN", str(plan))
    monkeypatch.setenv("AWS_TEST_LOG", str(log))
    monkeypatch.setenv("EXPECTED_PROFILE", "data-migration-dev")

    def poe(*arguments, expected=0):
        result = subprocess.run(
            [sys.executable, "-m", "poethepoet", *map(str, arguments)],
            text=True,
            capture_output=True,
        )
        assert result.returncode == expected, result.stdout + result.stderr

    poe(
        "plan-deployment",
        "--config",
        environment,
        "--environment",
        "dev",
        "--bundle",
        release / "bundle",
        "--output",
        plan,
    )
    poe("deploy", "--plan", plan, "--operation", "create")
    monkeypatch.setenv("EXPECTED_PROFILE", "alternate")
    poe("deploy", "--plan", plan, "--operation", "update", "--profile", "alternate")
    poe(
        "run-glue",
        "--plan",
        plan,
        "--config-uri",
        "s3://config/run.yaml",
        "--config-sha256",
        "a" * 64,
        "--profile",
        "alternate",
    )
    assert json.loads((plan / "runs/jr_synthetic.json").read_text())["JobRunId"] == "jr_synthetic"
    monkeypatch.setenv("EXPECTED_PROFILE", "data-migration-dev")
    poe("glue-status", "--plan", plan, "--run-id", "jr_synthetic")
    assert json.loads((plan / "runs/jr_synthetic.status.json").read_text())["State"] == "SUCCEEDED"
    monkeypatch.setenv("AWS_TEST_STATE", "FAILED")
    poe("glue-status", "--plan", plan, "--run-id", "jr_synthetic", expected=1)
    before = log.read_text().splitlines()
    monkeypatch.setenv("AWS_TEST_ACCOUNT", "999999999999")
    poe("deploy", "--plan", plan, "--operation", "update", expected=1)
    after = log.read_text().splitlines()
    assert len(after) == len(before) + 1
    assert json.loads(after[-1])["args"][:2] == ["sts", "get-caller-identity"]


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
    (tmp_path / "glue").mkdir()
    (tmp_path / "glue/job.yaml").write_text(yaml.safe_dump(template))
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "custom-plan"
    plan_deployment(
        config=environment,
        account="123456789012",
        environment="dev",
        bundle=release / "bundle",
        output=output,
    )
    payload = json.loads((output / "create-job.json").read_text())
    assert payload["Timeout"] == 15
    assert payload["SecurityConfiguration"] == "verified-security"
    assert payload["Connections"] == {"Connections": ["vpc"]}
