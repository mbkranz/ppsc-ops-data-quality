"""Native type evidence is separate from independently parsed lake DDL."""

import json
import shutil
from pathlib import Path

import pytest
import yaml
from salesforce.entities.field_definitions.schemas import to_sqlglot
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    check_native_columns,
    metadata_inputs,
)
from ppsc_ops_data_quality.io import (
    RelationLocation,
    discover_ddl,
    export_ddl,
    load_inputs,
    read_ddl,
)


def test_ddl_read_export_and_exclusive_write(tmp_path):
    path = tmp_path / "lake.sql"
    path.write_text("CREATE TABLE lake.finance.ledger (id VARCHAR, amount DECIMAL(12,0))")
    ddl = read_ddl(path)
    receipt = export_ddl(ddl, path=tmp_path / "export.sql", source="selected catalog")
    assert receipt.sha256 and read_ddl(receipt.path).sql(dialect="athena") == ddl.sql(
        dialect="athena"
    )
    with pytest.raises(FileExistsError):
        export_ddl(ddl, path=receipt.path, source="again")
    for sql in [
        "SELECT 1",
        "CREATE TABLE x (a INT, A VARCHAR)",
        "CREATE TABLE x AS SELECT 1",
        "CREATE TABLE x (a INT); DROP TABLE x",
    ]:
        path.write_text(sql)
        with pytest.raises(ValueError):
            read_ddl(path)


def test_native_decimal_scale_zero_is_preserved_and_loss_rejected():
    native = to_sqlglot(
        {
            "objectName": "Invoice",
            "QualifiedApiName": "Amount",
            "DataType": "Number",
            "Precision": 12,
            "Scale": 0,
        }
    )
    inputs = {
        "field_definitions": [native.dump()],
        "tables": {
            "invoice": {
                "native_object": "Invoice",
                "fields": {"amount": "decimal(12,0)"},
                "columns": {"amount": "Amount"},
                "history_fields": [],
            }
        },
    }
    check_native_columns(inputs)
    inputs["tables"]["invoice"]["fields"]["amount"] = "decimal(11,0)"
    with pytest.raises(ValueError, match="lossy"):
        check_native_columns(inputs)
    inputs["field_definitions"] = []
    with pytest.raises(ValueError, match="Missing native"):
        check_native_columns(inputs)


def test_provisional_profiles_are_not_native_evidence():
    inputs = metadata_inputs()
    assert not inputs["field_definitions"]
    with pytest.raises(ValueError, match="Missing native"):
        check_native_columns(inputs)


def test_api_capture_selection_and_sha_round_trip(tmp_path):
    source = Path("src/ppsc_ops_data_quality/account_to_survey_results/metadata")
    shutil.copytree(source, tmp_path, dirs_exist_ok=True)
    manifest = yaml.safe_load((tmp_path / "inputs.yaml").read_text())
    manifest.update(field_export="fields.json", native_fields=["Account.Count__c"])
    (tmp_path / "inputs.yaml").write_text(yaml.safe_dump(manifest))
    native = [
        {
            "QualifiedApiName": "Account",
            "Fields": {
                "done": True,
                "records": [
                    {
                        "QualifiedApiName": "Count__c",
                        "DataType": "Number",
                        "Precision": 12,
                        "Scale": 0,
                    }
                ],
            },
        }
    ]
    (tmp_path / "fields.json").write_text(json.dumps(native))
    inputs = load_inputs(tmp_path)
    column = exp.Expression.load(inputs["field_definitions"][0])
    assert column.kind.sql() == "DECIMAL(12, 0)"
    assert column.meta["ppsc"]["source_sha256"]
    assert inputs["flow_sha256"] == metadata_inputs()["flow_sha256"]
    native[0]["Fields"]["records"] = []
    (tmp_path / "fields.json").write_text(json.dumps(native))
    with pytest.raises(ValueError, match="incomplete"):
        load_inputs(tmp_path)


def test_discovery_never_executes_ddl():
    class Client:
        def get_table(self, **kwargs):
            assert kwargs == {"DatabaseName": "finance", "Name": "ledger"}
            return {
                "Table": {
                    "Name": "ledger",
                    "StorageDescriptor": {"Columns": [{"Name": "id", "Type": "string"}]},
                }
            }

    ddl = discover_ddl(
        Client(), location=RelationLocation(catalog="lake", database="finance", relation="ledger")
    )
    assert ddl.this.this.catalog == "lake"


def test_compound_components_keep_parent_identity(tmp_path):
    source = Path("src/ppsc_ops_data_quality/account_to_survey_results/metadata")
    shutil.copytree(source, tmp_path, dirs_exist_ok=True)
    manifest = yaml.safe_load((tmp_path / "inputs.yaml").read_text())
    manifest.update(
        field_export="fields.json",
        native_fields=["Account.BillingAddress.Latitude", "Account.ShippingAddress.Latitude"],
    )
    (tmp_path / "inputs.yaml").write_text(yaml.safe_dump(manifest))
    native = [
        {
            "QualifiedApiName": "Account",
            "Fields": {
                "done": True,
                "records": [
                    {
                        "QualifiedApiName": parent,
                        "DataType": "Address",
                        "Particles": {
                            "done": True,
                            "records": [
                                {
                                    "QualifiedApiName": "Latitude",
                                    "DataType": "double",
                                    "IsComponent": True,
                                    "Precision": 12,
                                    "Scale": 8,
                                }
                            ],
                        },
                    }
                    for parent in ["BillingAddress", "ShippingAddress"]
                ],
            },
        }
    ]
    (tmp_path / "fields.json").write_text(json.dumps(native))
    inputs = load_inputs(tmp_path)
    assert [
        exp.Expression.load(d).meta["ppsc"]["target_field"] for d in inputs["field_definitions"]
    ] == manifest["native_fields"]
    native[0]["Fields"]["done"] = False
    (tmp_path / "fields.json").write_text(json.dumps(native))
    with pytest.raises(ValueError, match="Incomplete"):
        load_inputs(tmp_path)
