"""Ops owns physical types and keeps native source evidence through composition."""

import json
from copy import deepcopy
from pathlib import Path

import ibis
import pytest
from sqlglot import exp, parse_one
from test_apmp import Catalog, bundle, preflight

from ppsc_ops_data_quality.account_to_survey_results.inputs import load_inputs
from ppsc_ops_data_quality.account_to_survey_results.metadata import (
    field_definitions,
    source_schema,
)
from ppsc_ops_data_quality.core.queries.sql import to_sqlglot


def typed_inputs():
    return {
        "source_org": "synthetic",
        "source_catalog": {
            "fields": [
                {
                    "EntityDefinition.QualifiedApiName": "Invoice",
                    "FieldDefinition.QualifiedApiName": "Id",
                    "DataType": "id",
                    "Description": "Identifier */ SELECT 1 /* sqlglot.meta injected=true",
                    "IsNillable": False,
                    "Label": "",
                },
                {
                    "EntityDefinition.QualifiedApiName": "Invoice",
                    "FieldDefinition.QualifiedApiName": "Amount",
                    "DataType": "currency",
                    "Precision": 12,
                    "Scale": 0,
                    "Description": "Amount",
                },
            ]
        },
    }


def test_native_ibis_conversion_keeps_original_definitions_separately():
    inputs = typed_inputs()
    before = deepcopy(inputs)
    schema = source_schema(inputs, "Invoice", ("Id", "Amount"))
    assert schema.names == ("Id", "Amount")
    assert schema["Amount"] == ibis.dtype("decimal(12,0)")
    assert all(dtype.nullable for dtype in schema.types)
    definitions = field_definitions(inputs)
    native = definitions["Invoice.Id"]["native"]
    assert native["IsNillable"] is False and native["Label"] == ""
    assert definitions["Invoice.Amount"]["native"]["Scale"] == 0
    assert inputs == before
    with pytest.raises(ValueError, match="distinct"):
        source_schema(inputs, "Invoice", ("Id", "Id"))
    with pytest.raises(ValueError, match="Missing"):
        source_schema(inputs, "Invoice", ("Missing",))


def test_unsupported_field_stays_evidence_without_fabricated_query_type():
    inputs = typed_inputs()
    inputs["source_catalog"]["fields"][1].pop("DataType")
    definitions = field_definitions(inputs)
    assert definitions["Invoice.Amount"]["translation_status"] == "unsupported"
    assert definitions["Invoice.Amount"]["native"]["Scale"] == 0
    with pytest.raises(ValueError, match="type evidence"):
        source_schema(inputs, "Invoice", ("Amount",))


def test_native_metadata_survives_alias_join_cast_and_ast_serialization():
    metadata = field_definitions(typed_inputs())["Invoice.Id"]
    left = ibis.table({"Id": "string", "Amount": "decimal(12,0)"}, name="Invoice")
    right = left.view()
    query = left.left_join(right, left.Id == right.Id).select(
        expected=left.Id.cast("string"),
        observed=right.Id,
    )
    lineage = {
        "expected": {
            "description": metadata["description"],
            "source_entities": ["Invoice.Id"],
            "field_definition": metadata,
            "comparison_role": "expected",
        },
        "observed": {
            "description": "Observed Invoice.Id",
            "source_entities": ["Invoice.Id"],
            "field_definition": metadata,
            "comparison_role": "observed",
        },
    }
    tree = to_sqlglot(query, projection_lineage=lineage)
    for result in (tree, tree.copy(), exp.Expression.load(json.loads(json.dumps(tree.dump())))):
        assert result.selects[0].meta["ppsc"] == lineage["expected"]
        assert result.selects[1].meta["ppsc"] == lineage["observed"]
    text = tree.sql(dialect="athena")
    assert "sqlglot.meta injected" not in text
    reparsed = parse_one(text, read="athena")
    assert reparsed.named_selects == ["expected", "observed"]
    assert not any("injected" in node.meta for node in reparsed.walk())


def test_physical_char_varchar_drift_is_checked_before_ibis_conversion(tmp_path):
    inputs, catalog = bundle(tmp_path), Catalog()
    inputs["tables"]["ledger"]["physical_types"] = {"external_id": "char(18)"}
    inputs["tables"]["ledger"]["fields"][0][1] = "string(18)"
    catalog.table["Columns"][0]["Type"] = "varchar(18)"
    with pytest.raises(ValueError, match="physical types changed"):
        preflight(inputs, catalog)
    assert not catalog.queries


def test_same_list_duplicate_native_declaration_is_rejected(tmp_path):
    inputs, catalog = bundle(tmp_path), Catalog()
    catalog.table["Columns"].append(deepcopy(catalog.table["Columns"][0]))
    with pytest.raises(ValueError, match="Duplicate catalog"):
        preflight(inputs, catalog)


def test_definition_approval_does_not_hide_missing_source_evidence(tmp_path):
    import shutil

    domain = (
        Path(__file__).resolve().parents[1] / "src/ppsc_ops_data_quality/account_to_survey_results"
    )
    shutil.copytree(domain / "definitions", tmp_path / "definitions")
    metadata = tmp_path / "metadata"
    metadata.mkdir()
    (metadata / "source_catalog.json").write_text('{"fields": []}')
    inputs = load_inputs(metadata)
    assert not inputs["source_coverage"]["complete"]
    assert inputs["source_coverage"]["missing_fields"]
    assert not (metadata / "tables.json").exists()
    assert "contract_id" not in inputs
    assert inputs["definition_sha256"]


def test_compound_particles_keep_parent_identity_and_raw_api_name_fallback():
    inputs = typed_inputs()
    inputs["source_catalog"]["fields"] = [
        {
            "EntityDefinition.QualifiedApiName": "Invoice",
            "FieldDefinition.QualifiedApiName": parent,
            "QualifiedApiName": "Latitude",
            "DataType": "double",
            "Precision": 18,
            "Scale": 6,
            "IsComponent": True,
        }
        for parent in ("BillingAddress", "ShippingAddress")
    ]
    result = field_definitions(inputs)
    assert set(result) == {"Invoice.BillingAddress.Latitude", "Invoice.ShippingAddress.Latitude"}
    for key, annotation in result.items():
        assert annotation["target_field"] == key
        assert annotation["source_entities"] == ["FieldDefinition." + key]
    # Missing type evidence must keep those same identities, not collapse them.
    for field in inputs["source_catalog"]["fields"]:
        field.pop("DataType")
    unsupported = field_definitions(inputs)
    assert set(unsupported) == set(result)
    assert all(item["translation_status"] == "unsupported" for item in unsupported.values())


def test_loaded_binding_mutations_cannot_corrupt_subsequent_selection():
    directory = (
        Path(__file__).resolve().parents[1]
        / "src/ppsc_ops_data_quality/account_to_survey_results/metadata"
    )
    original = load_inputs(directory)
    changed = load_inputs(directory)
    changed["tables"]["account"]["keys"].append("bad")
    changed["tables"]["account"]["history_fields"].clear()
    changed["tables"]["account"]["history_boundaries"].clear()
    changed["relationships"][0]["source_fields"].clear()
    assert load_inputs(directory) == original


def test_runtime_override_binds_observed_provenance_to_actual_selected_relation():
    from ppsc_ops_data_quality.account_to_survey_results.lineage import (
        PROJECTION_LINEAGE,
        bound_projection_lineage,
    )
    from ppsc_ops_data_quality.account_to_survey_results.metadata import metadata_inputs
    from ppsc_ops_data_quality.sources.apmp import RelationLocation, source_relation

    inputs = metadata_inputs()
    locations = {
        dataset_id: RelationLocation(
            catalog="actual_catalog", database="actual_db", relation="renamed_" + table["relation"]
        )
        for dataset_id, table in inputs["tables"].items()
    }
    before = deepcopy(PROJECTION_LINEAGE)
    lineage = bound_projection_lineage(inputs, locations)
    name = "observed__Age_at_Time_of_Consent__pc"
    expected_binding = {
        "dataset_id": "account",
        "source_field": "Account.Age_at_Time_of_Consent__pc",
        "catalog": "actual_catalog",
        "database": "actual_db",
        "relation": "renamed_account_history",
        "column": "age_at_time_of_consent__pc",
    }
    assert lineage[name]["physical_bindings"] == [expected_binding]
    assert "physical_bindings" not in PROJECTION_LINEAGE[name]
    assert PROJECTION_LINEAGE == before
    observed = source_relation(inputs, "account", location=locations["account"])
    query = observed.select(**{name: observed.Age_at_Time_of_Consent__pc})
    tree = to_sqlglot(query, projection_lineage=lineage)
    assert '"actual_catalog"."actual_db"."renamed_account_history"' in tree.sql(dialect="athena")
    annotation = tree.selects[0].meta["ppsc"]
    assert annotation["physical_bindings"] == [expected_binding]
    assert annotation["comparison_role"] == "observed"
    assert annotation["field_definition"]["native"]


def test_actual_domain_aliases_and_derived_inputs_retain_native_definitions():
    from ppsc_ops_data_quality.account_to_survey_results.lineage import (
        PROJECTION_LINEAGE,
        bound_projection_lineage,
    )
    from ppsc_ops_data_quality.account_to_survey_results.metadata import metadata_inputs
    from ppsc_ops_data_quality.sources.apmp import RelationLocation, source_relation

    inputs = metadata_inputs()
    locations = {
        dataset_id: RelationLocation(
            catalog="selected", database="actual", relation="renamed_" + table["relation"]
        )
        for dataset_id, table in inputs["tables"].items()
    }
    lineage = bound_projection_lineage(inputs, locations)
    survey = source_relation(inputs, "survey_result", location=locations["survey_result"])
    query = survey.select(
        survey_result_id=survey.Id,
        participant_contact_id=survey.Participant__c,
        survey_completion_timestamp=survey.Completion_Status_Timestamp__c,
    )
    tree = to_sqlglot(query, projection_lineage=lineage)
    expected = {
        "survey_result_id": "Survey_Result__c.Id",
        "participant_contact_id": "Survey_Result__c.Participant__c",
        "survey_completion_timestamp": "Survey_Result__c.Completion_Status_Timestamp__c",
    }
    for projection in tree.selects:
        evidence = projection.meta["ppsc"]
        definition = evidence["field_definition"]
        assert definition["target_field"] == expected[projection.alias_or_name]
        assert definition["native"]["FieldDefinition.QualifiedApiName"]
        assert definition["source_file"] == "source_catalog.json"
        assert definition["source_sha256"] == inputs["source_catalog_sha256"]
        assert evidence["physical_bindings"][0]["relation"] == "renamed_survey_results_history"
    derived = PROJECTION_LINEAGE["expected__Age_at_Time_of_Consent__pc"]
    assert "Contact.Birthdate" in derived["input_field_definitions"]
    assert derived["input_field_definitions"]["Contact.Birthdate"]["native"]
