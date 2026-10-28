"""Explicit APMP relationships preserve ordered composite matching and findings."""

import operator
from functools import reduce

import great_expectations as gx
import great_expectations.expectations as gxe
import ibis
import pytest
from great_expectations.expectations.row_conditions import Column


def relationship():
    return {
        "source_object": "Child",
        "source_fields": ["country", "code"],
        "target_object": "Parent",
        "target_fields": ["country", "code"],
    }


@pytest.mark.parametrize("form", ["object", "reversed"])
def test_native_composite_match_and_gx_findings_are_equivalent(form):
    key = relationship()
    if form == "reversed":
        key["source_fields"].reverse()
        key["target_fields"].reverse()
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
            for left, right in zip(key["source_fields"], key["target_fields"], strict=True)
        ],
    )
    comparison = joined.select(
        source.row_id,
        applicable=reduce(
            operator.and_, (source[field].notnull() for field in key["source_fields"])
        ),
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
