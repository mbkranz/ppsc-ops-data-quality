"""Explicit account_to_survey_results suites operations."""

from __future__ import annotations

from copy import deepcopy

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.expectations.row_conditions import Column

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    ACCOUNT_FIELDS_ASSIGNED_BY_FLOW,
    ROLLUP_ACCOUNT_FIELDS,
    ComparisonSpec,
)


def equal_values(*, field: str, row_condition, meta: dict, description: str | None = None):
    """The shared native equality/null policy; callers supply applicability."""
    return gxe.ExpectColumnPairValuesToBeEqual(
        column_A=f"observed.{field}",
        column_B=f"expected.{field}",
        ignore_row_if="both_values_are_missing",
        mostly=1,
        row_condition=row_condition,
        meta=meta,
        description=description,
    )


def comparison_suite(spec: ComparisonSpec, *, name: str) -> gx.ExpectationSuite:
    """Build checks only; no context, query execution, policy or source acquisition."""
    scope = Column("comparison_scope") == True
    valid = scope & (Column("comparison_keys_are_valid") == True)
    columns = ["comparison_scope", "comparison_keys_are_valid", "comparison_evidence_is_complete"]
    keys = [f"{side}.key.{key.name}" for key in spec.keys for side in ("expected", "observed")]
    columns.extend(keys)
    checks = [
        gxe.ExpectColumnValuesToNotBeNull(
            column="comparison_scope",
            meta={"check_id": "scope_known", "failure_status": "incomplete"},
        ),
        gxe.ExpectColumnValuesToBeInSet(
            column="comparison_keys_are_valid",
            value_set=[True],
            row_condition=scope,
            meta={"check_id": "comparison_grain_valid"},
        ),
        gxe.ExpectColumnValuesToBeInSet(
            column="comparison_evidence_is_complete",
            value_set=[True],
            row_condition=scope,
            meta={"check_id": "computation_complete", "failure_status": "incomplete"},
        ),
    ]
    for value in spec.values:
        expected, observed = f"expected.{value.name}", f"observed.{value.name}"
        columns.extend([expected, observed])
        applicable = valid
        for role in ("deterministic", "assigned", "required", "must_be_null"):
            if getattr(value, role) is not None:
                column = f"expected.{value.name}__{role}"
                columns.append(column)
                if role == "deterministic":
                    applicable = applicable & (Column(column) == True)
                elif role == "assigned":
                    applicable = applicable & Column(column).is_not_null()
                else:
                    expectation = (
                        gxe.ExpectColumnValuesToNotBeNull
                        if role == "required"
                        else gxe.ExpectColumnValuesToBeNull
                    )
                    checks.append(
                        expectation(
                            column=observed,
                            row_condition=valid & (Column(column) == True),
                            meta={"check_id": f"{value.name}_{role}"},
                        )
                    )
        checks.append(
            equal_values(
                field=value.name,
                row_condition=applicable,
                meta={
                    "check_id": f"{value.name}_equals_expected",
                    "both_null_policy": "accepted; native missing_count reports excluded pairs",
                    "denominator": "scoped rows with valid keys and known computation, excluding both-null pairs",
                },
            )
        )
    checks.insert(
        0,
        gxe.ExpectTableColumnsToMatchSet(
            column_set=columns, exact_match=False, meta={"check_id": "comparison_columns"}
        ),
    )
    return gx.ExpectationSuite(
        name=name,
        expectations=checks,
        meta={"comparison_spec": spec.model_dump(mode="json"), "finding_key_columns": keys},
    )


# Stable check identities survive output-label changes in the GX projection.
IDENTITY_CHECK_NAMES = {"expected.Id": "expected_account_id", "observed.Id": "observed_account_id"}

FLOW_IDENTITY_COLUMNS = (
    "survey_result_id",
    "participant_contact_id",
    "expected.Id",
    "observed.Id",
)


ROLLUP_IDENTITY_COLUMNS = (
    "expected.Id",
    "person_contact_id",
    "observed.Id",
)


POST_LAUNCH_COMPLETION = Column("survey_completion_occurred_on_or_after_launch") == True


def flow_account_suite(
    *,
    provenance: dict | None = None,
    lineage: dict | None = None,
    expected_row_count: int | None = None,
    required_fields: tuple[str, ...] = (),
    must_be_null_fields: tuple[str, ...] = (),
) -> gx.ExpectationSuite:
    """Return built-in expectations for the survey-event comparison dataset.

    The base suite has 29 expectations, including scope/computation completeness: required columns; four non-null identity
    columns; unique survey event Id; two lookup-resolution checks; and 19 value
    comparisons. Optional expected_row_count adds an independent source-count
    check for post-launch completions. Empty eligible cohorts are allowed when
    no count contract is supplied. The required-columns check is batch-wide.
    """
    PROJECTION_LINEAGE = lineage or {}
    expectations = []
    expectations.append(
        gxe.ExpectTableColumnsToMatchSet(
            column_set=[
                *FLOW_IDENTITY_COLUMNS,
                "validation_record_id",
                "comparison_keys_are_valid",
                "flow_evidence_is_complete",
                "cabor_lookup_is_deterministic",
                "survey_completion_timestamp",
                "survey_completion_occurred_on_or_after_launch",
                *[f"expected.{field}" for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW],
                *[f"observed.{field}" for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW],
                *[f"expected.{field}__deterministic" for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW],
                *[f"expected.{field}__assigned" for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW],
                *[f"expected.{field}_required" for field in required_fields],
                *[f"expected.{field}_must_be_null" for field in must_be_null_fields],
            ],
            exact_match=False,
            description="The joined comparison contains all identity, evidence and value columns.",
            meta={"check_id": "flow_comparison_required_columns"},
        )
    )
    expectations.extend(
        [
            gxe.ExpectColumnValuesToNotBeNull(
                column="survey_completion_occurred_on_or_after_launch",
                description="Unknown business scope is incomplete evidence, not a passed comparison.",
                meta={"check_id": "flow_scope_is_known", "failure_status": "incomplete"},
            ),
            gxe.ExpectColumnValuesToBeInSet(
                column="flow_evidence_is_complete",
                value_set=[True],
                row_condition=POST_LAUNCH_COMPLETION,
                description="All expected fields have known routing, assignment and authored presence evidence.",
                meta={"check_id": "flow_computation_is_complete", "failure_status": "incomplete"},
            ),
        ]
    )
    for column in FLOW_IDENTITY_COLUMNS:
        expectations.append(
            gxe.ExpectColumnValuesToNotBeNull(
                column=column,
                row_condition=POST_LAUNCH_COMPLETION,
                mostly=1,
                description=f"Every survey event has {column}.",
                meta={"check_id": f"flow_{IDENTITY_CHECK_NAMES.get(column, column)}_is_present"},
            )
        )
    expectations.append(
        gxe.ExpectColumnValuesToBeUnique(
            column="survey_result_id",
            row_condition=POST_LAUNCH_COMPLETION,
            mostly=1,
            description="Survey event IDs are unique in the comparison; joins do not fan out.",
            meta={"check_id": "one_comparison_row_per_survey_event"},
        )
    )
    expectations.append(
        gxe.ExpectColumnValuesToNotBeNull(
            column="cabor_lookup_is_deterministic",
            row_condition=POST_LAUNCH_COMPLETION,
            mostly=1,
            meta={"check_id": "permission_lookup_resolution_evidence_is_present"},
        )
    )
    expectations.append(
        gxe.ExpectColumnValuesToBeInSet(
            column="cabor_lookup_is_deterministic",
            value_set=[True],
            row_condition=POST_LAUNCH_COMPLETION,
            mostly=1,
            description="The permission lookup resolves a reproducible expected CABOR value.",
            meta={
                "check_id": "permission_lookup_is_deterministic",
                "ppsc": deepcopy(PROJECTION_LINEAGE.get("cabor_lookup_is_deterministic", {})),
            },
        )
    )
    for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW:
        row_condition = (
            POST_LAUNCH_COMPLETION
            & (Column("comparison_keys_are_valid") == True)
            & (Column(f"expected.{field}__deterministic") == True)
            & Column(f"expected.{field}__assigned").is_not_null()
        )
        if field == "CABOR_Completion_Date__c":
            row_condition = row_condition & (Column("cabor_lookup_is_deterministic") == True)
        expectations.append(
            equal_values(
                field=field,
                description=f"Observed Account.{field} equals its expected AFTER value.",
                meta={
                    "check_id": f"observed_{field}_equals_expected",
                    "ppsc": deepcopy(PROJECTION_LINEAGE.get("expected." + field, {})),
                    "both_null_policy": "accepted; native missing_count reports these excluded pairs",
                    "denominator": "scoped deterministic rows with valid keys, excluding both-null pairs",
                },
                row_condition=row_condition,
            )
        )
    for fields, suffix, expectation_type in (
        (required_fields, "required", gxe.ExpectColumnValuesToNotBeNull),
        (must_be_null_fields, "must_be_null", gxe.ExpectColumnValuesToBeNull),
    ):
        if len(set(fields)) != len(fields) or not set(fields) <= set(
            ACCOUNT_FIELDS_ASSIGNED_BY_FLOW
        ):
            raise ValueError("Presence checks must bind unique selected expected fields")
        for field in fields:
            expectations.append(
                expectation_type(
                    column=f"observed.{field}",
                    row_condition=(
                        POST_LAUNCH_COMPLETION
                        & (Column("comparison_keys_are_valid") == True)
                        & (Column(f"expected.{field}_{suffix}") == True)
                    ),
                    meta={"check_id": f"observed_{field}_{suffix}", "presence_role": suffix},
                )
            )
    if expected_row_count is not None:
        expectations.append(
            gxe.ExpectTableRowCountToEqual(
                value=expected_row_count,
                row_condition=POST_LAUNCH_COMPLETION,
                description="Post-launch comparison row count equals the independent source count.",
                meta={"check_id": "flow_comparison_row_count_matches_source"},
            )
        )
    return gx.ExpectationSuite(
        name="account_to_survey_results_flow",
        meta={
            "metadata_inputs": provenance or {},
            "expected_value_provenance": lineage or {},
            "grain": "survey_event",
            "expected_state": "Account BEFORE plus one Flow event",
            "observed_state": "independent Account AFTER the same event",
            "row_scope": deepcopy(
                PROJECTION_LINEAGE.get("survey_completion_occurred_on_or_after_launch", {})
            ),
        },
        expectations=expectations,
    )


def rollup_account_suite(
    *, expected_row_count: int | None = None, lineage: dict | None = None
) -> gx.ExpectationSuite:
    """Return 25 built-in expectations for current-snapshot Account rollups.

    Required columns, three non-null identities, unique person Account Id, and
    19 observed/expected count comparisons. Optional source row count adds one
    expectation. Unlike the event suite, Account Id must be unique at this grain.
    """
    PROJECTION_LINEAGE = lineage or {}
    expectations = []
    expectations.append(
        gxe.ExpectTableColumnsToMatchSet(
            column_set=[
                *ROLLUP_IDENTITY_COLUMNS,
                "validation_record_id",
                "source_parent_keys_are_valid",
                "comparison_keys_are_valid",
                *[f"expected.{field}" for field in ROLLUP_ACCOUNT_FIELDS],
                *[f"observed.{field}" for field in ROLLUP_ACCOUNT_FIELDS],
            ],
            exact_match=False,
            meta={"check_id": "rollup_comparison_required_columns"},
        )
    )
    for column in ROLLUP_IDENTITY_COLUMNS:
        expectations.append(
            gxe.ExpectColumnValuesToNotBeNull(
                column=column,
                mostly=1,
                meta={"check_id": f"rollup_{IDENTITY_CHECK_NAMES.get(column, column)}_is_present"},
            )
        )
    expectations.append(
        gxe.ExpectColumnValuesToBeUnique(
            column="expected.Id",
            mostly=1,
            description="Person Account IDs are unique in the rollup comparison.",
            meta={"check_id": "one_rollup_comparison_row_per_person_account"},
        )
    )
    expectations.append(
        gxe.ExpectColumnValuesToBeInSet(
            column="source_parent_keys_are_valid",
            value_set=[True],
            description="Source parent IDs are unique before any child aggregation.",
            meta={"check_id": "rollup_source_parent_keys_are_valid"},
        )
    )
    for field in ROLLUP_ACCOUNT_FIELDS:
        expectations.append(
            equal_values(
                field=field,
                row_condition=Column("comparison_keys_are_valid") == True,
                description=f"Observed Account.{field} equals its expected survey rollup count.",
                meta={
                    "check_id": f"observed_{field}_equals_expected_rollup",
                    "ppsc": deepcopy(PROJECTION_LINEAGE.get("expected." + field, {})),
                },
            )
        )
    if expected_row_count is not None:
        expectations.append(
            gxe.ExpectTableRowCountToEqual(
                value=expected_row_count,
                description="Comparison row count equals the independent person Account count.",
                meta={"check_id": "rollup_comparison_row_count_matches_source"},
            )
        )
    return gx.ExpectationSuite(
        name="account_to_survey_results_rollups",
        meta={
            "grain": "person_account",
            "state": "same current snapshot for all inputs",
        },
        expectations=expectations,
    )
