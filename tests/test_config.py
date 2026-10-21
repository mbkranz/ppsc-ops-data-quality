"""Configuration distinguishes offline authoring, discovery, and live validation."""

from pathlib import Path

import pytest
import yaml

from ppsc_ops_data_quality.config import load_config, validate_bindings, validate_config


@pytest.fixture
def configuration_data():
    path = Path(__file__).parents[1] / "params.yaml"
    data = yaml.safe_load(path.read_text())
    data["athena"].update(
        region="us-east-2",
        database="fixture_lake",
        workgroup="fixture_quality",
        s3_staging_dir="s3://fixture-results/quality/",
        profile="fixture-profile",
    )
    data["tables"]["account"]["name"] = "account_history"
    data["tables"]["contact"]["name"] = "contact_history"
    data["tables"]["survey_result"]["name"] = "survey_history"
    return data


@pytest.fixture
def read_configuration(tmp_path):
    def read(data):
        path = tmp_path / "params.yaml"
        path.write_text(yaml.safe_dump(data))
        return load_config(path)

    return read


def test_discovery_requires_connection_settings_without_table_bindings(
    configuration_data, read_configuration
):
    configuration_data.pop("tables")
    config = read_configuration(configuration_data)

    validate_config(config, live=True, discovery=True)
    assert config.tables == {}
    with pytest.raises(ValueError, match="Missing tables.account"):
        validate_bindings(config)


def test_named_inspection_does_not_require_column_bindings(configuration_data, read_configuration):
    for binding in configuration_data["tables"].values():
        binding.pop("columns")
    config = read_configuration(configuration_data)

    validate_config(config, live=True)
    assert all(not binding.columns for binding in config.tables.values())
    with pytest.raises(ValueError, match="missing column bindings"):
        validate_bindings(config)


def test_tracked_placeholders_are_valid_for_offline_compilation():
    config = load_config(Path(__file__).parents[1] / "params.yaml")

    validate_config(config, live=False)
    validate_bindings(config)
    with pytest.raises(ValueError, match="placeholder"):
        validate_config(config, live=True)


@pytest.mark.parametrize(
    "field_path",
    [
        ("athena", "database"),
        ("athena", "profile"),
        ("tables", "account", "name"),
        ("tables", "account", "columns", "id", "name"),
    ],
)
def test_live_configuration_rejects_unresolved_placeholders(
    configuration_data, read_configuration, field_path
):
    parent = configuration_data
    for part in field_path[:-1]:
        parent = parent[part]
    parent[field_path[-1]] = "<REPLACE_ME>"
    config = read_configuration(configuration_data)

    validate_config(config, live=False)
    validate_bindings(config)
    with pytest.raises(ValueError, match="placeholder"):
        validate_config(config, live=True)


@pytest.mark.parametrize("subject", ["account", "contact", "survey_result"])
def test_validation_requires_both_subject_bindings(configuration_data, read_configuration, subject):
    configuration_data["tables"].pop(subject)

    with pytest.raises(ValueError, match=f"Missing tables.{subject}"):
        validate_bindings(read_configuration(configuration_data))


@pytest.mark.parametrize(
    ("subject", "column"),
    [("account", "valid_from"), ("contact", "account_id"), ("survey_result", "participant_id")],
)
def test_validation_requires_columns_used_by_the_queries(
    configuration_data, read_configuration, subject, column
):
    configuration_data["tables"][subject]["columns"].pop(column)

    with pytest.raises(ValueError, match=f"missing column bindings {column}"):
        validate_bindings(read_configuration(configuration_data))


@pytest.mark.parametrize(
    ("subject", "changes", "message"),
    [
        ("account", {"id": "int64"}, "must be a string"),
        ("contact", {"account_id": "int64"}, "must be a string"),
        ("survey_result", {"participant_id": "int64"}, "must be a string"),
        ("account", {"is_current": "string"}, "must be boolean"),
        (
            "account",
            {"valid_from": "string", "valid_to": "string"},
            "same date/timestamp type",
        ),
        ("account", {"valid_to": "timestamp"}, "same date/timestamp type"),
        ("account", {"loaded_at": "int64"}, "must be a date/timestamp"),
    ],
)
def test_validation_rejects_incompatible_declared_types(
    configuration_data, read_configuration, subject, changes, message
):
    columns = configuration_data["tables"][subject]["columns"]
    for alias, declared_type in changes.items():
        columns[alias]["type"] = declared_type

    with pytest.raises(ValueError, match=message):
        validate_bindings(read_configuration(configuration_data))


def test_multiple_aliases_cannot_hide_a_missing_physical_column(
    configuration_data, read_configuration
):
    columns = configuration_data["tables"]["contact"]["columns"]
    columns["account_id"]["name"] = columns["id"]["name"]

    with pytest.raises(ValueError, match="physical column bindings must be unique"):
        validate_bindings(read_configuration(configuration_data))


def test_interval_confirmation_requires_a_boolean(configuration_data, read_configuration):
    configuration_data["interval_convention_confirmed"] = "false"

    with pytest.raises(ValueError, match="must be true or false"):
        read_configuration(configuration_data)


def test_live_results_location_must_be_s3(configuration_data, read_configuration):
    configuration_data["athena"]["s3_staging_dir"] = "/tmp/athena-results"

    with pytest.raises(ValueError, match="must be an s3:// location"):
        validate_config(read_configuration(configuration_data), live=True)


def test_credential_values_are_not_an_allowed_configuration_field(
    configuration_data, read_configuration
):
    configuration_data["athena"]["aws_secret_access_key"] = "synthetic-disallowed-value"

    with pytest.raises(ValueError, match="Unknown Athena settings") as error:
        read_configuration(configuration_data)
    assert "synthetic-disallowed-value" not in str(error.value)


def test_configuration_retains_physical_names_and_serializable_run_settings(
    configuration_data, read_configuration
):
    configuration_data["interval_convention_confirmed"] = True
    configuration_data["load_completion_evidence"] = "Synthetic completed-delivery fixture"
    config = read_configuration(configuration_data)

    validate_config(config, live=True)
    validate_bindings(config)
    recorded = config.as_dict()

    assert config.tables["account"].columns["id"].name == "Id"
    assert config.tables["contact"].columns["account_id"].name == "AccountId"
    assert recorded["output"] == "build/runs"
    assert recorded["interval_convention_confirmed"] is True
    assert recorded["load_completion_evidence"] == "Synthetic completed-delivery fixture"
