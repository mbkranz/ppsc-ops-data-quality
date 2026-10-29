"""View extraction preserves relation semantics and bounded external effects."""

import json

import ibis
import pandas as pd
import pytest
import sqlglot
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    FLOW_FIELDS,
    projection_lineage,
)
from ppsc_ops_data_quality.io import RelationLocation
from ppsc_ops_data_quality.runtime import prepare_query, query_asset_sql
from ppsc_ops_data_quality.views import (
    ViewConfiguration,
    ViewRequest,
    create_query_view,
    create_view_sql,
    drop_query_view,
    extract_cte_view,
)
from scripts.check_validation import comparisons, synthetic_history_tables


def location(name="expected_view"):
    return RelationLocation(catalog="memory", database="main", relation=name)


@pytest.mark.parametrize(
    "mutation", ["none", "duplicates", "missing_after", "assigned_null", "unknown"]
)
def test_full_flow_view_matches_inline_multiset_and_current_lineage(mutation):
    backend = ibis.duckdb.connect()
    try:
        history = synthetic_history_tables(backend)
        if mutation == "duplicates":
            for table in ("Contact_history", "Account_history", "Survey_Result__c_history"):
                backend.con.execute(f'INSERT INTO "{table}" SELECT * FROM "{table}"')
        elif mutation == "missing_after":
            backend.con.execute('DELETE FROM "Account_history" WHERE valid_to IS NULL')
        elif mutation == "assigned_null":
            backend.con.execute(
                'UPDATE "Survey_Result__c_history" SET "Completion_Status_Timestamp__c"=NULL'
            )
        inline = comparisons(history, eligibility=None if mutation == "unknown" else True)["flow"]
        original = inline.dump()
        expected, short = extract_cte_view(inline, cte_name="Expected_Account", location=location())
        assert original == inline.dump()
        assert "flow_row_id" not in expected.named_selects
        assert expected.named_selects == short.ctes[0].this.named_selects
        assert short.meta["ppsc"]["source_graph"] == inline.meta["ppsc"]["source_graph"]
        backend.con.execute(
            "CREATE VIEW expected_view AS " + expected.sql(dialect="duckdb", comments=False)
        )
        a = backend.con.execute(inline.sql(dialect="duckdb", comments=False)).fetchdf()
        b = backend.con.execute(short.sql(dialect="duckdb", comments=False)).fetchdf()
        pd.testing.assert_frame_equal(a, b)
        assert len(query_asset_sql(short).encode()) < 32_768
        assert len(create_view_sql(expected, ViewRequest(location=location())).encode()) < 262_144
        for query in (expected, short):
            for output in query.meta["ppsc"]["outputs"].values():
                for key in ("value_column", "assigned_column", "deterministic_column"):
                    assert output[key] in query.named_selects
            assert query.meta["ppsc"]["record_identity"]["column"] in query.named_selects
        for field in FLOW_FIELDS:
            lineage = projection_lineage(short)["expected." + field]
            assert lineage["value_column"] == "expected." + field
            assert lineage["native_output_columns"]["value_column"] == "expected__" + field
    finally:
        backend.disconnect()


def test_extract_preserves_scope_and_snapshot_pins():
    inline = sqlglot.parse_one(
        "WITH Expected AS (SELECT id FROM c.d.source), Other AS (SELECT id FROM c.d.observed) "
        "SELECT e.id FROM Expected e LEFT JOIN Other o ON e.id=o.id"
    )
    expected, short = extract_cte_view(inline, cte_name="Expected", location=location())
    pinned = prepare_query(expected, table_versions={("c", "d", "source"): "17"})
    ddl = create_view_sql(pinned, ViewRequest(location=location()))
    sql = query_asset_sql(short, table_versions={("c", "d", "observed"): "19"})
    assert "FOR VERSION AS OF 17" in ddl
    assert "FOR VERSION AS OF 19" in sql
    assert "FOR VERSION AS OF 17" not in sql
    assert '"expected_view" FOR VERSION' not in sql
    assert '"memory"."main"."expected_view"' in sql
    assert "REPLACE" not in ddl
    with pytest.raises(ValueError, match="outer CTE"):
        extract_cte_view(
            sqlglot.parse_one(
                "WITH x AS (SELECT 1 AS id), y AS (SELECT id FROM x) SELECT id FROM y"
            ),
            cte_name="y",
            location=location(),
        )
    with pytest.raises(ValueError, match="explicit unique"):
        extract_cte_view(
            sqlglot.parse_one("WITH x AS (SELECT * FROM t) SELECT * FROM x"),
            cte_name="x",
            location=location(),
        )


class Athena:
    def __init__(self, state="SUCCEEDED"):
        self.state = state
        self.calls = []
        self.cancelled = []

    def start_query_execution(self, **kwargs):
        self.calls.append(kwargs)
        return {"QueryExecutionId": f"query-{len(self.calls)}"}

    def get_query_execution(self, **kwargs):
        return {
            "QueryExecution": {
                "Status": {"State": self.state, "StateChangeReason": "fixture reason"}
            }
        }

    def stop_query_execution(self, **kwargs):
        self.cancelled.append(kwargs["QueryExecutionId"])


def test_create_drop_receipts_and_size_preflight():
    client = Athena()
    request = ViewRequest(location=location())
    receipt = create_query_view(
        exp.select(exp.alias_(exp.Literal.number(1), "id")),
        request,
        athena_client=client,
        query_options={"WorkGroup": "dq"},
    )
    assert receipt.query_id == "query-1"
    assert client.calls[0]["QueryExecutionContext"] == {"Catalog": "memory", "Database": "main"}
    assert (
        drop_query_view(receipt, athena_client=client, query_options={}, timeout_seconds=60)
        == "query-2"
    )
    assert client.calls[-1]["QueryString"].startswith("DROP VIEW")
    with pytest.raises(ValueError, match="262144"):
        create_query_view(
            exp.select(exp.alias_(exp.Literal.string("x" * 262144), "huge")),
            request,
            athena_client=client,
            query_options={},
        )
    assert len(client.calls) == 2  # Oversized CREATE was never submitted.


def test_failed_and_timed_out_creation_retains_query_identity(monkeypatch):
    from ppsc_ops_data_quality import runtime

    query = exp.select(exp.alias_(exp.Literal.number(1), "id"))
    request = ViewRequest(location=location())
    with pytest.raises(ValueError, match=r"failed \(query-1\).*fixture reason"):
        create_query_view(query, request, athena_client=Athena("FAILED"), query_options={})
    ticks = iter([0, 61])
    monkeypatch.setattr(runtime, "monotonic", lambda: next(ticks))
    client = Athena("RUNNING")
    with pytest.raises(TimeoutError, match="query-1"):
        create_query_view(query, request, athena_client=client, query_options={})
    assert client.cancelled == ["query-1"]


def test_view_settings_reject_ambiguous_configuration():
    for values in (
        {"database": "a.b"},
        {"database": "dq", "replace": True},
        {"database": "dq", "timeout_seconds": 0},
    ):
        with pytest.raises(ValueError):
            ViewConfiguration.model_validate(values)


def test_status_and_cancellation_errors_retain_submitted_query_id(monkeypatch):
    from ppsc_ops_data_quality import runtime

    class Unavailable(Athena):
        def get_query_execution(self, **kwargs):
            raise OSError("status unavailable")

    class CannotCancel(Athena):
        def stop_query_execution(self, **kwargs):
            raise OSError("cancellation unavailable")

    request = ViewRequest(location=location())
    query = exp.select(exp.alias_(exp.Literal.number(1), "id"))
    with pytest.raises(RuntimeError, match="query-1"):
        create_query_view(query, request, athena_client=Unavailable(), query_options={})
    ticks = iter([0, 61])
    monkeypatch.setattr(runtime, "monotonic", lambda: next(ticks))
    with pytest.raises(TimeoutError, match=r"query-1.*cancellation failed"):
        create_query_view(query, request, athena_client=CannotCancel("RUNNING"), query_options={})


def test_gx_reads_real_view_and_publishes_dependency_definition(tmp_path):
    import great_expectations as gx
    import sqlalchemy as sa

    from ppsc_ops_data_quality.runtime import (
        guard_query_size,
        prepare_validation,
        run_validations_with_reports,
    )

    database = tmp_path / "gx.sqlite"
    engine = sa.create_engine(f"sqlite:///{database}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE source (id TEXT, expected INTEGER, observed INTEGER)"
        )
        connection.exec_driver_sql("INSERT INTO source VALUES ('a', 1, 1), ('b', NULL, NULL)")
        connection.exec_driver_sql("CREATE VIEW expected_view AS SELECT id, expected FROM source")
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_sql(
        name="view_source", connection_string=f"sqlite:///{database}", create_temp_table=False
    )
    gx_engine = source.get_execution_engine()
    listener, sizes = guard_query_size(gx_engine.engine)
    query = sqlglot.parse_one(
        'SELECT e.id AS validation_record_id, e.expected AS "expected.F", o.observed AS "observed.F" FROM expected_view e JOIN source o ON e.id=o.id'
    )
    suite = context.suites.add(
        gx.ExpectationSuite(
            name="view_pairs",
            expectations=[
                gx.expectations.ExpectColumnPairValuesToBeEqual(
                    column_A="expected.F",
                    column_B="observed.F",
                    ignore_row_if="both_values_are_missing",
                )
            ],
        )
    )
    definition, _ = prepare_validation(context, source, query, suite, name="view_pairs")
    dependencies = [
        {
            "relation": "expected_view",
            "definition_sql": "CREATE VIEW expected_view AS SELECT id, expected FROM source",
        }
    ]
    try:
        results = run_validations_with_reports(
            context,
            [definition],
            run_directory=tmp_path / "reports",
            sources={
                "view_pairs": {
                    "source_tables": ["source"],
                    "source_query": definition.data.data_asset.query,
                    "source_query_dialect": "sqlite",
                    "query_dependencies": dependencies,
                }
            },
        )
        assert results["view_pairs"].success
        path = tmp_path / "reports/queries/000_view_pairs.dependencies.json"
        assert json.loads(path.read_text()) == dependencies
        assert any(
            p.endswith(".dependencies.json")
            for p in json.loads((tmp_path / "reports/manifest.json").read_text())["artifacts"]
        )
        assert sizes and max(sizes) < 10000
    finally:
        sa.event.remove(gx_engine.engine, "before_cursor_execute", listener)
        gx_engine.close()
        engine.dispose()
