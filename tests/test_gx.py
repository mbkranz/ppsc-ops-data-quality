"""Native GX behavior on SQLite; Athena acceptance is a separate live gate."""

import json
import sqlite3

import great_expectations as gx
import pytest

from ppsc_ops_data_quality.gx import (
    account,
    account_contact_relation,
    account_contact_relation_to_account,
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
        account_contact_relation.build_suite,
        account_contact_relation_to_account.build_suite,
    ],
)
def test_native_suite_json_round_trip_preserves_rule_evidence(builder):
    original = builder().to_json_dict()
    restored = gx.ExpectationSuite(**json.loads(json.dumps(original)))
    assert restored.to_json_dict() == original
    for expectation in restored.expectations:
        assert expectation.description
        assert expectation.meta["rule_id"]
        assert expectation.meta["rationale"]
        assert expectation.meta["sources"]
        assert expectation.meta["assumptions"]
        assert expectation.meta["investigation"]


@pytest.mark.parametrize("subject", [account, account_contact_relation])
def test_identity_suite_accepts_distinct_ids_and_extra_columns(tmp_path, subject):
    columns = {**STATE_COLUMNS, "account_id": "TEXT", "extra": "TEXT"}
    rows = [
        ("row-a", "2020-01-01", None, 1, "2026-01-01", "parent-a", "retained"),
        ("row-b", "2025-01-01", None, 1, "2026-01-01", "parent-b", "retained"),
    ]
    result = validate_rows(tmp_path, subject.build_suite(), columns, rows)
    assert result.success


@pytest.mark.parametrize("subject", [account, account_contact_relation])
def test_identity_suite_keeps_null_blank_and_duplicate_findings_separate(tmp_path, subject):
    columns = {**STATE_COLUMNS, "account_id": "TEXT"}
    rows = [
        (identifier, "2020-01-01", None, 1, "2026-01-01", "parent")
        for identifier in [None, "", "   ", "duplicate", "duplicate", "valid"]
    ]
    suite = subject.build_suite()
    result = validate_rows(tmp_path, suite, columns, rows)
    assert not result.success
    rules = by_rule(result)
    assert rules[f"{suite.name}.columns"].success
    assert rules[f"{suite.name}.id.required"].result["unexpected_count"] == 1
    assert rules[f"{suite.name}.id.nonblank"].result["observed_value"] == 2
    assert rules[f"{suite.name}.id.unique"].result["unexpected_count"] == 2


@pytest.mark.parametrize("subject", [account, account_contact_relation])
def test_identity_suite_requires_projected_temporal_columns(tmp_path, subject):
    result = validate_rows(
        tmp_path, subject.build_suite(), {"id": "TEXT", "account_id": "TEXT"}, [("a", "p")]
    )
    assert not result.success
    assert not by_rule(result)[f"{subject.build_suite().name}.columns"].success


def test_relationship_violations_preserve_child_grain_and_distinguish_causes(tmp_path):
    result = validate_rows(
        tmp_path,
        account_contact_relation_to_account.build_suite(),
        {"id": "TEXT", "account_id": "TEXT", "matching_account_versions": "INTEGER"},
        [
            ("valid", "a", 1),
            ("null-key", None, 0),
            ("blank-key", "  ", 0),
            ("absent-parent", "b", 0),
            ("ambiguous-parent", "c", 3),
        ],
    )
    assert not result.success
    rules = by_rule(result)
    prefix = "account_contact_relation_to_account"
    expected = {
        "reference.required": {"null-key", "blank-key"},
        "parent.exists": {"absent-parent"},
        "parent.unambiguous": {"ambiguous-parent"},
    }
    for rule, identifiers in expected.items():
        finding = rules[f"{prefix}.{rule}"].result
        assert finding["observed_value"] == len(identifiers)
        assert {row["id"] for row in finding["details"]["unexpected_rows"]} == identifiers


def test_unexpected_rows_count_is_not_truncated_to_the_diagnostic_sample(tmp_path):
    result = validate_rows(
        tmp_path,
        account_contact_relation_to_account.build_suite(),
        {"id": "TEXT", "account_id": "TEXT", "matching_account_versions": "INTEGER"},
        [(f"child-{number}", "missing", 0) for number in range(205)],
    )
    finding = by_rule(result)["account_contact_relation_to_account.parent.exists"].result
    assert finding["observed_value"] == 205
    assert len(finding["details"]["unexpected_rows"]) == 200
    assert not result.success


def test_native_identity_counts_remain_complete_with_bounded_samples(tmp_path):
    identifiers = [f"duplicate-{number}" for number in range(205) for _ in range(2)]
    identifiers += [None] * 205
    rows = [(identifier, "2020-01-01", None, 1, "2026-01-01") for identifier in identifiers]
    result = validate_rows(tmp_path, account.build_suite(), STATE_COLUMNS, rows)
    rules = by_rule(result)
    assert rules["account.id.unique"].result["unexpected_count"] == 410
    assert rules["account.id.required"].result["unexpected_count"] == 205
    for rule_id in ("account.id.unique", "account.id.required"):
        finding = rules[rule_id].result
        assert len(finding["partial_unexpected_list"]) == 200
        assert len(finding["unexpected_list"]) == 200
        assert len(finding["partial_unexpected_counts"]) <= 200
        assert not finding.get("unexpected_index_query")
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
