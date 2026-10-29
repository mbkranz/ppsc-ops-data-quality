"""Configuration boundaries reject ambiguity before queries or service requests."""

import hashlib
import io
import re
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import yaml

from ppsc_ops_data_quality.account_to_survey_results.workflow import load_validation_configuration
from ppsc_ops_data_quality.glue import ConfigurationResource, read_configuration
from ppsc_ops_data_quality.io import load_yaml


def test_yaml_preserves_temporal_types_and_quoted_account_ids(tmp_path):
    path = tmp_path / "settings.yaml"
    path.write_text("""account_id: '012345678901'
day: 2026-10-21
instant: 2026-10-21T12:00:00Z
""")
    values = load_yaml(path)
    assert values == {
        "account_id": "012345678901",
        "day": date(2026, 10, 21),
        "instant": datetime(2026, 10, 21, 12, tzinfo=UTC),
    }
    path.write_text("athena:\n  region: first\n  region: second\n")
    with pytest.raises(ValueError, match="Duplicate YAML"):
        load_yaml(path)


def test_runtime_config_rejects_unknown_keys_and_incompatible_times(tmp_path):
    path = tmp_path / "params.yaml"
    values = yaml.safe_load(
        re.sub(r"REPLACE_WITH_[A-Z_]+", "fixture", Path("params.example.yaml").read_text())
    )
    values["event"]["execution_at"] = values["event"]["execution_at"].replace(tzinfo=UTC)
    path.write_text(yaml.safe_dump(values))
    with pytest.raises(ValueError, match="comparable"):
        load_validation_configuration(path)
    for key in ("account_before_at", "account_after_at"):
        values["event"][key] = values["event"][key].replace(tzinfo=UTC)
    path.write_text(yaml.safe_dump(values))
    request = load_validation_configuration(path)
    assert request.event.execution_at.tzinfo == UTC
    assert type(request.event.flow_run_date) is date
    values["unexpected"] = True
    path.write_text(yaml.safe_dump(values))
    with pytest.raises(ValueError, match="Extra inputs"):
        load_validation_configuration(path)


def test_verified_resource_closes_body_on_success_and_hash_mismatch():
    content = b"athena: {}\n"
    bodies = []

    class S3:
        def get_object(self, **kwargs):
            assert kwargs == {"Bucket": "configs", "Key": "one.yaml"}
            body = io.BytesIO(content)
            bodies.append(body)
            return {"Body": body}

    request = ConfigurationResource(
        uri="s3://configs/one.yaml", sha256=hashlib.sha256(content).hexdigest()
    )
    receipt = read_configuration(request, s3_client=S3())
    assert receipt.content == content
    assert receipt.sha256 == request.sha256
    assert bodies[-1].closed
    with pytest.raises(ValueError, match="SHA256"):
        read_configuration(ConfigurationResource(uri=request.uri, sha256="0" * 64), s3_client=S3())
    assert bodies[-1].closed


def test_shared_backend_settings_do_not_load_account_workflow():
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
from ppsc_ops_data_quality.runtime import AthenaConfiguration, ReportConfiguration
AthenaConfiguration(region="fixture", database="fixture", s3_staging_dir="s3://fixture/staging", work_group="fixture")
ReportConfiguration(s3_uri="s3://fixture/reports")
assert not any('.account_to_survey_results' in name for name in sys.modules)
""",
        ],
        check=True,
    )
