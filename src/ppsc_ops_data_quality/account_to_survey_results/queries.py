"""Expected Account values compiled from pinned native metadata into Ibis.

    Record = join_account(Survey_Result__c, Contact, Account)
    Record = add_flow_context(Record, Survey_Result__c, flow_run_date=run_date)
    ExpectedAccount = expected_account_values(Record)
    query = to_sqlglot(ExpectedAccount, projection_lineage=PROJECTION_LINEAGE)
    sql = query.sql(dialect="athena", pretty=True)

The shared metadata compiler owns Flow decisions, assignments, lookups and the
age formula. This application binds history/relationships and comparison scope.
The pinned QA2 metadata is provisional; live trigger eligibility and production
Flow/version selection require local verification.

Complete Ibis composition before compiling with core.queries.sql.to_sqlglot().
Supply this domain's PROJECTION_LINEAGE mapping explicitly for annotations. The
query builders themselves do not compile, execute, or attach metadata to Ibis.

CASE order and assigned NULLs matter. Unselected Account assignments retain BEFORE
values; unreachable FlowDecisions return typed NULL targets. Source behavior is
preserved, including the consent assignments documented in the lineage mapping.

Grain: one candidate survey event per Record.Id, not a reconstructed Account
history. Supply unique IDs, Account BEFORE state, Contact/lookup data at execution,
and the org-local execution DATE. Select qualifying events upstream (Complete
transition, automation exemption disabled, async path settled). Current snapshots
alone produce hypothetical per-event projections. LEFT JOINs retain missing
parents. Snapshot rollups use a separate person Account grain.

This module builds native Ibis expressions and executes no data. Athena compiler
integration is isolated in core/queries/sql.py.
"""

from collections.abc import Mapping, Sequence
from datetime import date, datetime

import ibis
import ibis.expr.types as ir
from ppsc_metadata.sources.salesforce_flow import flow_assignments, flow_context

from ppsc_ops_data_quality.core.queries.snapshot import snapshot

from .lineage import ROLLUP_FIELD_LINEAGE
from .metadata import FLOW_FIELDS, FLOW_REQUEST, metadata_inputs

ACCOUNT_FIELDS_ASSIGNED_BY_FLOW = FLOW_FIELDS


def join_account(Survey_Result__c: ir.Table, Contact: ir.Table, Account: ir.Table) -> ir.Table:
    """Build Record with the same relationship paths used by the Flow.

    Lineage: datamodel-Fields Survey_Result__c.Participant__c is Master-Detail(Contact);
    each FlowRecordUpdate targets Account.Id = $Record.Participant__r.AccountId.
    Account fields are BEFORE values, named Participant__r.Account.<API name>.
    Contact.Birthdate supplies $Record.Participant__r.Birthdate. All joins are left
    joins; missing parents remain visible through NULL relationship columns.
    """
    Survey_Result__c = Survey_Result__c.alias("Survey_Result__c")
    Contact = Contact.alias("Contact")
    Account = Account.alias("Account")
    Record = Survey_Result__c.select(
        "Id",
        "Participant__c",
        "Survey_Index_Number__c",
        "Completion_Status__c",
        "Consent_Status__c",
        "Completion_Status_Timestamp__c",
        "California_Signature__c",
    )
    Record = Record.left_join(Contact, Record.Participant__c == Contact.Id).select(
        Record,
        Contact.AccountId.name("Participant__r.AccountId"),
        Contact.Birthdate.name("Participant__r.Birthdate"),
    )
    return Record.left_join(Account, Record["Participant__r.AccountId"] == Account.Id).select(
        Record,
        Account.Id.name("Participant__r.Account.Id"),
        **{
            f"Participant__r.Account.{field}": Account[field]
            for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW
        },
    )


def _eligible(Record: ir.Table) -> ir.BooleanValue:
    """Observable completion guard; full trigger eligibility remains caller policy."""
    return Record.Completion_Status__c == "Complete"


def add_flow_context(
    Record: ir.Table, Survey_Result__c: ir.Table, *, flow_run_date: ir.DateValue
) -> ir.Table:
    """Compile native lookup filters, first-row semantics and referenced formulas."""
    return flow_context(
        Record,
        {"Survey_Result__c": Survey_Result__c},
        metadata_inputs().flow["Metadata"],
        FLOW_REQUEST,
        flow_run_date=flow_run_date,
        eligibility=_eligible,
    )


def derived_account_expressions(Record: ir.Table) -> tuple[ir.Value, ...]:
    """The selected native QA2 assignments; SQL display text is never executed."""
    return tuple(
        flow_assignments(
            Record,
            metadata_inputs().flow["Metadata"],
            FLOW_REQUEST,
            eligibility=_eligible,
        ).expressions.values()
    )


def survey_rollup_indicators(Record: ir.Table) -> tuple[ir.Value, ...]:
    """Define per-child 1/0 Ibis CASE indicators to sum per person Account.

    Bind to Survey_Result__c joined through Account.PersonContactId. An unmatched
    LEFT JOIN row takes ELSE 0. These are current-snapshot rollup indicators, not
    event-level Account assignments. Original definitions and source caveats are
    in ROLLUP_FIELD_LINEAGE and ROLLUP_SOURCE_NOTES.
    """
    Complete = Record.Completion_Status__c == "Complete"
    Yes = Record.Consent_Status__c == "Yes"
    No = Record.Consent_Status__c == "No"
    NotRevoked = Record.Consent_Revoked__c == False
    Index = Record.Survey_Index_Number__c
    count_completed_ehr_authorization = Complete & (Index == "1003")
    ehr_authorized_indicator = ibis.cases(
        (count_completed_ehr_authorization, 1),
        else_=0,
    ).name("EHR_Authorized__pc")

    count_of_completed_ehr_auth_indicator = ibis.cases(
        (count_completed_ehr_authorization, 1),
        else_=0,
    ).name("Count_of_Completed_EHR_Auth__pc")

    count_completed_primary_consent = Complete & (Index == "1001")
    count_of_completed_primary_consent_indicator = ibis.cases(
        (count_completed_primary_consent, 1),
        else_=0,
    ).name("Count_of_Completed_Primary_Consent__pc")

    count_completed_primary_consent_updates = Complete & (Index == "1005")
    count_of_completed_reconsent_indicator = ibis.cases(
        (count_completed_primary_consent_updates, 1),
        else_=0,
    ).name("Count_of_Completed_Reconsent__pc")

    count_completed_lifestyle_surveys = Complete & (Index == "2005")
    ppi_2_completion_count_indicator = ibis.cases(
        (count_completed_lifestyle_surveys, 1),
        else_=0,
    ).name("PPI_2_Completion_Count__pc")

    count_completed_overall_health_surveys = Complete & (Index == "2003")
    ppi_3_completion_count_indicator = ibis.cases(
        (count_completed_overall_health_surveys, 1),
        else_=0,
    ).name("PPI_3_Completion_Count__pc")

    count_active_ehr_consent = Complete & Yes & NotRevoked & Index.isin(["1003", "1004"])
    ehr_consent_active_indicator = ibis.cases(
        (count_active_ehr_consent, 1),
        else_=0,
    ).name("EHR_Consent_Active__pc")

    count_declined_ehr_consent = Complete & No & NotRevoked & Index.isin(["1003", "1004"])
    ehr_consent_declined_indicator = ibis.cases(
        (count_declined_ehr_consent, 1),
        else_=0,
    ).name("EHR_Consent_Declined__pc")

    count_completed_unrevoked_basics_surveys = Complete & NotRevoked & Index.isin(["2001", "2002"])
    pp1_basics_survey_complete_indicator = ibis.cases(
        (count_completed_unrevoked_basics_surveys, 1),
        else_=0,
    ).name("PP1_Basics_Survey_Complete__pc")

    count_declined_primary_consent_updates = Complete & No & NotRevoked & (Index == "1005")
    re_consent_declined_indicator = ibis.cases(
        (count_declined_primary_consent_updates, 1),
        else_=0,
    ).name("Re_Consent_Declined__pc")

    count_active_primary_consent_updates = Complete & Yes & NotRevoked & (Index == "1005")
    re_consent_active_indicator = ibis.cases(
        (count_active_primary_consent_updates, 1),
        else_=0,
    ).name("Re_consent_Active__pc")

    count_declined_primary_consent = Complete & No & NotRevoked & Index.isin(["1005", "1002"])
    primary_consent_declined_indicator = ibis.cases(
        (count_declined_primary_consent, 1),
        else_=0,
    ).name("Primary_Consent_Declined__pc")

    count_ever_authorized_ehr_consent = Complete & Yes & Index.isin(["1003", "1004"])
    ehr_consent_ever_indicator = ibis.cases(
        (count_ever_authorized_ehr_consent, 1),
        else_=0,
    ).name("EHR_Consent_Ever__pc")

    count_completed_active_assent = Complete & Yes & NotRevoked & (Index == "1008")
    assent_completion_count_indicator = ibis.cases(
        (count_completed_active_assent, 1),
        else_=0,
    ).name("Assent_Completion_Count__pc")

    count_completed_active_pediatric_permission = Complete & Yes & NotRevoked & (Index == "1007")
    pediatric_permission_completion_count_indicator = ibis.cases(
        (count_completed_active_pediatric_permission, 1),
        else_=0,
    ).name("Pediatric_Permission_Completion_Count__pc")

    count_active_permission_ages_zero_to_six = Yes & NotRevoked & (Index == "1002")
    x0_6_peds_permission_count_indicator = ibis.cases(
        (count_active_permission_ages_zero_to_six, 1),
        else_=0,
    ).name("X0_6_Peds_Permission_Count__pc")

    count_declined_permission_ages_zero_to_six = No & (Index == "1002")
    x0_6_peds_permission_declined_count_indicator = ibis.cases(
        (count_declined_permission_ages_zero_to_six, 1),
        else_=0,
    ).name("X0_6_Peds_Permission_Declined_Count__pc")

    count_revoked_permission_ages_zero_to_six = (Record.Consent_Revoked__c == True) & (
        Index == "1002"
    )
    x0_6_peds_permission_revoked_count_indicator = ibis.cases(
        (count_revoked_permission_ages_zero_to_six, 1),
        else_=0,
    ).name("X0_6_Peds_Permission_Revoked_Count__pc")

    count_completed_active_pediatric_ehr_consent = Complete & Yes & NotRevoked & (Index == "1004")
    ehr_pediatric_complete_indicator = ibis.cases(
        (count_completed_active_pediatric_ehr_consent, 1),
        else_=0,
    ).name("EHR_Pediatric_Complete__pc")

    return (
        ehr_authorized_indicator,
        count_of_completed_ehr_auth_indicator,
        count_of_completed_primary_consent_indicator,
        count_of_completed_reconsent_indicator,
        ppi_2_completion_count_indicator,
        ppi_3_completion_count_indicator,
        ehr_consent_active_indicator,
        ehr_consent_declined_indicator,
        pp1_basics_survey_complete_indicator,
        re_consent_declined_indicator,
        re_consent_active_indicator,
        primary_consent_declined_indicator,
        ehr_consent_ever_indicator,
        assent_completion_count_indicator,
        pediatric_permission_completion_count_indicator,
        x0_6_peds_permission_count_indicator,
        x0_6_peds_permission_declined_count_indicator,
        x0_6_peds_permission_revoked_count_indicator,
        ehr_pediatric_complete_indicator,
    )


def expected_account_values(
    Record: ir.Table, *, fields: Sequence[ir.Value] | None = None
) -> ir.Table:
    """Select expected Account AFTER values and lookup determinism evidence.

    fields accepts ordinary named Ibis values. Pass a subset of
    derived_account_expressions(Record), or compose a value directly in select().
    Each output name must be unique; branch priority belongs in its CASE.

    Multiple unsorted pediatric permissions leave the CABOR signature unresolved:
    value NULL, evidence flag FALSE. No permission produces a known NULL with the
    flag TRUE. This evidence does not alter the authored assignment condition.
    """
    fields = tuple(derived_account_expressions(Record) if fields is None else fields)
    names = [field.get_name() for field in fields]
    if len(set(names)) != len(names):
        raise ValueError("Supply one Ibis expression per output name.")
    expressions = {field.get_name(): field for field in fields}
    if "CABOR_Completion_Date__c" in expressions:
        expressions["CABOR_Completion_Date__c_is_deterministic"] = cabor_lookup_is_deterministic(
            Record
        )
    return Record.select(
        Record.Id.name("Record.Id"),
        Record["Participant__r.Account.Id"].name("Account.Id"),
        Record.Participant__c,
        Record.Survey_Index_Number__c,
        Record.Completion_Status_Timestamp__c,
        Record["FlowRecordLookup.Pediatric_Permission_For_Assent.match_count"],
        **expressions,
    )


def survey_rollup_expressions(Record: ir.Table) -> dict[str, ir.Value]:
    """Compose SUM(CASE WHEN predicate THEN 1 ELSE 0 END) for each rollup."""
    return {indicator.get_name(): indicator.sum() for indicator in survey_rollup_indicators(Record)}


def _survey_rollup_record(Account: ir.Table, Survey_Result__c: ir.Table) -> ir.Table:
    Account = (
        Account.filter(Account.IsPersonAccount)
        .select("Id", "PersonContactId")
        .alias("Person_Account")
    )
    Survey_Result__c = Survey_Result__c.select(
        "Participant__c",
        "Completion_Status__c",
        "Survey_Index_Number__c",
        "Consent_Status__c",
        "Consent_Revoked__c",
    ).alias("Survey_Result__c")
    return Account.left_join(
        Survey_Result__c,
        Account.PersonContactId == Survey_Result__c.Participant__c,
    ).select(
        Account.Id.name("Account.Id"),
        Account.PersonContactId,
        Survey_Result__c.Completion_Status__c,
        Survey_Result__c.Survey_Index_Number__c,
        Survey_Result__c.Consent_Status__c,
        Survey_Result__c.Consent_Revoked__c,
    )


def expected_survey_rollups(Account: ir.Table, Survey_Result__c: ir.Table) -> ir.Table:
    """Compose conditional counts at one row per person Account.

    LEFT JOIN preserves zero-child Accounts. Duplicate source Accounts contribute
    to the same group, just as duplicate survey matches do. Inputs are complete
    snapshots with deleted survey rows excluded upstream.
    """
    Record = _survey_rollup_record(Account, Survey_Result__c)
    return Record.group_by("Account.Id", "PersonContactId").aggregate(
        **survey_rollup_expressions(Record)
    )


ROLLUP_ACCOUNT_FIELDS = tuple(field.removeprefix("Account.") for field in ROLLUP_FIELD_LINEAGE)
SURVEY_COMPLETION_FLOW_LAUNCH_DATE = date(2024, 12, 16)


def cabor_lookup_is_deterministic(Record: ir.Table) -> ir.BooleanValue:
    """Keep unsorted permission ambiguity separate from the authored assignment."""
    return flow_assignments(
        Record,
        metadata_inputs().flow["Metadata"],
        FLOW_REQUEST,
        eligibility=_eligible,
    ).deterministic["CABOR_Completion_Date__c"]


def flow_account_comparison(
    Record: ir.Table,
    AccountAfter: ir.Table,
    *,
    event_id_column: str = "survey_result_id",
) -> ir.Table:
    """Project resolved per-event assignments beside independent AFTER values.

    Input Record is add_flow_context() output. AccountAfter has
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
        Record.Completion_Status_Timestamp__c.date()
        >= ibis.literal(SURVEY_COMPLETION_FLOW_LAUNCH_DATE, type="date")
    ).name("survey_completion_occurred_on_or_after_launch")
    AccountAfter = AccountAfter.alias("Account_After")
    Joined = Record.left_join(
        AccountAfter,
        [
            Record["Participant__r.Account.Id"] == AccountAfter.Id,
            Record.Id == AccountAfter[event_id_column],
        ],
    )
    return Joined.select(
        Record.Id.name("survey_result_id"),
        Record.Participant__c.name("participant_contact_id"),
        Record["Participant__r.Account.Id"].name("expected_account_id"),
        AccountAfter.Id.name("observed_account_id"),
        Record.Survey_Index_Number__c.name("survey_index_number"),
        Record.Completion_Status_Timestamp__c.name("survey_completion_timestamp"),
        survey_completion_occurred_on_or_after_launch,
        cabor_lookup_is_deterministic(Record).name("cabor_lookup_is_deterministic"),
        **{f"expected__{field.get_name()}": field for field in derived_account_expressions(Record)},
        **{f"observed__{field}": AccountAfter[field] for field in ACCOUNT_FIELDS_ASSIGNED_BY_FLOW},
    )


def rollup_account_comparison(
    Account: ir.Table, Survey_Result__c: ir.Table, AccountSnapshot: ir.Table
) -> ir.Table:
    """Aggregate resolved conditional counts beside independently observed fields.

    Group by an observation's row identity, not just its values: identical
    duplicate observations must remain separate comparison rows. Joining before
    aggregation otherwise preserves the same source-account/survey multiplicity
    as expected_survey_rollups(), including unmatched observations and zero children.
    """
    Record = _survey_rollup_record(Account, Survey_Result__c)
    AccountSnapshot = AccountSnapshot.mutate(
        _comparison_observation_row=ibis.row_number().over(ibis.window())
    ).alias("Account_Snapshot")
    Joined = Record.left_join(AccountSnapshot, Record["Account.Id"] == AccountSnapshot.Id).select(
        Record,
        AccountSnapshot.Id.name("observed_account_id"),
        AccountSnapshot._comparison_observation_row,
        **{f"observed__{field}": AccountSnapshot[field] for field in ROLLUP_ACCOUNT_FIELDS},
    )
    observed_fields = [f"observed__{field}" for field in ROLLUP_ACCOUNT_FIELDS]
    Comparison = Joined.group_by(
        Joined["Account.Id"].name("expected_account_id"),
        Joined.PersonContactId.name("person_contact_id"),
        Joined.observed_account_id,
        Joined._comparison_observation_row,
        *[Joined[field] for field in observed_fields],
    ).aggregate(
        **{
            f"expected__{field}": expression
            for field, expression in survey_rollup_expressions(Joined).items()
        }
    )
    return Comparison.select(
        "expected_account_id",
        "person_contact_id",
        "observed_account_id",
        *[f"expected__{field}" for field in ROLLUP_ACCOUNT_FIELDS],
        *observed_fields,
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
    flow_account_comparison -> snapshot(Account AFTER).
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

    AccountBefore = snapshot(history["Account"], as_of=account_before_at).alias("Account_Before")
    ContactAtExecution = snapshot(history["Contact"], as_of=execution_at).alias(
        "Contact_At_Execution"
    )
    Survey_Result__c = snapshot(history["Survey_Result__c"], as_of=execution_at).alias(
        "Survey_Results_At_Execution"
    )
    AccountAfter = snapshot(history["Account"], as_of=account_after_at)
    Trigger = Survey_Result__c.filter(Survey_Result__c.Id == survey_result_id).alias(
        "Trigger_Survey_Result"
    )
    Record = join_account(Trigger, ContactAtExecution, AccountBefore)
    Record = add_flow_context(Record, Survey_Result__c, flow_run_date=ibis.literal(flow_run_date))
    AccountAfterBySurveyEvent = AccountAfter.mutate(survey_result_id=ibis.literal(survey_result_id))
    return flow_account_comparison(Record, AccountAfterBySurveyEvent)


def rollup_account_query(
    history: Mapping[str, ir.Table], *, as_of: date | datetime | None = None
) -> ir.Table:
    """Compare rollups and independent observed fields at one effective snapshot.

    Lineage: Account.PersonContactId -> Survey_Result__c.Participant__c -> the
    existing 19 field formulas -> expected/observed comparison. as_of=None uses
    current flags on both relations. Preserve zero-child Accounts and duplicates.
    """
    AccountSnapshot = snapshot(history["Account"], as_of=as_of).alias("Account_At_Snapshot")
    SurveyResultSnapshot = snapshot(history["Survey_Result__c"], as_of=as_of).alias(
        "Survey_Results_At_Snapshot"
    )
    return rollup_account_comparison(AccountSnapshot, SurveyResultSnapshot, AccountSnapshot)
