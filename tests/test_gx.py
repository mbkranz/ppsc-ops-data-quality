"""Native GX behavior on SQLite; Athena acceptance is a separate live gate."""

import json
import sqlite3

import great_expectations as gx
import pytest

from ppsc_ops_data_quality.gx import (
    account,
    survey_result,
    survey_result_to_account,
)

STATE_COLUMNS = {
    "id": "TEXT",
    "valid_from": "TEXT",
    "valid_to": "TEXT",
    "is_current": "INTEGER",
    "loaded_at": "TEXT",
}


def validate_rows(tmp_path, suite, columns, rows):
    """Exercise native GX with a real SQL query asset over controlled local rows."""
    database = tmp_path / "fixture.sqlite"
    with sqlite3.connect(database) as connection:
        fields = ", ".join(f'"{name}" {dtype}' for name, dtype in columns.items())
        connection.execute(f"CREATE TABLE fixture ({fields})")
        placeholders = ", ".join("?" for _ in columns)
        connection.executemany(f"INSERT INTO fixture VALUES ({placeholders})", rows)

    context = gx.get_context(mode="ephemeral")
    datasource = context.data_sources.add_sql(
        name="local_fixture",
        connection_string=f"sqlite:///{database}",
        create_temp_table=False,
    )
    asset = datasource.add_query_asset(name="selected_rows", query="SELECT * FROM fixture")
    batch = asset.add_batch_definition_whole_table("all_selected_rows")
    suite = context.suites.add(suite)
    validation = context.validation_definitions.add(
        gx.ValidationDefinition(name="fixture_validation", data=batch, suite=suite)
    )
    return validation.run(
        result_format={
            "result_format": "COMPLETE",
            "partial_unexpected_count": 200,
            "return_unexpected_index_query": False,
        }
    )


def by_rule(result):
    return {item.expectation_config.meta["rule_id"]: item for item in result.results}


@pytest.mark.parametrize(
    "builder",
    [
        account.build_suite,
        survey_result.build_suite,
        survey_result_to_account.build_suite,
    ],
)
def test_native_suite_json_round_trip_preserves_rule_evidence(builder):
    original = builder().to_json_dict()
    restored = gx.ExpectationSuite(**json.loads(json.dumps(original)))
    assert restored.to_json_dict() == original
    assert restored.meta["sources"]
    assert restored.meta["assumptions"]
    for expectation in restored.expectations:
        assert expectation.description
        assert expectation.meta["rule_id"]
        if expectation.expectation_type == "unexpected_rows_expectation":
            assert expectation.meta["sql_file"].endswith(
                f"/{expectation.meta['expectation_name']}.sql"
            )
            assert expectation.meta["expectation_name"].startswith("expect_")
            assert (
                expectation.meta["rule_id"]
                == f"{restored.name}.{expectation.meta['expectation_name']}"
            )


@pytest.mark.parametrize("subject", [account, survey_result])
def test_identity_suite_accepts_distinct_ids_and_extra_columns(tmp_path, subject):
    columns = {**STATE_COLUMNS, "participant_id": "TEXT", "extra": "TEXT"}
    rows = [
        ("row-a", "2020-01-01", None, 1, "2026-01-01", "parent-a", "retained"),
        ("row-b", "2025-01-01", None, 1, "2026-01-01", "parent-b", "retained"),
    ]
    result = validate_rows(tmp_path, subject.build_suite(), columns, rows)
    assert result.success


@pytest.mark.parametrize("subject", [account, survey_result])
def test_identity_suite_keeps_null_blank_and_duplicate_findings_separate(tmp_path, subject):
    columns = {**STATE_COLUMNS, "participant_id": "TEXT"}
    rows = [
        (identifier, "2020-01-01", None, 1, "2026-01-01", "parent")
        for identifier in [None, "", "   ", "duplicate", "duplicate", "valid"]
    ]
    suite = subject.build_suite()
    result = validate_rows(tmp_path, suite, columns, rows)
    assert not result.success
    rules = by_rule(result)
    assert rules[f"{suite.name}.columns"].success
    assert rules[f"{suite.name}.expect_column_values_to_not_be_null"].result["observed_value"] == 1
    assert rules[f"{suite.name}.expect_column_values_to_not_be_blank"].result["observed_value"] == 2
    assert rules[f"{suite.name}.expect_column_values_to_be_unique"].result["observed_value"] == 2


@pytest.mark.parametrize("subject", [account, survey_result])
def test_identity_suite_requires_projected_temporal_columns(tmp_path, subject):
    result = validate_rows(
        tmp_path, subject.build_suite(), {"id": "TEXT", "participant_id": "TEXT"}, [("a", "p")]
    )
    assert not result.success
    assert not by_rule(result)[f"{subject.build_suite().name}.columns"].success


def test_relationship_violations_distinguish_both_hops_at_survey_grain(tmp_path):
    result = validate_rows(
        tmp_path,
        survey_result_to_account.build_suite(),
        {
            "id": "TEXT",
            "participant_id": "TEXT",
            "matching_contact_versions": "INTEGER",
            "missing_account_references": "INTEGER",
            "matching_account_versions": "INTEGER",
        },
        [
            ("valid", "c", 1, 0, 1),
            ("null-key", None, 0, 0, 0),
            ("blank-key", "  ", 0, 0, 0),
            ("missing-participant", "absent", 0, 0, 0),
            ("duplicate-participant", "dup", 2, 0, 2),
            ("null-account", "c-null", 1, 1, 0),
            ("blank-account", "c-blank", 1, 1, 0),
            ("absent-account", "c-absent", 1, 0, 0),
            ("duplicate-account", "c-dup", 1, 0, 3),
        ],
    )
    expected = {
        "expect_survey_result_participant_reference_to_be_present": {"null-key", "blank-key"},
        "expect_survey_result_participant_to_exist": {"missing-participant"},
        "expect_survey_result_participant_to_be_unique": {"duplicate-participant"},
        "expect_survey_result_account_reference_to_be_present": {"null-account", "blank-account"},
        "expect_survey_result_account_to_exist": {"absent-account"},
        "expect_survey_result_account_to_be_unique": {"duplicate-account"},
    }
    for name, identifiers in expected.items():
        finding = by_rule(result)[f"survey_result_to_account.{name}"].result
        assert finding["observed_value"] == len(identifiers)
        assert {row["id"] for row in finding["details"]["unexpected_rows"]} == identifiers


def test_unexpected_rows_count_is_not_truncated_to_the_diagnostic_sample(tmp_path):
    result = validate_rows(
        tmp_path,
        survey_result_to_account.build_suite(),
        {
            "id": "TEXT",
            "participant_id": "TEXT",
            "matching_contact_versions": "INTEGER",
            "missing_account_references": "INTEGER",
            "matching_account_versions": "INTEGER",
        },
        [(f"survey-{number}", "contact", 1, 0, 0) for number in range(205)],
    )
    finding = by_rule(result)[
        "survey_result_to_account.expect_survey_result_account_to_exist"
    ].result
    assert finding["observed_value"] == 205
    assert len(finding["details"]["unexpected_rows"]) == 200
    assert not result.success


def test_native_identity_counts_remain_complete_with_bounded_samples(tmp_path):
    identifiers = [f"duplicate-{number}" for number in range(205) for _ in range(2)]
    identifiers += [None] * 205
    rows = [(identifier, "2020-01-01", None, 1, "2026-01-01") for identifier in identifiers]
    result = validate_rows(tmp_path, account.build_suite(), STATE_COLUMNS, rows)
    rules = by_rule(result)
    assert rules["account.expect_column_values_to_be_unique"].result["observed_value"] == 410
    assert rules["account.expect_column_values_to_not_be_null"].result["observed_value"] == 205
    for rule_id in (
        "account.expect_column_values_to_be_unique",
        "account.expect_column_values_to_not_be_null",
    ):
        finding = rules[rule_id].result
        assert len(finding["details"]["unexpected_rows"]) == 200
    assert not result.success


def test_query_error_is_retained_as_an_execution_exception(tmp_path):
    suite = gx.ExpectationSuite(
        name="broken_query",
        expectations=[
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query="SELECT missing_column FROM {batch}",
                catch_exceptions=True,
            )
        ],
    )
    result = validate_rows(tmp_path, suite, {"id": "TEXT"}, [("a",)])
    assert not result.success
    errors = result.results[0].exception_info
    assert errors
    assert "missing_column" in json.dumps(errors)
    assert all(info["raised_exception"] for info in errors.values())


@pytest.fixture
def sql_check_directory(tmp_path, monkeypatch):
    from ppsc_ops_data_quality import gx as suites

    subject = tmp_path / "custom"
    subject.mkdir()
    monkeypatch.setattr(suites, "files", lambda _: tmp_path)
    return subject


def test_sql_files_discover_in_order_with_stable_ids_and_comments(sql_check_directory):
    from ppsc_ops_data_quality.gx import sql_expectations

    for name in ("expect_b", "expect_a"):
        (sql_check_directory / f"{name}.sql").write_text(
            f"-- Explain {name}.\nWITH selected AS (SELECT * FROM batch) "
            "SELECT * FROM selected WHERE id IS NULL;\n"
        )
    checks = sql_expectations("custom")
    assert [check.meta["rule_id"] for check in checks] == ["custom.expect_a", "custom.expect_b"]
    assert "Explain expect_a." in checks[0].description
    assert "batch" in checks[0].unexpected_rows_query


@pytest.mark.parametrize(
    "sql",
    [
        "-- no query",
        "SELECT * FROM batch; SELECT * FROM batch",
        "DELETE FROM batch",
        "SELECT * INTO output_table FROM batch",
        "SELECT * FROM production.account",
        "SELECT * FROM unselected_account",
        "SELECT 1",
        "SELECT * FROM batch LIMIT 1",
        "SELECT * FROM batch WHERE (",
    ],
)
def test_expect_invalid_sql_files_fail_authoring_with_filename(sql_check_directory, sql):
    from ppsc_ops_data_quality.gx import sql_expectations

    (sql_check_directory / "expect_invalid.sql").write_text(sql)
    with pytest.raises(ValueError, match="custom/expect_invalid.sql"):
        sql_expectations("custom")


def test_empty_check_directory_cannot_silently_pass(sql_check_directory):
    from ppsc_ops_data_quality.gx import sql_expectations

    with pytest.raises(ValueError, match="no SQL checks"):
        sql_expectations("custom")


def test_cross_table_sql_uses_selected_relations_and_native_gx(tmp_path, sql_check_directory):
    from ppsc_ops_data_quality.gx import sql_expectations

    (sql_check_directory / "expect_parent_to_exist.sql").write_text(
        "-- A populated child reference must resolve in the selected Account state.\n"
        "SELECT child.* FROM contact_state AS child "
        "WHERE child.account_id IS NOT NULL AND NOT EXISTS "
        "(SELECT 1 FROM account_state AS parent WHERE parent.id = child.account_id)"
    )
    checks = sql_expectations(
        "custom",
        {
            "account_state": "SELECT 'parent' AS id",
            "contact_state": "SELECT * FROM fixture",
        },
    )
    suite = gx.ExpectationSuite(name="custom", expectations=checks)
    result = validate_rows(
        tmp_path,
        suite,
        {"id": "TEXT", "account_id": "TEXT"},
        [("valid", "parent"), ("missing", "absent"), ("null", None)],
    )
    finding = by_rule(result)["custom.expect_parent_to_exist"].result
    assert finding["observed_value"] == 1
    assert finding["details"]["unexpected_rows"] == [{"id": "missing", "account_id": "absent"}]


@pytest.mark.parametrize("identifier", ["{batch}", '{"key":1}', "x{3}", "{}", "__gx_batch__"])
def test_sql_literals_survive_binding_and_native_gx_formatting(
    tmp_path, sql_check_directory, identifier
):
    from ppsc_ops_data_quality.gx import sql_expectations

    (sql_check_directory / "expect_literal.sql").write_text(
        f"SELECT batch.* FROM batch WHERE batch.id = '{identifier}'"
    )
    suite = gx.ExpectationSuite(name="literals", expectations=sql_expectations("custom"))
    result = validate_rows(tmp_path, suite, {"id": "TEXT"}, [(identifier,), ("other",)])
    finding = by_rule(result)["custom.expect_literal"].result
    assert finding["observed_value"] == 1
    assert finding["details"]["unexpected_rows"] == [{"id": identifier}]


def test_authored_cte_can_consume_a_selected_population(tmp_path, sql_check_directory):
    from ppsc_ops_data_quality.gx import sql_expectations

    (sql_check_directory / "expect_parent_to_exist.sql").write_text(
        "WITH selected AS (SELECT * FROM contact_state) "
        "SELECT child.* FROM selected AS child WHERE NOT EXISTS "
        "(SELECT 1 FROM account_state AS parent WHERE parent.id = child.account_id)"
    )
    suite = gx.ExpectationSuite(
        name="cte",
        expectations=sql_expectations(
            "custom",
            {
                "account_state": "SELECT 'parent' AS id",
                "contact_state": "SELECT * FROM fixture",
            },
        ),
    )
    result = validate_rows(
        tmp_path,
        suite,
        {"id": "TEXT", "account_id": "TEXT"},
        [("valid", "parent"), ("missing", "absent")],
    )
    finding = by_rule(result)["custom.expect_parent_to_exist"].result
    assert finding["observed_value"] == 1
    assert finding["details"]["unexpected_rows"] == [{"id": "missing", "account_id": "absent"}]


def test_qualified_batch_alias_works_in_a_join(tmp_path, sql_check_directory):
    from ppsc_ops_data_quality.gx import sql_expectations

    (sql_check_directory / "expect_join_to_resolve.sql").write_text(
        "SELECT child.* FROM batch AS child LEFT JOIN account_state AS parent "
        "ON child.account_id = parent.id WHERE parent.id IS NULL"
    )
    suite = gx.ExpectationSuite(
        name="joined",
        expectations=sql_expectations("custom", {"account_state": "SELECT 'parent' AS id"}),
    )
    result = validate_rows(
        tmp_path,
        suite,
        {"id": "TEXT", "account_id": "TEXT"},
        [("valid", "parent"), ("missing", "absent")],
    )
    finding = by_rule(result)["custom.expect_join_to_resolve"].result
    assert finding["observed_value"] == 1
    assert finding["details"]["unexpected_rows"] == [{"id": "missing", "account_id": "absent"}]


def test_local_cte_shadows_a_selected_population_without_being_rewritten(
    tmp_path, sql_check_directory
):
    from ppsc_ops_data_quality.gx import sql_expectations

    (sql_check_directory / "expect_local_to_resolve.sql").write_text(
        "WITH account_state AS (SELECT 'local' AS id) "
        "SELECT b.* FROM batch AS b WHERE EXISTS "
        "(SELECT 1 FROM account_state AS parent WHERE parent.id = b.id)"
    )
    suite = gx.ExpectationSuite(
        name="local",
        expectations=sql_expectations("custom", {"account_state": "SELECT 'remote' AS id"}),
    )
    result = validate_rows(tmp_path, suite, {"id": "TEXT"}, [("local",), ("remote",)])
    assert by_rule(result)["custom.expect_local_to_resolve"].result["details"][
        "unexpected_rows"
    ] == [{"id": "local"}]


@pytest.mark.parametrize("name", ["check.sql", "expect_.sql", "expect.bad.sql", "Expect_a.sql"])
def test_sql_filename_must_be_an_expectation_name(sql_check_directory, name):
    from ppsc_ops_data_quality.gx import sql_expectations

    (sql_check_directory / name).write_text("SELECT * FROM batch WHERE id IS NULL")
    with pytest.raises(ValueError, match="name SQL files after expectations"):
        sql_expectations("custom")
