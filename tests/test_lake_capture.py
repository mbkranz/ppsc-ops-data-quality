"""Explicit selected Glue capture retains storage/view evidence and performs no DDL."""

import json

import pytest

from scripts.capture_lake import CaptureRequest, capture_resources


def test_selected_capture_retains_storage_and_view_definitions(tmp_path):
    native = {
        "Name": "orders",
        "DatabaseName": "saved",
        "TableType": "EXTERNAL_TABLE",
        "StorageDescriptor": {
            "Location": "s3://synthetic/orders/",
            "SerdeInfo": {"SerializationLibrary": "native"},
        },
        "ViewOriginalText": "native view definition",
    }

    class Client:
        def get_table(self, **kwargs):
            assert kwargs == {
                "CatalogId": "123456789012",
                "DatabaseName": "saved",
                "Name": "orders",
            }
            return {"Table": native}

    receipt = capture_resources(
        CaptureRequest(account_id="123456789012", database="saved", relations=("orders",)),
        glue_client=Client(),
        output_path=tmp_path / "selected.json",
    )
    assert json.loads(receipt.output_path.read_text())["tables"] == [native]


def test_failed_selected_capture_preserves_existing_snapshot(tmp_path):
    output = tmp_path / "selected.json"
    output.write_text("previous")

    class Client:
        def get_table(self, **kwargs):
            raise ValueError("unavailable")

    with pytest.raises(ValueError, match="unavailable"):
        capture_resources(
            CaptureRequest(account_id="123456789012", database="saved", relations=("orders",)),
            glue_client=Client(),
            output_path=output,
        )
    assert output.read_text() == "previous"
