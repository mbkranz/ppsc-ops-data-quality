import unittest
from unittest.mock import Mock

import ibis
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    ROLLUP_ACCOUNT_FIELDS,
    expected_survey_rollups,
    rollup_account_comparison,
    to_sqlglot,
)
from ppsc_ops_data_quality.runtime import query_batch_definition


class QueryAssetTests(unittest.TestCase):
    def test_aliases_preserve_self_joins_and_literal_values(self):
        backend = ibis.duckdb.connect()
        try:
            table = backend.create_table(
                "Account", ibis.memtable({"Id": ["a", "b"], "label": ["t1", "t2"]})
            )
            other = table.view()
            expression = table.left_join(other, table.Id == other.Id).select(
                table.Id, table.label, other.label.name("t3"), marker=ibis.literal("t7")
            )
            query = to_sqlglot(expression)
            actual = backend.raw_sql(query.sql(dialect="duckdb")).fetchall()
            self.assertCountEqual(actual, [("a", "t1", "t1", "t7"), ("b", "t2", "t2", "t7")])
            self.assertEqual(query.named_selects, ["Id", "label", "t3", "marker"])
            self.assertEqual(
                {node.name for node in query.find_all(exp.TableAlias)}, {"Account", "Account_2"}
            )
        finally:
            backend.disconnect()

    def test_inlining_cte_with_the_same_name_as_its_physical_source(self):
        backend = ibis.duckdb.connect()
        try:
            table = backend.create_table("Account", ibis.memtable({"Id": ["a", "a"]}))
            expression = table.alias("Account").mutate(marker=ibis.literal("Account"))
            query = to_sqlglot(expression)
            self.assertIsNone(query.args.get("with_"))
            self.assertCountEqual(
                backend.raw_sql(query.sql(dialect="duckdb")).fetchall(),
                [("a", "Account"), ("a", "Account")],
            )
        finally:
            backend.disconnect()

    def test_rollup_grouping_preserves_identical_observations_and_missing_parents(self):
        backend = ibis.duckdb.connect()
        try:
            account = backend.create_table(
                "Account",
                ibis.memtable(
                    {
                        "Id": ["a1", "a1", "a2", None],
                        "PersonContactId": ["c1", "c1", "c2", "c3"],
                        "IsPersonAccount": [True, True, True, True],
                    }
                ),
            )
            survey = backend.create_table(
                "Survey",
                ibis.memtable(
                    {
                        "Participant__c": ["c1", "c1", "c3"],
                        "Completion_Status__c": ["Complete"] * 3,
                        "Survey_Index_Number__c": ["1001"] * 3,
                        "Consent_Status__c": ["Yes"] * 3,
                        "Consent_Revoked__c": [False] * 3,
                    }
                ),
            )
            observed = backend.create_table(
                "Observed",
                ibis.memtable(
                    {
                        "Id": ["a1", "a1", "observed_only"],
                        **{field: [0, 0, 0] for field in ROLLUP_ACCOUNT_FIELDS},
                    }
                ),
            )
            comparison = rollup_account_comparison(
                expected_survey_rollups(account, survey), observed
            )
            self.assertCountEqual(
                backend.raw_sql(
                    backend.compile(
                        comparison.select(
                            "expected.Id",
                            "person_contact_id",
                            "observed.Id",
                            "expected.Count_of_Completed_Primary_Consent__pc",
                        )
                    )
                ).fetchall(),
                [
                    ("a1", "c1", "a1", 4),
                    ("a1", "c1", "a1", 4),
                    ("a2", "c2", None, 0),
                    (None, "c3", None, 1),
                    (None, None, "observed_only", None),
                ],
            )
            self.assertCountEqual(
                backend.raw_sql(to_sqlglot(comparison).sql(dialect="duckdb")).fetchall(),
                backend.raw_sql(backend.compile(comparison)).fetchall(),
            )
        finally:
            backend.disconnect()

    def test_utf8_query_limit_fails_before_registering_an_asset(self):
        source = Mock()
        expression = ibis.table({"Id": "string"}, name="input").mutate(
            note=ibis.literal("é" * 140000)
        )
        with self.assertRaisesRegex(ValueError, "262144-byte"):
            query_batch_definition(source, to_sqlglot(expression), name="oversized")
        source.add_query_asset.assert_not_called()

    def test_registration_does_not_fetch_batch_or_create_views(self):
        data_source = Mock()
        query = ibis.table({"Id": "string"}, name="history")
        definition = query_batch_definition(
            data_source, to_sqlglot(query), name="run_comparison", metadata={"run_id": "run_1"}
        )
        call = data_source.add_query_asset.call_args
        self.assertEqual(call.kwargs["batch_metadata"], {"run_id": "run_1"})
        self.assertRegex(call.kwargs["query"], "^SELECT\\s")
        self.assertNotIn("CREATE VIEW", call.kwargs["query"])
        self.assertIs(
            definition,
            data_source.add_query_asset.return_value.add_batch_definition_whole_table.return_value,
        )
        definition.get_batch.assert_not_called()


def test_complete_gx_statements_are_measured_and_limit_checked(tmp_path):
    import great_expectations as gx
    import great_expectations.expectations as gxe
    import pandas as pd
    import pytest
    import sqlalchemy as sa

    from ppsc_ops_data_quality.runtime import guard_query_size, prepare_validation, run_validations

    url = "sqlite:///" + str(tmp_path / "comparison.db")
    seed = sa.create_engine(url)
    pd.DataFrame({"id": ["a"], "expected": [1], "observed": [1]}).to_sql(
        "comparison", seed, index=False
    )
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    source = context.data_sources.add_sqlite(name="sql", connection_string=url)
    suite = context.suites.add(
        gx.ExpectationSuite(
            name="pairs",
            expectations=[
                gxe.ExpectColumnPairValuesToBeEqual(column_A="expected", column_B="observed")
            ],
        )
    )
    native = exp.select(exp.column("id"), exp.column("expected"), exp.column("observed")).from_(
        "comparison"
    )
    definition, _ = prepare_validation(
        context, source, native, suite, name="query", sql_path=tmp_path / "query.sql"
    )
    engine = source.get_execution_engine().engine
    listener, sizes = guard_query_size(engine)
    try:
        results = run_validations([definition], suite_directory=tmp_path / "suites")
        assert results["query"].success and sizes
        assert max(sizes) > len(definition.data.data_asset.query.encode())
        assert (tmp_path / "query.lineage.json").is_file()
    finally:
        sa.event.remove(engine, "before_cursor_execute", listener)
    listener, _ = guard_query_size(engine, max_bytes=10)
    try:
        with pytest.raises(ValueError, match="GX statement exceeds"):
            with engine.connect() as connection:
                connection.execute(sa.text("SELECT 123456789"))
    finally:
        sa.event.remove(engine, "before_cursor_execute", listener)
    engine.dispose()
    seed.dispose()


def test_native_sql_gx_dotted_labels_preserve_pair_and_null_semantics(tmp_path):
    import great_expectations as gx
    import great_expectations.expectations as gxe
    import sqlalchemy as sa

    from ppsc_ops_data_quality.account_to_survey_results.suites import equal_values
    from ppsc_ops_data_quality.runtime import prepare_validation, run_validations

    url = "sqlite:///" + str(tmp_path / "dotted.db")
    seed = sa.create_engine(url)
    with seed.begin() as connection:
        for table in ("expected", "observed"):
            connection.execute(sa.text(f'CREATE TABLE {table} (Id INTEGER, "F__c" INTEGER)'))
            connection.execute(sa.text(f"INSERT INTO {table} VALUES (1, 7), (2, NULL)"))
    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False}
    source = context.data_sources.add_sqlite(name="dotted", connection_string=url)
    pair = equal_values(field="F__c", row_condition=None, meta={"check_id": "F_equals_expected"})
    suite = context.suites.add(
        gx.ExpectationSuite(
            name="pairs",
            expectations=[
                gxe.ExpectColumnValuesToBeUnique(column="expected.Id"),
                pair,
            ],
        )
    )
    # Table qualifiers belong inside the join; dotted labels are single identifiers outside it.
    query = __import__("sqlglot").parse_one("""SELECT expected.Id AS "expected.Id",
        expected.F__c AS "expected.F__c", observed.F__c AS "observed.F__c"
        FROM expected LEFT JOIN observed ON expected.Id = observed.Id""")
    definition, _ = prepare_validation(
        context, source, query, suite, name="dotted", sql_path=tmp_path / "query.sql"
    )
    equal = run_validations([definition], suite_directory=tmp_path / "equal")["dotted"]
    assert equal.success
    assert equal.results[1].result["missing_count"] == 1
    with seed.begin() as connection:
        connection.execute(sa.text("UPDATE observed SET F__c=8 WHERE Id=1"))
        connection.execute(sa.text("UPDATE observed SET F__c=9 WHERE Id=2"))
    unequal = run_validations([definition], suite_directory=tmp_path / "unequal")["dotted"]
    assert not unequal.success
    assert unequal.results[1].result["unexpected_count"] == 2
    with seed.begin() as connection:
        connection.execute(sa.text("INSERT INTO observed VALUES (1, 8)"))
    duplicate = run_validations([definition], suite_directory=tmp_path / "duplicate")["dotted"]
    assert not duplicate.results[0].success
    assert duplicate.results[1].result["unexpected_count"] == 3
    source.get_execution_engine().engine.dispose()
    seed.dispose()
