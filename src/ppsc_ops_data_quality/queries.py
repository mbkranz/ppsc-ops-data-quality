"""Compose history snapshots, expected values and comparisons as plain Ibis tables.

No GX imports or database writes. Query parameters are explicit Python values
compiled as Ibis literals. Complete composition before to_sqlglot() adds lineage.
Snapshot and expected-value implementation stays in its existing source modules.
"""

from collections.abc import Mapping
from datetime import date, datetime

import ibis
import ibis.expr.types as ir

from ppsc_ops_data_quality.account_to_survey_results import (
    ACCOUNT_FIELDS_ASSIGNED_BY_FLOW,
    add_flow_context,
    expected_account_values,
    expected_survey_rollups,
    join_account,
)
from ppsc_ops_data_quality.account_to_survey_results_lineage import ROLLUP_FIELD_LINEAGE
from ppsc_ops_data_quality.snapshot import snapshot

ROLLUP_ACCOUNT_FIELDS = tuple(field.removeprefix("Account.") for field in ROLLUP_FIELD_LINEAGE)
SURVEY_COMPLETION_FLOW_LAUNCH_DATE = date(2024, 12, 16)


def bind_history_tables(
    backend,
    *,
    account_database: str,
    contact_database: str,
    survey_result_database: str,
) -> dict[str, ir.Table]:
    """Bind each object's Athena history table using its actual catalog schema.

    Map lowercase columns to Salesforce API names upstream when needed. For a
    combined-history table supply three explicitly object-scoped relations instead.
    """
    return {
        "Account": backend.table("history", database=account_database),
        "Contact": backend.table("history", database=contact_database),
        "Survey_Result__c": backend.table("history", database=survey_result_database),
    }


def flow_account_comparison(
    ExpectedAccount: ir.Table,
    AccountAfter: ir.Table,
    *,
    event_id_column: str = "survey_result_id",
) -> ir.Table:
    """LEFT JOIN expected per-event values to an independent Account AFTER state.

    Input ExpectedAccount is expected_account_values() output. AccountAfter has
    Id, the 19 Account fields, and event_id_column identifying the survey event
    whose observed AFTER state that row represents. Join on both event and Account
    identity: separate events for one Account must not share an arbitrary latest
    state. AccountAfter may be an upstream query binding a verified snapshot to a
    selected event; it is not necessarily a historical Salesforce object table.

    Retain missing observed Accounts and duplicate observed IDs: integrity checks
    must detect these conditions. Account IDs are deliberately not unique at this
    grain; several survey events may refer to one Account.

    Project the completion timestamp and the inclusive launch predicate without
    filtering rows. The predicate uses the timestamp's calendar date; normalize
    source timestamps to the agreed business timezone upstream. NULL timestamps
    retain an unknown predicate. This is a business scope, not a FlowDecision.
    Pre-launch events remain available for profiling and migration reconciliation.
    """
    survey_completion_occurred_on_or_after_launch = (
        ExpectedAccount.Completion_Status_Timestamp__c.date()
        >= ibis.literal(SURVEY_COMPLETION_FLOW_LAUNCH_DATE, type="date")
    ).name("survey_completion_occurred_on_or_after_launch")
    AccountAfter = AccountAfter.view()
    Joined = ExpectedAccount.left_join(
        AccountAfter,
        [
            ExpectedAccount["Account.Id"] == AccountAfter.Id,
            ExpectedAccount["Record.Id"] == AccountAfter[event_id_column],
        ],
    )
    return Joined.select(
        ExpectedAccount["Record.Id"].name("survey_result_id"),
        ExpectedAccount.Participant__c.name("participant_contact_id"),
        ExpectedAccount["Account.Id"].name("expected_account_id"),
        AccountAfter.Id.name("observed_account_id"),
        ExpectedAccount.Survey_Index_Number__c.name("survey_index_number"),
        ExpectedAccount.Completion_Status_Timestamp__c.name("survey_completion_timestamp"),
        survey_completion_occurred_on_or_after_launch,
        ExpectedAccount.CABOR_Completion_Date__c_is_deterministic.name(
            "cabor_lookup_is_deterministic"
        ),
        **{
            f"expected__{field}": ExpectedAccount[field]
            for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW
        },
        **{f"observed__{field}": AccountAfter[field] for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW},
    )


def rollup_account_comparison(ExpectedRollups: ir.Table, AccountSnapshot: ir.Table) -> ir.Table:
    """LEFT JOIN expected rollup counts to Account fields from the same snapshot.

    Input ExpectedRollups is expected_survey_rollups() output. Preserve the one
    row per person Account grain; a duplicate observed Account produces duplicate
    expected_account_id values and fails the uniqueness expectation.
    """
    AccountSnapshot = AccountSnapshot.view()
    Joined = ExpectedRollups.left_join(
        AccountSnapshot, ExpectedRollups["Account.Id"] == AccountSnapshot.Id
    )
    return Joined.select(
        ExpectedRollups["Account.Id"].name("expected_account_id"),
        ExpectedRollups.PersonContactId.name("person_contact_id"),
        AccountSnapshot.Id.name("observed_account_id"),
        **{f"expected__{field}": ExpectedRollups[field] for field in ROLLUP_ACCOUNT_FIELDS},
        **{f"observed__{field}": AccountSnapshot[field] for field in ROLLUP_ACCOUNT_FIELDS},
    )


def flow_account_query(
    history: Mapping[str, ir.Table],
    *,
    survey_result_id: str,
    account_before_at: date | datetime,
    execution_at: date | datetime,
    account_after_at: date | datetime,
    flow_run_date: date,
) -> ir.Table:
    """Return one event's expected/observed comparison directly over history.

    Lineage: snapshot(Account BEFORE) + snapshot(Contact at execution) +
    snapshot(Survey_Result__c at execution) -> join_account -> add_flow_context ->
    expected_account_values -> flow_account_comparison -> snapshot(Account AFTER).
    Named local variables mirror the Salesforce objects and existing expressions.

    Only the selected trigger is projected; FlowRecordLookups retain all survey
    records at execution. AFTER observations are explicitly bound to that event.
    Caller verifies eligibility (Complete transition, no exemption, async work
    settled) and org-local execution date. SCD2 date-grain history cannot represent
    BEFORE/AFTER instants within one day. No latest-state fallback is allowed.
    """
    if not isinstance(survey_result_id, str) or not survey_result_id.strip():
        raise ValueError("survey_result_id must identify one verified triggering event")
    if not isinstance(flow_run_date, date) or isinstance(flow_run_date, datetime):
        raise TypeError("flow_run_date must be the org-local execution date")
    times = (account_before_at, execution_at, account_after_at)
    if any(not isinstance(value, date) for value in times):
        raise TypeError("BEFORE, execution and AFTER must be explicit dates or datetimes")
    try:
        ordered = account_before_at < execution_at < account_after_at
    except TypeError as error:
        raise ValueError(
            "Temporal bindings must use comparable date/time types and time zones"
        ) from error
    if not ordered:
        raise ValueError("Require account_before_at < execution_at < account_after_at")

    AccountBefore = snapshot(history["Account"], as_of=account_before_at)
    ContactAtExecution = snapshot(history["Contact"], as_of=execution_at)
    Survey_Result__c = snapshot(history["Survey_Result__c"], as_of=execution_at)
    AccountAfter = snapshot(history["Account"], as_of=account_after_at)
    Trigger = Survey_Result__c.filter(Survey_Result__c.Id == survey_result_id)
    Record = join_account(Trigger, ContactAtExecution, AccountBefore)
    Record = add_flow_context(Record, Survey_Result__c, flow_run_date=ibis.literal(flow_run_date))
    ExpectedAccount = expected_account_values(Record)
    AccountAfterBySurveyEvent = AccountAfter.mutate(survey_result_id=ibis.literal(survey_result_id))
    return flow_account_comparison(ExpectedAccount, AccountAfterBySurveyEvent)


def rollup_account_query(
    history: Mapping[str, ir.Table], *, as_of: date | datetime | None = None
) -> ir.Table:
    """Compare rollups and independent observed fields at one effective snapshot.

    Lineage: Account.PersonContactId -> Survey_Result__c.Participant__c -> the
    existing 19 field formulas -> expected/observed comparison. as_of=None uses
    current flags on both relations. Preserve zero-child Accounts and duplicates.
    """
    AccountSnapshot = snapshot(history["Account"], as_of=as_of)
    SurveyResultSnapshot = snapshot(history["Survey_Result__c"], as_of=as_of)
    ExpectedRollups = expected_survey_rollups(AccountSnapshot, SurveyResultSnapshot)
    return rollup_account_comparison(ExpectedRollups, AccountSnapshot)
