"""Verified APMP aliases, catalog drift and applied snapshot identities."""

from copy import deepcopy

import ibis
import pytest
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    RelationLocation,
    logical_schema,
    source_relation,
    to_sqlglot,
)
from ppsc_ops_data_quality.account_to_survey_results.workflow import ValidationConfiguration
from ppsc_ops_data_quality.runtime import DataVersionBinding, check_catalog


def bundle(tmp_path):
    return {
        "tables": {
            "ledger": {
                "native_object": "Invoice",
                "catalog": "lake",
                "database": "finance",
                "relation": "delivery_42",
                "kind": "table",
                "columns": {"external_id": "Id", "posted_amount": "Amount"},
                "fields": [["external_id", "string"], ["posted_amount", "decimal(12, 2)"]],
                "keys": ["Id"],
                "grain": "invoice",
                "history_fields": [],
                "history_boundaries": [],
                "history_grain": "unestablished",
                "partition_columns": [],
                "provisional": True,
            }
        },
        "relationships": [],
        "flow": {},
        "source_catalog": {},
        "rollups": {},
    }


class Catalog:
    def __init__(self):
        self.table = {
            "Name": "delivery_42",
            "TableType": "EXTERNAL_TABLE",
            "Parameters": {"table_type": "ICEBERG"},
            "Columns": [
                {"Name": "external_id", "Type": "string"},
                {"Name": "posted_amount", "Type": "decimal(12,2)"},
            ],
            "PartitionKeys": [],
        }
        self.queries = []

    def get_table_metadata(self, **kwargs):
        assert kwargs == {
            "CatalogName": "lake",
            "DatabaseName": "finance",
            "TableName": "delivery_42",
        }
        return {"TableMetadata": deepcopy(self.table)}

    def start_query_execution(self, **kwargs):
        self.queries.append(kwargs["QueryString"])
        return {"QueryExecutionId": "schema-probe"}

    def get_query_execution(self, **kwargs):
        return {"QueryExecution": {"Status": {"State": "SUCCEEDED"}}}

    def get_query_results(self, **kwargs):
        return {"ResultSet": {"ResultSetMetadata": {"ColumnInfo": self.table["Columns"][:2]}}}


def preflight(inputs, client, *, version=None, stable=False):
    return check_catalog(
        inputs,
        dataset_ids=("ledger",),
        locations={
            "ledger": RelationLocation(catalog="lake", database="finance", relation="delivery_42")
        },
        data_versions={"ledger": version or DataVersionBinding()},
        athena_client=client,
        query_options={},
        require_repeatable_reads=stable,
    )


def test_physical_names_are_executable_aliases_and_nulls_survive(tmp_path):
    inputs = bundle(tmp_path)
    backend = ibis.duckdb.connect()
    try:
        backend.con.execute(
            "CREATE TABLE delivery_42 AS SELECT 'one' AS external_id, CAST(NULL AS DECIMAL(12,2)) AS posted_amount"
        )
        catalog = backend.con.execute("SELECT current_database()").fetchone()[0]
        relation = source_relation(
            inputs,
            "ledger",
            location=RelationLocation(catalog=catalog, database="main", relation="delivery_42"),
        )
        assert relation.schema() == logical_schema(inputs, "ledger")
        sql = to_sqlglot(relation).sql(dialect="duckdb")
        assert '"external_id"' in sql and '"posted_amount"' in sql and '"delivery_42"' in sql
        rows = backend.con.execute(sql).fetchall()
        assert rows == [("one", None)]
    finally:
        backend.disconnect()


def test_unreferenced_additions_are_recorded_without_retyping_selected_fields(tmp_path):
    inputs, client = bundle(tmp_path), Catalog()
    client.table["Columns"].append({"Name": "unrelated", "Type": "uniontype<int,string>"})
    result = preflight(inputs, client)[0]
    assert result.compatible and result.additional_columns == ("unrelated",)
    assert not result.repeatability_established
    assert any("Mutable input" in text for text in result.limitations)
    assert not client.queries


@pytest.mark.parametrize("change", ["missing", "type", "partition", "kind", "identity"])
def test_breaking_catalog_drift_blocks_before_validation_queries(tmp_path, change):
    inputs, client = bundle(tmp_path), Catalog()
    if change == "missing":
        client.table["Columns"].pop()
    elif change == "type":
        client.table["Columns"][1]["Type"] = "double"
    elif change == "partition":
        client.table["PartitionKeys"] = [{"Name": "day", "Type": "date"}]
    elif change == "kind":
        client.table["TableType"] = "VIRTUAL_VIEW"
    else:
        client.table["Name"] = "unexpected"
    with pytest.raises(ValueError, match="changed|identity"):
        preflight(inputs, client)
    assert not client.queries


def test_unavailable_metadata_and_mutable_stable_assertions_fail_explicitly(tmp_path):
    inputs, client = bundle(tmp_path), Catalog()
    with pytest.raises(ValueError, match="Stable-input assertion unestablished"):
        preflight(inputs, client, stable=True)
    client.get_table_metadata = lambda **kwargs: {}
    with pytest.raises(ValueError, match="unavailable"):
        preflight(inputs, client)


def test_selected_snapshot_is_probed_and_applied_to_every_physical_read(tmp_path):
    inputs, client = bundle(tmp_path), Catalog()
    result = preflight(
        inputs,
        client,
        version=DataVersionBinding(mode="iceberg_snapshot", snapshot_id="123"),
        stable=True,
    )[0]
    assert result.repeatability_established and result.schema_query_execution_id == "schema-probe"
    assert "FOR VERSION AS OF 123" in client.queries[0]
    relation = source_relation(inputs, "ledger")
    other = relation.view()
    query = relation.join(other, relation.Id == other.Id).select(relation.Id, other.Amount)
    ast = to_sqlglot(query, table_versions={("lake", "finance", "delivery_42"): "123"})
    physical = [node for node in ast.find_all(exp.Table) if node.catalog == "lake"]
    assert physical and all(node.args["version"].expression.this == "123" for node in physical)
    assert ast.sql(dialect="athena").count("FOR VERSION AS OF 123") == len(physical)


def test_generated_schema_and_mapping_disagreement_is_rejected(tmp_path):
    inputs = bundle(tmp_path)
    inputs["tables"]["ledger"]["columns"]["missing"] = "Missing"
    with pytest.raises(ValueError, match="schema/mapping"):
        source_relation(inputs, "ledger")


def test_nonempty_legacy_runtime_type_override_has_migration_message():
    with pytest.raises(ValueError, match="Extra inputs"):
        ValidationConfiguration.model_validate({"schema_overrides": {"account": {"x": "string"}}})


def test_query_assets_receive_the_same_snapshot_on_each_metric_source(tmp_path):
    from types import SimpleNamespace

    from ppsc_ops_data_quality.runtime import query_batch_definition

    inputs = bundle(tmp_path)
    relation = source_relation(inputs, "ledger")
    queries = []

    class Source:
        def add_query_asset(self, **kwargs):
            queries.append(kwargs["query"])
            return SimpleNamespace(add_batch_definition_whole_table=lambda **kwargs: "batch")

    for query in (relation, relation.filter(relation.Amount.notnull())):
        assert (
            query_batch_definition(
                Source(),
                to_sqlglot(query),
                name="selected",
                table_versions={("lake", "finance", "delivery_42"): "123"},
            )
            == "batch"
        )
    assert len(queries) == 2
    assert all("FOR VERSION AS OF 123" in query for query in queries)


def test_invalid_selection_never_constructs_an_online_client(tmp_path, monkeypatch):
    import re
    from pathlib import Path

    from ppsc_ops_data_quality.account_to_survey_results import workflow as validation
    from ppsc_ops_data_quality.account_to_survey_results.queries import metadata_receipt
    from ppsc_ops_data_quality.account_to_survey_results.workflow import (
        load_validation_configuration,
    )

    path = tmp_path / "config.yaml"
    path.write_text(
        re.sub(r"REPLACE_WITH_[A-Z_]+", "fixture", Path("params.example.yaml").read_text())
    )
    request = load_validation_configuration(path)
    from ppsc_ops_data_quality.account_to_survey_results.queries import metadata_inputs

    monkeypatch.setattr(validation, "metadata_inputs", lambda *_: metadata_inputs())
    request = request.model_copy(update={"locations": {}})
    calls = []
    with pytest.raises(ValueError, match="Live validation requires"):
        validation.run_validation(
            request,
            run_directory=tmp_path / "never",
            athena_client_factory=lambda: calls.append(True),
        )
    assert not calls and not (tmp_path / "never").exists()
    assert metadata_receipt()["provisional"]


def test_snapshot_column_info_precision_and_scale_are_preserved(tmp_path):
    inputs, client = bundle(tmp_path), Catalog()

    def results(**kwargs):
        return {
            "ResultSet": {
                "ResultSetMetadata": {
                    "ColumnInfo": [
                        {"Name": "external_id", "Type": "varchar"},
                        {"Name": "posted_amount", "Type": "decimal", "Precision": 12, "Scale": 2},
                    ]
                }
            }
        }

    client.get_query_results = results
    result = preflight(
        inputs,
        client,
        version=DataVersionBinding(mode="iceberg_snapshot", snapshot_id="123"),
        stable=True,
    )
    assert result[0].repeatability_established
    client.get_query_results = lambda **kwargs: {
        "ResultSet": {
            "ResultSetMetadata": {
                "ColumnInfo": [
                    {"Name": "external_id", "Type": "varchar"},
                    {"Name": "posted_amount", "Type": "decimal", "Precision": 18, "Scale": 6},
                ]
            }
        }
    }
    with pytest.raises(ValueError, match="historical schema differs"):
        preflight(
            inputs,
            client,
            version=DataVersionBinding(mode="iceberg_snapshot", snapshot_id="123"),
            stable=True,
        )


def test_case_colliding_added_live_column_is_not_harmless(tmp_path):
    inputs, client = bundle(tmp_path), Catalog()
    client.table["Columns"].append({"Name": "EXTERNAL_ID", "Type": "string"})
    with pytest.raises(ValueError, match="case-colliding"):
        preflight(inputs, client)
    assert not client.queries


def test_generated_native_query_types_preserve_precision_timezone_and_order(tmp_path):
    from ppsc_ops_data_quality.account_to_survey_results.queries import physical_schema

    inputs = bundle(tmp_path)
    table = inputs["tables"]["ledger"]
    table["columns"]["observed_at"] = "ObservedAt"
    table["fields"].append(["observed_at", "timestamp('UTC', 6)"])
    schema = physical_schema(inputs, "ledger")
    assert schema.names == ("external_id", "posted_amount", "observed_at")
    assert schema["posted_amount"] == ibis.dtype("decimal(12,2)")
    assert schema["observed_at"] == ibis.dtype("timestamp('UTC',6)")
    with pytest.raises(ValueError, match="Unknown APMP"):
        physical_schema(inputs, "not_selected")


def test_report_sources_follow_executed_sql_and_exclude_unused_locations():
    from ppsc_ops_data_quality.runtime import query_source_tables

    selected = {
        "used": RelationLocation(catalog="lake", database="finance", relation="delivery_42"),
        "unused": RelationLocation(catalog="lake", database="finance", relation="unread_lookup"),
    }
    sql = """WITH delivery_42 AS (
      SELECT external_id FROM "lake"."finance"."delivery_42" FOR VERSION AS OF 123
    ) SELECT external_id FROM delivery_42"""
    assert query_source_tables(sql, locations=selected) == ["lake.finance.delivery_42"]
    with pytest.raises(ValueError, match="unselected physical relation"):
        query_source_tables(
            'SELECT external_id FROM "other"."finance"."delivery_42"', locations=selected
        )
