"""Built-in GX expectations over independently expected and observed Account values.

    from ppsc_ops_data_quality.account_to_survey_results.queries import flow_account_comparison
    Expected = expected_account_values(Record)
    Comparison = flow_account_comparison(Expected, AccountAfter)
    # Supply Comparison as a GX Batch, then:
    result = batch.validate(flow_account_suite(), result_format="SUMMARY")

Tested with GX Core 1.24.0. Every expectation is a built-in gxe class; this module
defines no Expectation subclass, metric provider or unexpected-rows query. The
Ibis derivation module remains independent of GX. This module returns suites;
it creates no context, data asset or checkpoint.

Flow contract: expected values use Account BEFORE plus one qualifying survey
event. AccountAfter is the independently observed Account AFTER that same event,
after automation settles. Historical survey events cannot all be compared to a
single latest Account snapshot. Use consistent timestamps, types and time zones.

Rollup contract: expected counts and observed Account rollups represent the same
current snapshot, including the same deletion/revocation state.

NULL policy: ignore only pairs where both values are missing. A one-sided NULL is
a mismatch; no sentinel values or additional nullity flags are used. An ambiguous
unsorted permission lookup fails the resolution expectation, while the CABOR
value comparison alone is limited to rows with a deterministic expected value.
All row-scoped Flow checks, including the optional count, apply only to completion
dates on/after 2024-12-16. The query projects this business scope without filtering
the batch. Pre-launch and unknown-date rows remain available for profiling but
are not validated by these Flow checks. Structural checks remain batch-wide.

Documentation and reviewed skill references are listed in the accompanying README.
"""

from copy import deepcopy

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.expectations.row_conditions import Column

from ppsc_ops_data_quality.account_to_survey_results.lineage import PROJECTION_LINEAGE
from ppsc_ops_data_quality.account_to_survey_results.queries import (
    ACCOUNT_FIELDS_ASSIGNED_BY_FLOW,
    ROLLUP_ACCOUNT_FIELDS,
)

FLOW_IDENTITY_COLUMNS = (
    "survey_result_id",
    "participant_contact_id",
    "expected_account_id",
    "observed_account_id",
)
ROLLUP_IDENTITY_COLUMNS = (
    "expected_account_id",
    "person_contact_id",
    "observed_account_id",
)

# The Ibis query owns the date comparison; GX consumes its named result so the
# cutoff and timestamp semantics are not independently reimplemented here.
POST_LAUNCH_COMPLETION = Column("survey_completion_occurred_on_or_after_launch") == True


def flow_account_suite(*, expected_row_count: int | None = None) -> gx.ExpectationSuite:
    """Return built-in expectations for the survey-event comparison dataset.

    The base suite has 27 expectations: required columns; four non-null identity
    columns; unique survey event Id; two lookup-resolution checks; and 19 value
    comparisons. Optional expected_row_count adds an independent source-count
    check for post-launch completions. Empty eligible cohorts are allowed when
    no count contract is supplied. The required-columns check is batch-wide.
    """
    expectations = []
    expectations.append(
        gxe.ExpectTableColumnsToMatchSet(
            column_set=[
                *FLOW_IDENTITY_COLUMNS,
                "cabor_lookup_is_deterministic",
                "survey_completion_timestamp",
                "survey_completion_occurred_on_or_after_launch",
                *[f"expected__{field}" for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW],
                *[f"observed__{field}" for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW],
            ],
            exact_match=False,
            description="The joined comparison contains all identity, evidence and value columns.",
            meta={"check_id": "flow_comparison_required_columns"},
        )
    )
    for column in FLOW_IDENTITY_COLUMNS:
        expectations.append(
            gxe.ExpectColumnValuesToNotBeNull(
                column=column,
                row_condition=POST_LAUNCH_COMPLETION,
                mostly=1,
                description=f"Every survey event has {column}.",
                meta={"check_id": f"flow_{column}_is_present"},
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
                "ppsc": deepcopy(PROJECTION_LINEAGE["CABOR_Completion_Date__c_is_deterministic"]),
            },
        )
    )
    for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW:
        row_condition = POST_LAUNCH_COMPLETION
        if field == "CABOR_Completion_Date__c":
            row_condition = row_condition & (Column("cabor_lookup_is_deterministic") == True)
        expectations.append(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=f"observed__{field}",
                column_B=f"expected__{field}",
                ignore_row_if="both_values_are_missing",
                mostly=1,
                description=f"Observed Account.{field} equals its expected AFTER value.",
                meta={
                    "check_id": f"observed_{field}_equals_expected",
                    "ppsc": deepcopy(PROJECTION_LINEAGE[field]),
                },
                row_condition=row_condition,
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
            "grain": "survey_event",
            "expected_state": "Account BEFORE plus one Flow event",
            "observed_state": "independent Account AFTER the same event",
            "row_scope": deepcopy(
                PROJECTION_LINEAGE["survey_completion_occurred_on_or_after_launch"]
            ),
        },
        expectations=expectations,
    )


def rollup_account_suite(*, expected_row_count: int | None = None) -> gx.ExpectationSuite:
    """Return 24 built-in expectations for current-snapshot Account rollups.

    Required columns, three non-null identities, unique person Account Id, and
    19 observed/expected count comparisons. Optional source row count adds one
    expectation. Unlike the event suite, Account Id must be unique at this grain.
    """
    expectations = []
    expectations.append(
        gxe.ExpectTableColumnsToMatchSet(
            column_set=[
                *ROLLUP_IDENTITY_COLUMNS,
                *[f"expected__{field}" for field in ROLLUP_ACCOUNT_FIELDS],
                *[f"observed__{field}" for field in ROLLUP_ACCOUNT_FIELDS],
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
                meta={"check_id": f"rollup_{column}_is_present"},
            )
        )
    expectations.append(
        gxe.ExpectColumnValuesToBeUnique(
            column="expected_account_id",
            mostly=1,
            description="Person Account IDs are unique in the rollup comparison.",
            meta={"check_id": "one_rollup_comparison_row_per_person_account"},
        )
    )
    for field in ROLLUP_ACCOUNT_FIELDS:
        expectations.append(
            gxe.ExpectColumnPairValuesToBeEqual(
                column_A=f"observed__{field}",
                column_B=f"expected__{field}",
                ignore_row_if="both_values_are_missing",
                mostly=1,
                description=f"Observed Account.{field} equals its expected survey rollup count.",
                meta={
                    "check_id": f"observed_{field}_equals_expected_rollup",
                    "ppsc": deepcopy(PROJECTION_LINEAGE[field]),
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
