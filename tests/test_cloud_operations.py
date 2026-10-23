"""SDK operations preserve account/drift gates and meaningful partial evidence."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from scripts.glue_operations import RunRequest, StatusRequest, get_glue_status, start_glue_run
from scripts.register_report_catalog import CatalogRequest, register_report_catalog


@pytest.fixture
def cloud(tmp_path):
    plan, catalog = tmp_path / "plan with spaces", tmp_path / "catalog with spaces"
    plan.mkdir()
    catalog.mkdir()
    expected = {
        "Command": {"Name": "glueetl", "ScriptLocation": "s3://artifacts/release/driver.py"},
        "DefaultArguments": {"--release_revision": "a" * 40},
    }
    (plan / "target.json").write_text(
        json.dumps({"account_id": "111111111111", "region": "us-east-1", "job_name": "validation"})
    )
    (plan / "update-job.json").write_text(
        json.dumps({"JobName": "validation", "JobUpdate": expected})
    )
    (catalog / "target.json").write_text(
        json.dumps(
            {
                "region": "us-east-1",
                "work_group": "quality",
                "context": {"Database": "reports"},
                "results": {"OutputLocation": "s3://results/queries/"},
            }
        )
    )
    for name in ("00.sql", "01.sql"):
        (catalog / name).write_text(f"CREATE TABLE report_{name[:2]} (value string);\n")
    glue, athena = Mock(), Mock()
    glue.get_job.return_value = {"Job": expected}
    glue.start_job_run.return_value = {"JobRunId": "jr_123"}
    athena.start_query_execution.side_effect = [
        {"QueryExecutionId": "query-0"},
        {"QueryExecutionId": "query-1"},
    ]
    sts = Mock()
    sts.get_caller_identity.return_value = {"Account": "111111111111"}
    session = Mock()
    session.client.side_effect = lambda service, **kwargs: {
        "sts": sts,
        "glue": glue,
        "athena": athena,
    }[service]
    return SimpleNamespace(
        plan=plan, catalog=catalog, session=session, sts=sts, glue=glue, athena=athena
    )


def request(cloud):
    return RunRequest(
        plan=cloud.plan, config_uri="s3://approved/config.yaml", config_sha256="a" * 64
    )


def test_run_uses_exact_plan_and_retains_run_id(cloud):
    result = start_glue_run(request(cloud), session=cloud.session)
    assert result.status == "submitted" and result.run_id == "jr_123"
    cloud.glue.start_job_run.assert_called_once_with(
        JobName="validation",
        Arguments={"--config_uri": "s3://approved/config.yaml", "--config_sha256": "a" * 64},
    )
    assert json.loads((cloud.plan / "runs/jr_123.json").read_text())["JobRunId"] == "jr_123"


def test_job_drift_prevents_submission(cloud):
    cloud.glue.get_job.return_value = {
        "Job": {"Command": {"ScriptLocation": "s3://other/driver.py"}}
    }
    with pytest.raises(ValueError, match="differs"):
        start_glue_run(request(cloud), session=cloud.session)
    cloud.glue.start_job_run.assert_not_called()
    assert not (cloud.plan / "run.json").exists()


@pytest.mark.parametrize("operation", ["run", "status", "catalog"])
def test_wrong_account_prevents_network_operations(cloud, operation):
    cloud.sts.get_caller_identity.return_value = {"Account": "999999999999"}
    with pytest.raises(ValueError, match="account differs"):
        if operation == "run":
            start_glue_run(request(cloud), session=cloud.session)
        elif operation == "status":
            get_glue_status(StatusRequest(plan=cloud.plan, run_id="jr_123"), session=cloud.session)
        else:
            register_report_catalog(
                CatalogRequest(plan=cloud.plan, catalog=cloud.catalog), session=cloud.session
            )
    cloud.glue.start_job_run.assert_not_called()
    cloud.glue.get_job_run.assert_not_called()
    cloud.athena.start_query_execution.assert_not_called()


def test_lost_submission_response_is_unknown_and_is_not_retried(cloud):
    cloud.glue.start_job_run.side_effect = TimeoutError("response lost")
    result = start_glue_run(request(cloud), session=cloud.session)
    assert result.status == "unknown" and result.run_id is None
    assert json.loads((cloud.plan / "run.json").read_text())["status"] == "unknown"
    assert cloud.glue.start_job_run.call_count == 1


@pytest.mark.parametrize(
    ("state", "outcome"),
    [
        ("RUNNING", "running"),
        ("SUCCEEDED", "succeeded"),
        ("FAILED", "failed"),
        ("TIMEOUT", "failed"),
        ("EXPIRED", "failed"),
    ],
)
def test_status_preserves_terminal_failure_and_persists_evidence(cloud, state, outcome):
    cloud.glue.get_job_run.return_value = {
        "JobRun": {"JobRunState": state, "ErrorMessage": "detail"}
    }
    result = get_glue_status(StatusRequest(plan=cloud.plan, run_id="jr_123"), session=cloud.session)
    assert result.state == state and result.outcome == outcome and result.error == "detail"
    assert json.loads((cloud.plan / "runs/jr_123.status.json").read_text())["outcome"] == outcome


def test_catalog_retains_both_query_ids_and_native_parameters(cloud):
    result = register_report_catalog(
        CatalogRequest(plan=cloud.plan, catalog=cloud.catalog), session=cloud.session
    )
    assert result.status == "submitted"
    assert [item.query_id for item in result.queries] == ["query-0", "query-1"]
    assert cloud.athena.start_query_execution.call_args_list[0].kwargs["WorkGroup"] == "quality"
    assert json.loads((cloud.catalog / "submission.json").read_text())["status"] == "submitted"


def test_partial_catalog_failure_retains_successful_first_submission(cloud):
    cloud.athena.start_query_execution.side_effect = [
        {"QueryExecutionId": "query-0"},
        RuntimeError("second submission failed"),
    ]
    result = register_report_catalog(
        CatalogRequest(plan=cloud.plan, catalog=cloud.catalog), session=cloud.session
    )
    assert result.status == "failed" and [item.query_id for item in result.queries] == ["query-0"]
    persisted = json.loads((cloud.catalog / "submission.json").read_text())
    assert persisted["queries"][0]["query_id"] == "query-0" and persisted["error"]


def test_missing_second_statement_prevents_partial_submission(cloud):
    (cloud.catalog / "01.sql").unlink()
    with pytest.raises(FileNotFoundError):
        register_report_catalog(
            CatalogRequest(plan=cloud.plan, catalog=cloud.catalog), session=cloud.session
        )
    cloud.athena.start_query_execution.assert_not_called()


def test_invalid_public_requests_fail_before_execution():
    with pytest.raises(ValidationError):
        RunRequest(plan="plan", config_uri="https://unapproved/config.yaml", config_sha256="bad")
    with pytest.raises(ValidationError):
        StatusRequest(plan="plan", run_id="../../outside")
