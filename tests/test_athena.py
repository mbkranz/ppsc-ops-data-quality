"""Use real SQL compilation and isolate only external Athena access."""

from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from ppsc_ops_data_quality import athena
from ppsc_ops_data_quality.config import AthenaSettings, Column, load_config


@pytest.fixture
def athena_config():
    config = load_config(Path(__file__).parents[1] / "params.yaml")
    settings = AthenaSettings(
        region="us-east-2",
        catalog="AwsDataCatalog",
        database="fixture_lake",
        workgroup="fixture_quality",
        s3_staging_dir="s3://fixture-results/quality/",
        profile="fixture-profile",
    )
    names = {"account": "account_history", "account_contact_relation": "acr_history"}
    tables = {
        subject: replace(
            binding,
            catalog=settings.catalog,
            database=settings.database,
            name=names[subject],
        )
        for subject, binding in config.tables.items()
    }
    return replace(config, athena=settings, tables=tables)


@pytest.fixture
def schema_report(athena_config):
    return {
        "tables": {
            subject: {
                "name": binding.name,
                "columns": [
                    {"name": column.name, "declared_type": column.type}
                    for column in binding.columns.values()
                ],
            }
            for subject, binding in athena_config.tables.items()
        }
    }


def test_sources_and_relationship_compile_offline_with_both_snapshots(athena_config, monkeypatch):
    from ppsc_ops_data_quality.run import build_queries

    unexpected_access = Mock(side_effect=AssertionError("Compilation must not access AWS"))
    monkeypatch.setattr(athena, "create_engine", unexpected_access)
    monkeypatch.setattr("pyathena.connect", unexpected_access)
    queries = build_queries(
        athena_config, date(2026, 10, 15), athena.snapshot_time("2026-10-17T07:00:00-05:00")
    )
    query = queries[-1][1]
    for table_name in ("account_history", "acr_history"):
        assert f'"AwsDataCatalog"."fixture_lake"."{table_name}"' in query
    assert query.count("FOR TIMESTAMP AS OF") == 2
    assert query.count("2026-10-17 12:00:00") == 2
    unexpected_access.assert_not_called()


def test_source_quotes_identifiers_without_changing_their_identity(athena_config):
    binding = athena_config.tables["account"]
    columns = {**binding.columns, "id": Column('ID"name', "string")}
    binding = replace(
        binding, catalog='Cat"alog', database='db"name', name='account"name.part', columns=columns
    )
    query = athena.source_table(binding, datetime(2026, 10, 17, 12, tzinfo=UTC))
    assert '"Cat""alog"."db""name"."account""name.part"' in query
    assert '"ID""name" AS "id"' in query


@pytest.mark.parametrize(
    "value",
    [
        "2026-10-17T12:00:00Z",
        "2026-10-17T07:00:00-05:00",
        "2026-10-17T14:30:00+02:30",
    ],
)
def test_snapshot_timestamp_is_normalized_to_utc(value):
    result = athena.snapshot_time(value)

    assert result == datetime(2026, 10, 17, 12, tzinfo=UTC)
    assert result.tzinfo is UTC


@pytest.mark.parametrize("value", ["2026-10-17", "2026-10-17T12:00:00"])
def test_snapshot_timestamp_rejects_a_missing_timezone(value):
    with pytest.raises(ValueError, match="timezone"):
        athena.snapshot_time(value)


def test_source_rejects_a_naive_snapshot_datetime(athena_config):
    with pytest.raises(ValueError, match="timezone"):
        athena.source_table(athena_config.tables["account"], datetime(2026, 10, 17, 12))


def test_compilation_preserves_snapshot_fractional_seconds(athena_config):
    instant = athena.snapshot_time("2026-10-17T07:00:00.123456-05:00")
    query = athena.source_table(athena_config.tables["account"], instant)

    assert "2026-10-17 12:00:00.123456" in query


def test_connection_url_uses_a_profile_and_the_standard_credential_chain(athena_config):
    url = athena.sqlalchemy_url(athena_config)

    assert url.drivername == "awsathena+rest"
    assert url.username is None
    assert url.password is None
    assert url.host == "athena.us-east-2.amazonaws.com"
    assert url.database == "fixture_lake"
    assert dict(url.query) == {
        "catalog_name": "AwsDataCatalog",
        "work_group": "fixture_quality",
        "s3_staging_dir": "s3://fixture-results/quality/",
        "profile_name": "fixture-profile",
    }


def test_discovery_can_list_tables_before_bindings_exist(athena_config, monkeypatch):
    config = replace(athena_config, tables={})
    engine = Mock()
    connection = Mock()
    context = Mock()
    context.__enter__ = Mock(return_value=connection)
    context.__exit__ = Mock(return_value=False)
    engine.connect.return_value = context
    inspector = Mock()
    inspector.get_table_names.return_value = ["account_history", "acr_history"]
    monkeypatch.setattr(athena, "create_engine", Mock(return_value=engine))
    monkeypatch.setattr(athena, "inspect", Mock(return_value=inspector))

    report = athena.inspect_tables(config, discover=True)

    assert report["table_names"] == ["account_history", "acr_history"]
    assert report["tables"] == {}
    inspector.get_table_names.assert_called_once_with(schema="fixture_lake")
    inspector.get_columns.assert_not_called()
    connection.execute.assert_not_called()
    engine.dispose.assert_called_once_with()


def test_preflight_accepts_verified_physical_names_and_types(athena_config, schema_report):
    athena.check_physical_schema(athena_config, schema_report)


def test_preflight_does_not_substitute_canonical_aliases_for_physical_names(
    athena_config, schema_report
):
    schema_report["tables"]["account"]["columns"][0]["name"] = "id"

    with pytest.raises(ValueError, match="physical column 'Id' is missing"):
        athena.check_physical_schema(athena_config, schema_report)


def test_preflight_rejects_incorrect_physical_types_before_projection(athena_config, schema_report):
    schema_report["tables"]["account"]["columns"][0]["declared_type"] = "int64"

    with pytest.raises(ValueError, match="account.id: expected TEXT, found BIGINT"):
        athena.check_physical_schema(athena_config, schema_report)


def test_preflight_preserves_inspection_errors(athena_config, schema_report):
    schema_report["tables"]["account"] = {"error": "AccessDenied: fixture metadata is inaccessible"}

    with pytest.raises(ValueError, match="AccessDenied: fixture metadata is inaccessible"):
        athena.check_physical_schema(athena_config, schema_report)


def test_preflight_allows_unreported_timestamp_precision(athena_config, schema_report):
    for column in schema_report["tables"]["account"]["columns"]:
        if column["name"] == "loaded_at":
            column["declared_type"] = "timestamp(6)"

    athena.check_physical_schema(athena_config, schema_report)


def test_preflight_rejects_reported_timestamp_precision_mismatch(athena_config, schema_report):
    account = athena_config.tables["account"]
    account = replace(
        account,
        columns={**account.columns, "loaded_at": Column("loaded_at", "timestamp(6)")},
    )
    config = replace(athena_config, tables={**athena_config.tables, "account": account})
    for column in schema_report["tables"]["account"]["columns"]:
        if column["name"] == "loaded_at":
            column["declared_type"] = "timestamp(3)"

    with pytest.raises(ValueError, match="expected TIMESTAMP"):
        athena.check_physical_schema(config, schema_report)
