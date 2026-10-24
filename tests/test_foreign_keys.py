"""Equivalent ODCS declarations preserve composite matching and keyed findings."""

import operator
from copy import deepcopy
from functools import reduce

import great_expectations as gx
import great_expectations.expectations as gxe
import ibis
import pytest
from great_expectations.expectations.row_conditions import Column
from ppsc_metadata.contracts import validate_contract

from ppsc_ops_data_quality.core.schemas.contracts import normalize_foreign_keys


def document():
    return {
        "apiVersion": "v3.2.0",
        "kind": "DataContract",
        "id": "foreign-keys",
        "version": "1",
        "schema": [
            {
                "id": "children",
                "name": "Child",
                "properties": [
                    {"id": f, "name": f, "logicalType": "string"}
                    for f in ("row_id", "country", "code")
                ],
            },
            {
                "id": "parents",
                "name": "Parent",
                "properties": [
                    {"id": f, "name": f, "logicalType": "string"} for f in ("country", "code")
                ],
            },
        ],
    }


def relationship():
    return {
        "type": "foreignKey",
        "from": ["Child.country", "Child.code"],
        "to": ["Parent.country", "Parent.code"],
    }


def declared(form):
    doc = document()
    child = doc["schema"][0]
    relation = relationship()
    if form == "reversed":
        relation["from"].reverse()
        relation["to"].reverse()
    child["relationships"] = [relation]
    return doc


def test_composite_form_preserves_order():
    form = "object"
    keys = normalize_foreign_keys(validate_contract(declared(form)))
    assert len(keys) == 1
    assert keys[0].model_dump() == {
        "source_object": "Child",
        "source_fields": ("country", "code"),
        "target_object": "Parent",
        "target_fields": ("country", "code"),
    }


def test_implicit_property_key_and_object_key_are_equivalent():
    doc = document()
    child = doc["schema"][0]
    child["properties"][2]["relationships"] = [{"type": "foreignKey", "to": "Parent.code"}]
    property_keys = normalize_foreign_keys(validate_contract(doc))
    child["properties"][2].pop("relationships")
    child["relationships"] = [{"type": "foreignKey", "from": "Child.code", "to": "Parent.code"}]
    assert normalize_foreign_keys(validate_contract(doc)) == property_keys


def test_equivalent_duplicate_declarations_collapse_without_reordering_pairs():
    doc = declared("object")
    equivalent = deepcopy(relationship())
    equivalent["from"].reverse()
    equivalent["to"].reverse()
    doc["schema"][0]["relationships"].append(equivalent)
    keys = normalize_foreign_keys(validate_contract(doc))
    assert len(keys) == 1 and keys[0].source_fields == ("country", "code")


@pytest.mark.parametrize(
    "change",
    ["missing", "arity", "ambiguous", "duplicate", "external", "unsupported", "owner", "repeat"],
)
def test_invalid_or_unsupported_relationships_fail_at_boundary(change):
    doc = declared("object")
    relation = doc["schema"][0]["relationships"][0]
    if change == "missing":
        relation["to"][1] = "Parent.missing"
    elif change == "arity":
        relation["to"].pop()
    elif change == "ambiguous":
        relation.pop("from")
    elif change == "duplicate":
        changed = deepcopy(relation)
        changed["to"].reverse()
        doc["schema"][0]["relationships"].append(changed)
    elif change == "external":
        relation["to"] = [
            "https://example.invalid/contract#country",
            "https://example.invalid/contract#code",
        ]
    elif change == "unsupported":
        relation["type"] = "unimplemented"
    elif change == "owner":
        relation["from"] = ["Parent.country", "Parent.code"]
    elif change == "repeat":
        relation["from"] = ["Child.code", "Child.code"]
    with pytest.raises(ValueError):
        normalize_foreign_keys(validate_contract(doc))


def test_field_definition_link_is_not_a_relational_key():
    doc = document()
    doc["schema"][0]["properties"][2]["authoritativeDefinitions"] = [
        {"type": "fieldReference", "url": "#/schema/parents/properties/code"}
    ]
    assert normalize_foreign_keys(validate_contract(doc)) == ()


@pytest.mark.parametrize("form", ["object", "reversed"])
def test_native_composite_match_and_gx_findings_are_equivalent(form):
    (key,) = normalize_foreign_keys(validate_contract(declared(form)))
    source = ibis.memtable(
        {
            "row_id": ["crossed", "valid", "nullable", "missing"],
            "country": ["US", "US", None, "ZZ"],
            "code": ["1", "2", "1", "0"],
        }
    )
    target = ibis.memtable({"country": ["US", "CA"], "code": ["2", "1"]})
    # One conjunction over ordered pairs; independent set checks would miss crossed.
    target = target.mutate(matched=ibis.literal(True))
    joined = source.left_join(
        target,
        [
            source[left] == target[right]
            for left, right in zip(key.source_fields, key.target_fields, strict=True)
        ],
    )
    comparison = joined.select(
        source.row_id,
        applicable=reduce(operator.and_, (source[field].notnull() for field in key.source_fields)),
        matched=target.matched.fill_null(False),
    )
    backend = ibis.duckdb.connect()
    try:
        frame = backend.execute(comparison)
    finally:
        backend.disconnect()
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    batch = (
        context.data_sources.add_pandas(name="relationships")
        .add_dataframe_asset(name="comparison")
        .add_batch_definition_whole_dataframe("whole")
        .get_batch(batch_parameters={"dataframe": frame})
    )
    result = batch.validate(
        gx.ExpectationSuite(
            name="foreign_key",
            expectations=[
                gxe.ExpectColumnValuesToBeInSet(
                    column="matched",
                    value_set=[True],
                    row_condition=Column("applicable") == True,
                )
            ],
        ),
        result_format={"result_format": "COMPLETE", "unexpected_index_column_names": ["row_id"]},
    )
    finding = result.results[0]
    assert not finding.success and not finding.exception_info["raised_exception"]
    assert {row["row_id"] for row in finding.result["unexpected_index_list"]} == {
        "crossed",
        "missing",
    }
    assert finding.result["element_count"] == 3  # Nullable composite reference is out of scope.
