"""Consumer acceptance against independent history, observations and native Flow metadata."""

import json

import ibis
import pandas as pd
import pytest
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    FLOW_FIELDS,
    flow_account_query,
    metadata_inputs,
    projection_lineage,
)
from ppsc_ops_data_quality.account_to_survey_results.suites import flow_account_suite
from ppsc_ops_data_quality.runtime import prepare_query, query_asset_sql
from scripts.check_validation import (
    AFTER_AT,
    BEFORE_AT,
    EVENT_ID,
    EXECUTION_AT,
    FLOW_RUN_DATE,
    synthetic_history_tables,
)


@pytest.fixture
def lake():
    backend = ibis.duckdb.connect()
    history = synthetic_history_tables(backend)
    yield backend, history
    backend.disconnect()


def query(history, **kwargs):
    return flow_account_query(
        history,
        survey_result_id=EVENT_ID,
        account_before_at=BEFORE_AT,
        execution_at=EXECUTION_AT,
        account_after_at=AFTER_AT,
        flow_run_date=FLOW_RUN_DATE,
        inputs=kwargs.pop("inputs", metadata_inputs()),
        eligibility=kwargs.pop("eligibility", True),
        **kwargs,
    )


def rows(lake, **kwargs):
    backend, history = lake
    return backend.con.execute(
        query(history, **kwargs).sql(dialect="duckdb", comments=False)
    ).fetchdf()


@pytest.mark.parametrize(
    "relation,condition,expected",
    [
        ("Survey_Result__c_history", "TRUE", 2),
        ("Contact_history", "TRUE", 2),
        ("Account_history", "valid_to IS NOT NULL", 2),
        ("Account_history", "valid_to IS NULL", 2),
    ],
)
def test_duplicates_survive_without_context_rejoin_fanout(lake, relation, condition, expected):
    backend, _ = lake
    backend.con.execute(f'INSERT INTO "{relation}" SELECT * FROM "{relation}" WHERE {condition}')
    frame = rows(lake)
    assert len(frame) == expected
    assert not frame.comparison_keys_are_valid.any()
    assert frame.survey_result_id.eq(EVENT_ID).all()


@pytest.mark.parametrize(
    "relation,condition",
    [
        ("Contact_history", "TRUE"),
        ("Account_history", "valid_to IS NOT NULL"),
        ("Account_history", "valid_to IS NULL"),
    ],
)
def test_missing_relationship_and_observation_retained(lake, relation, condition):
    backend, _ = lake
    backend.con.execute(f'DELETE FROM "{relation}" WHERE {condition}')
    frame = rows(lake)
    assert len(frame) == 1
    assert not frame.comparison_keys_are_valid.all() or not frame.flow_evidence_is_complete.all()


def test_assigned_null_unassigned_and_unknown_are_distinct(lake):
    backend, _ = lake
    backend.con.execute(
        'UPDATE "Survey_Result__c_history" SET "Completion_Status_Timestamp__c"=NULL'
    )
    frame = rows(lake)
    assert frame["expected__Basics_Date_Time__c__assigned"].all()
    assert frame["expected__Basics_Date_Time__c"].isna().all()
    assert not frame["expected__Lifestyle_Date_Time__c__assigned"].any()
    assert frame.survey_completion_occurred_on_or_after_launch.isna().all()
    unknown = rows(lake, eligibility=None)
    assert not unknown.flow_evidence_is_complete.any()
    assert unknown["expected__Basics_Date_Time__c__assigned"].isna().all()


def test_observed_values_never_feed_expected_projection(lake):
    backend, _ = lake
    before = rows(lake)
    backend.con.execute(
        'UPDATE "Account_history" SET "Basics_Date_Time__c"=TIMESTAMP \'2000-01-01\' WHERE valid_to IS NULL'
    )
    changed = rows(lake)
    pd.testing.assert_series_equal(
        before["expected__Basics_Date_Time__c"], changed["expected__Basics_Date_Time__c"]
    )
    assert (
        changed["expected__Basics_Date_Time__c"][0] != changed["observed__Basics_Date_Time__c"][0]
    )


def test_old_unchanged_before_is_retained(lake):
    backend, _ = lake
    backend.con.execute(
        'UPDATE "Account_history" SET "Lifestyle_Date_Time__c"=TIMESTAMP \'2001-01-01\''
    )
    frame = rows(lake)
    assert frame["expected__Lifestyle_Date_Time__c"][0].year == 2001
    assert not frame["expected__Lifestyle_Date_Time__c__assigned"][0]


def test_metadata_change_controls_output_not_domain_rules(lake):
    inputs = metadata_inputs()
    node = next(
        n for n in inputs["flow"]["Metadata"]["recordUpdates"] if n["name"] == "updateAccount2001"
    )
    node["inputAssignments"][0]["value"] = {"dateTimeValue": "2000-01-02 00:00:00"}
    assert rows(lake, inputs=inputs)["expected__Basics_Date_Time__c"][0].year == 2000


def test_faithful_and_simplified_preserve_multiset_and_lineage(lake):
    backend, history = lake
    backend.con.execute('INSERT INTO "Contact_history" SELECT * FROM "Contact_history"')
    simple = query(history)
    faithful = query(history, simplify=False)
    a = backend.con.execute(simple.sql(dialect="duckdb", comments=False)).fetchdf()
    b = backend.con.execute(faithful.sql(dialect="duckdb", comments=False)).fetchdf()
    pd.testing.assert_frame_equal(a, b, check_dtype=False)
    assert simple.meta["ppsc"]["source_graph"] == faithful.meta["ppsc"]["source_graph"]
    assert simple.meta["ppsc"]["node_order"] == faithful.meta["ppsc"]["node_order"]
    restored = exp.Expression.load(json.loads(json.dumps(simple.dump())))
    assert restored.meta["ppsc"] == simple.meta["ppsc"]
    assert len(simple.meta["ppsc"]["outputs"]) == 19
    suite = flow_account_suite(
        lineage=projection_lineage(simple), provenance=simple.meta["ppsc"]["lake_bindings"]
    )
    assert suite.meta["metadata_inputs"]["compiler_commit"].startswith("4ce491c")
    check = next(
        e
        for e in suite.expectations
        if e.meta["check_id"] == "observed_Basics_Date_Time__c_equals_expected"
    )
    assert check.meta["ppsc"]["target_field"] == "Account.Basics_Date_Time__c"


def test_scope_safe_versions_and_select_first():
    import sqlglot

    ast = sqlglot.parse_one("WITH x AS (SELECT id FROM c.d.x) SELECT id FROM x")
    prepared = prepare_query(ast, table_versions={("c", "d", "x"): "17"})
    sql = prepared.sql(dialect="athena")
    assert sql.startswith("SELECT") and sql.count("FOR VERSION AS OF 17") == 1
    with pytest.raises(ValueError, match="Conflicting"):
        prepare_query(
            sqlglot.parse_one("SELECT id FROM c.d.x FOR VERSION AS OF 18", read="athena"),
            table_versions={("c", "d", "x"): "17"},
        )
    with pytest.raises(ValueError, match="unread"):
        prepare_query(ast, table_versions={("c", "d", "absent"): "17"})


def test_native_query_fits_gx_base_limit(lake):
    sql = query_asset_sql(query(lake[1]))
    assert len(sql.encode()) < 262144
    assert sql.startswith("SELECT")
    assert all("expected__" + field in sql for field in FLOW_FIELDS)
