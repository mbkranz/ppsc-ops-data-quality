"""Explicit APMP relationships preserve ordered composite matching and findings."""

import operator
from copy import deepcopy
from functools import reduce

import great_expectations as gx
import great_expectations.expectations as gxe
import ibis
import pytest
from great_expectations.expectations.row_conditions import Column
from ppsc_metadata.lake import LakeBindings

from ppsc_ops_data_quality.core.schemas.contracts import normalize_foreign_keys


def document():
    return {
        "datasets": {
            name.lower(): {
                "native_object": name,
                "catalog": "c",
                "database": "d",
                "relation": name.lower(),
                "ddl_path": f"lake/{name}.sql",
                "columns": {field: field for field in fields},
                "keys": [fields[0]],
                "grain": "row",
            }
            for name, fields in (
                ("Child", ("row_id", "country", "code")),
                ("Parent", ("country", "code")),
            )
        },
        "relationships": [],
    }


def relationship():
    return {
        "source_object": "Child",
        "source_fields": ["country", "code"],
        "target_object": "Parent",
        "target_fields": ["country", "code"],
    }


def declared(form):
    doc = document()
    relation = relationship()
    if form == "reversed":
        relation["source_fields"].reverse()
        relation["target_fields"].reverse()
    doc["relationships"] = [relation]
    return doc


def test_composite_form_preserves_order():
    keys = normalize_foreign_keys(LakeBindings.model_validate(declared("object")))
    assert len(keys) == 1
    assert keys[0].model_dump() == {
        "source_object": "Child",
        "source_fields": ("country", "code"),
        "target_object": "Parent",
        "target_fields": ("country", "code"),
    }


def test_fresh_binding_values_have_the_same_ordered_pairs():
    first = LakeBindings.model_validate(declared("object"))
    second = LakeBindings.model_validate(first.model_dump())
    assert normalize_foreign_keys(first) == normalize_foreign_keys(second)


@pytest.mark.parametrize(
    "change",
    ["missing", "arity", "ambiguous", "duplicate", "external", "unsupported", "owner", "repeat"],
)
def test_invalid_or_unsupported_relationships_fail_at_boundary(change):
    doc = declared("object")
    relation = doc["relationships"][0]
    if change == "missing":
        relation["target_fields"][1] = "missing"
    elif change == "arity":
        relation["target_fields"].pop()
    elif change == "ambiguous":
        relation.pop("source_fields")
    elif change == "duplicate":
        changed = deepcopy(relation)
        changed["target_fields"].reverse()
        doc["relationships"].append(changed)
    elif change == "external":
        relation["target_object"] = "https://example.invalid/Parent"
    elif change == "unsupported":
        relation["expression"] = "dynamic join"
    elif change == "owner":
        relation["source_object"] = "Unbound"
    elif change == "repeat":
        relation["source_fields"] = ["code", "code"]
    with pytest.raises(ValueError):
        normalize_foreign_keys(LakeBindings.model_validate(doc))


def test_mapped_field_identity_is_not_a_relational_key():
    assert normalize_foreign_keys(LakeBindings.model_validate(document())) == ()


@pytest.mark.parametrize("form", ["object", "reversed"])
def test_native_composite_match_and_gx_findings_are_equivalent(form):
    (key,) = normalize_foreign_keys(LakeBindings.model_validate(declared(form)))
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
