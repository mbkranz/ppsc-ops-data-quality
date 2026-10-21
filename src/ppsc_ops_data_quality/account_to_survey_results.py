"""Expected Account values authored in Ibis, with lineage added after compilation.

    Record = join_account(Survey_Result__c, Contact, Account)
    Record = add_flow_context(Record, Survey_Result__c, flow_run_date=run_date)
    ExpectedAccount = expected_account_values(Record)
    query = to_sqlglot(ExpectedAccount)
    sql = query.sql(dialect="athena", pretty=True)

Definitions are ordinary named Ibis conditions and CASE expressions, bound to the
supplied Record relation. Builders collect expressions; there are no per-rule
factories, custom rule classes, applicability fields or GX adapters. To select a
subset, pass ordinary named Ibis values to expected_account_values(fields=...).

Complete Ibis composition before calling to_sqlglot(). That helper isolates the
Athena compiler integration and attaches metadata to final projected fields by
exact output alias, using account_to_survey_results_lineage.py. It does not depend
on compiler-generated table aliases or WHEN positions. Branch IDs and their
original sources remain nested in the field's meta["ppsc"] record.

Comments explain generated SQL. Structured meta is retained by SQLGlot copy() and
Expression.dump()/load(); SQL text alone does not serialize it. Recompiling Ibis
creates a new AST and must run the annotation step again. Attach annotations after
any SQLGlot rewrite that replaces projected nodes. The independent mapping is
authoritative; arbitrary metadata is never attached to Ibis objects themselves.

CASE order and assigned NULLs matter. Unselected Account assignments retain BEFORE
values; unreachable FlowDecisions return typed NULL targets. Source behavior is
preserved, including the consent assignments documented in the lineage mapping.

Grain: one candidate survey event per Record.Id, not a reconstructed Account
history. Supply unique IDs, Account BEFORE state, Contact/lookup data at execution,
and the org-local execution DATE. Select qualifying events upstream (Complete
transition, automation exemption disabled, async path settled). Current snapshots
alone produce hypothetical per-event projections. LEFT JOINs retain missing
parents. Snapshot rollups use a separate person Account grain.

Runtime dependencies: ibis-framework and its compatible sqlglot version. This
module builds queries and executes no data. Keep the compiler integration tested
when upgrading Ibis; it is the only compiler-namespace call in the module.
"""

from collections.abc import Sequence
from copy import deepcopy

import ibis
import ibis.expr.types as ir
from sqlglot import exp

from ppsc_ops_data_quality.account_to_survey_results_lineage import PROJECTION_LINEAGE

ACCOUNT_FIELDS_ASSIGNED_BY_FLOW = (
    "Age_at_Time_of_Consent__pc",
    "CABOR_Completion_Date__c",
    "Earliest_Primary_Consent_Date_for_Report__c",
    "Latest_Primary_Consent_Date_for_Report__c",
    "EHR_Consent_Date_Time__c",
    "EHR_Reconsent_Date_Time__c",
    "Update_to_Primary_Consent_Completed__c",
    "Basics_Date_Time__c",
    "Overall_Health_Date_Time__c",
    "Lifestyle_Date_Time__c",
    "Personal_and_Family_History_Complete__c",
    "HC_Access_Date_Time__c",
    "Life_Functioning_Date_Time__c",
    "First_Physical_Measurement_Date_Time__c",
    "Last_Physical_Measurement_Date_Time__c",
    "EH_Date_Time__c",
    "Behavioral_Health_Completion__c",
    "Environmental_Exposures_Date_Time__c",
    "Social_Determinants_of_Health_Completion__c",
)


def join_account(Survey_Result__c: ir.Table, Contact: ir.Table, Account: ir.Table) -> ir.Table:
    """Build Record with the same relationship paths used by the Flow.

    Lineage: datamodel-Fields Survey_Result__c.Participant__c is Master-Detail(Contact);
    each FlowRecordUpdate targets Account.Id = $Record.Participant__r.AccountId.
    Account fields are BEFORE values, named Participant__r.Account.<API name>.
    Contact.Birthdate supplies $Record.Participant__r.Birthdate. All joins are left
    joins; missing parents remain visible through NULL relationship columns.
    """
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


def _append_first_FlowRecordLookup(Record, Candidate, resource, sort_field, *, exclude_Record):
    """Implement per-Record lookup join + ASC/LIMIT 1 without changing row grain.

    This helper implements mechanics only; the public lookup functions own their
    source filters. Lookup fields retain resource.<field> names. ASC uses NULLS
    FIRST. Equal sort keys may pick any tied row, as in the source lookup. Only
    existence (consent) or the equal sort value (physical) is consumed downstream.
    """
    Candidate = Candidate.view()
    conditions = [Record.Participant__c == Candidate.Participant__c]
    if exclude_Record:
        conditions.append(Record.Id != Candidate.Id)
    joined = Record.left_join(Candidate, conditions).select(
        Record,
        **{f"{resource}.{field}": Candidate[field] for field in ("Id", sort_field)},
    )
    window = ibis.window(
        group_by=joined.Id,
        order_by=joined[f"{resource}.{sort_field}"].asc(nulls_first=True),
    )
    ranked = joined.mutate(_lookup_rank=ibis.row_number().over(window))
    return ranked.filter(ranked._lookup_rank == 0).drop("_lookup_rank")


def FlowRecordLookup_Earliest_Other_Yes_Primary_Consent(
    Record: ir.Table, Survey_Result__c: ir.Table
) -> ir.Table:
    """Source: FlowRecordLookup.getEarliestPrimaryConsent; workbook row 14485.

    Append the earliest other Yes primary consent for each Record.

    Lineage: FlowRecordLookup getEarliestPrimaryConsent, workbook row 14485.
    Filters: index IN (1001,1002), same Participant__c, Consent_Status__c = Yes,
    Id <> Record.Id. Sort: Consent_Status_Timestamp__c ASC, first record only.
    The lookup does NOT filter Completion_Status__c. Raw attributes are used;
    generated SQL in the workbook is explanatory, not authoritative.
    """
    Candidate = Survey_Result__c.filter(
        Survey_Result__c.Survey_Index_Number__c.isin(["1001", "1002"])
        & (Survey_Result__c.Consent_Status__c == "Yes")
    ).select("Id", "Participant__c", "Consent_Status_Timestamp__c")
    return _append_first_FlowRecordLookup(
        Record,
        Candidate,
        "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent",
        "Consent_Status_Timestamp__c",
        exclude_Record=True,
    )


def FlowRecordLookup_Earliest_Other_Yes_EHR_Consent(
    Record: ir.Table, Survey_Result__c: ir.Table
) -> ir.Table:
    """Source: FlowRecordLookup.getEarliestEgetEarliestEHRConsentHRConsent; workbook row 14492.

    Append the earliest other Yes EHR consent; retain the source ID in provenance.

    Lineage: FlowRecordLookup getEarliestEgetEarliestEHRConsentHRConsent, row 14492.
    Filters: index IN (1003,1004), same participant, Yes, Id <> Record.Id.
    Sort: Consent_Status_Timestamp__c ASC. No Completion_Status__c filter.
    The rendered Expression cell is corrupted; these filters come from raw attrs.
    """
    Candidate = Survey_Result__c.filter(
        Survey_Result__c.Survey_Index_Number__c.isin(["1003", "1004"])
        & (Survey_Result__c.Consent_Status__c == "Yes")
    ).select("Id", "Participant__c", "Consent_Status_Timestamp__c")
    return _append_first_FlowRecordLookup(
        Record,
        Candidate,
        "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent",
        "Consent_Status_Timestamp__c",
        exclude_Record=True,
    )


def FlowRecordLookup_First_Remote_Physical_Measurement(
    Record: ir.Table, Survey_Result__c: ir.Table
) -> ir.Table:
    """Source: FlowRecordLookup.getFirstPhysicalMeasurement; workbook row 14518.

    Append the first 2009 completion timestamp for each Record's participant.

    Lineage: FlowRecordLookup getFirstPhysicalMeasurement, workbook row 14518.
    Filters: index = 2009 and same participant. Includes Record itself and does NOT
    require candidate Complete. Sort: Completion_Status_Timestamp__c ASC, first only.
    The rendered Expression is corrupted; the raw attributes supply these filters.
    """
    Candidate = Survey_Result__c.filter(Survey_Result__c.Survey_Index_Number__c == "2009").select(
        "Id", "Participant__c", "Completion_Status_Timestamp__c"
    )
    return _append_first_FlowRecordLookup(
        Record,
        Candidate,
        "FlowRecordLookup.First_Remote_Physical_Measurement",
        "Completion_Status_Timestamp__c",
        exclude_Record=False,
    )


def FlowRecordLookup_Pediatric_Permission_For_Assent(
    Record: ir.Table, Survey_Result__c: ir.Table
) -> ir.Table:
    """Source: FlowRecordLookup.Get_Permission_1007; workbook row 14500.

    Append permission existence and its unambiguous California signature.

    Lineage: FlowRecordLookup Get_Permission_1007, workbook row 14500. Filters:
    index = 1007, Yes, same participant, Id <> Record.Id; there is NO sort field.
    This resource is used only by the 1008 branch, so a 1007 cannot be Record itself.
    The join below gates this lookup to the 1008 connector, even when Record contains other indexes.

    With >1 match, this conservative translation marks CABOR unresolved. Id is a
    representative source ID used ONLY to test existence; it is not a claim about
    which row Salesforce selected. California_Signature__c is NULL when ambiguous.
    match_count exposes this condition; the expected projection includes a
    CABOR_Completion_Date__c_is_deterministic flag. Zero matches means a known NULL.
    """
    Permission = Survey_Result__c.filter(
        (Survey_Result__c.Survey_Index_Number__c == "1007")
        & (Survey_Result__c.Consent_Status__c == "Yes")
    )
    Permission = Permission.group_by("Participant__c").aggregate(
        Id=Permission.Id.min(),
        match_count=Permission.count(),
        California_Signature__c=ibis.cases(
            (Permission.count() == 1, Permission.California_Signature__c.min()),
            else_=ibis.null().cast("timestamp"),
        ),
    )
    # Restrict the lookup to its actual 1008 route. It is not a generic 1007 self-lookup.
    return Record.left_join(
        Permission,
        [
            Record.Participant__c == Permission.Participant__c,
            Record.FlowDecision_Survey_Completion_Route_target
            == "FlowRecordLookup.Pediatric_Permission_For_Assent",
        ],
    ).select(
        Record,
        Permission.Id.name("FlowRecordLookup.Pediatric_Permission_For_Assent.Id"),
        Permission.match_count.fill_null(0).name(
            "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count"
        ),
        Permission.California_Signature__c.name(
            "FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"
        ),
    )


def FlowFormula_Age_At_Execution(Record: ir.Table, flow_run_date: ir.DateValue) -> ir.IntegerValue:
    """Source: FlowFormula.formAgeCalculation; workbook row 14573.

    Translated FlowFormula formAgeCalculation: numeric execution-date age.

    Lineage: processing-Flow-elements row 14573.

    FLOOR((TODAY() - $Record.Participant__r.Birthdate) / 365.25). flow_run_date is
    the explicit org-local execution DATE replacing TODAY(), not consent date.
    Lineage: Contact.Birthdate -> Participant__r.Birthdate -> age calculation.
    The separate migration anniversary-age formula is not substituted here.
    """
    return (
        (flow_run_date.delta(Record["Participant__r.Birthdate"], unit="day") / 365.25)
        .floor()
        .cast("int64")
    )


def add_flow_context(
    Record: ir.Table, Survey_Result__c: ir.Table, *, flow_run_date: ir.DateValue
) -> ir.Table:
    """Compose translated FlowDecisions, lookup results and execution-date age.

    Conditions below select Flow connectors; names explicitly identify decision
    outputs. Unreached decisions have a NULL target. Original IDs and workbook
    rows are in FLOW_ENTITY_LINEAGE and PROJECTION_LINEAGE. The four lookups
    preserve the event grain, including missing or ambiguous lookup results.
    """
    Index = Record.Survey_Index_Number__c
    Yes = Record.Consent_Status__c == "Yes"
    Complete = Record.Completion_Status__c == "Complete"
    route_to_earliest_other_yes_primary_consent = Complete & (Index.isin(["1001", "1002"]) & Yes)
    route_to_earliest_other_yes_ehr_consent = Complete & (Index.isin(["1003", "1004"]) & Yes)
    route_to_primary_consent_update_completion = Complete & (Index == "1005")
    route_to_pediatric_permission_for_assent = Complete & (
        (Index == "1008") & Record.Consent_Status__c.isin(["Yes", "N/A"])
    )
    route_to_basics_completion = Complete & Index.isin(["2001", "2002"])
    route_to_overall_health_completion = Complete & Index.isin(["2003", "2004"])
    route_to_lifestyle_completion = Complete & (Index == "2005")
    route_to_personal_and_family_history_completion = Complete & (Index == "2006")
    route_to_healthcare_access_completion = Complete & (Index == "2007")
    route_to_life_functioning_completion = Complete & (Index == "2008")
    route_to_first_remote_physical_measurement = Complete & (Index == "2009")
    route_to_emotional_health_completion = Complete & (Index == "2010")
    route_to_behavioral_health_completion = Complete & (Index == "2011")
    route_to_environmental_exposures_completion = Complete & (Index == "2012")
    route_to_social_determinants_completion = Complete & (Index == "2013")
    survey_completion_flow_decision = ibis.cases(
        (
            route_to_earliest_other_yes_primary_consent,
            "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent",
        ),
        (
            route_to_earliest_other_yes_ehr_consent,
            "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent",
        ),
        (
            route_to_primary_consent_update_completion,
            "FlowRecordUpdate.Primary_Consent_Update_Completion",
        ),
        (
            route_to_pediatric_permission_for_assent,
            "FlowRecordLookup.Pediatric_Permission_For_Assent",
        ),
        (route_to_basics_completion, "FlowRecordUpdate.Basics_Completion"),
        (route_to_overall_health_completion, "FlowRecordUpdate.Overall_Health_Completion"),
        (route_to_lifestyle_completion, "FlowRecordUpdate.Lifestyle_Completion"),
        (
            route_to_personal_and_family_history_completion,
            "FlowRecordUpdate.Personal_And_Family_History_Completion",
        ),
        (route_to_healthcare_access_completion, "FlowRecordUpdate.Healthcare_Access_Completion"),
        (route_to_life_functioning_completion, "FlowRecordUpdate.Life_Functioning_Completion"),
        (
            route_to_first_remote_physical_measurement,
            "FlowRecordLookup.First_Remote_Physical_Measurement",
        ),
        (route_to_emotional_health_completion, "FlowRecordUpdate.Emotional_Health_Completion"),
        (route_to_behavioral_health_completion, "FlowRecordUpdate.Behavioral_Health_Completion"),
        (
            route_to_environmental_exposures_completion,
            "FlowRecordUpdate.Environmental_Exposures_Completion",
        ),
        (
            route_to_social_determinants_completion,
            "FlowRecordUpdate.Social_Determinants_Completion",
        ),
        else_=ibis.null().cast("string"),
    ).name("FlowDecision_Survey_Completion_Route_target")

    Record = Record.mutate(survey_completion_flow_decision)
    Record = FlowRecordLookup_Earliest_Other_Yes_Primary_Consent(Record, Survey_Result__c)
    Record = FlowRecordLookup_Earliest_Other_Yes_EHR_Consent(Record, Survey_Result__c)
    Record = FlowRecordLookup_First_Remote_Physical_Measurement(Record, Survey_Result__c)
    Record = FlowRecordLookup_Pediatric_Permission_For_Assent(Record, Survey_Result__c)

    primary_consent_without_prior_yes = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent"
    ) & Record["FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id"].isnull()
    primary_consent_with_prior_yes = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent"
    ) & ~Record["FlowRecordLookup.Earliest_Other_Yes_Primary_Consent.Id"].isnull()
    primary_consent_account_update_flow_decision = ibis.cases(
        (primary_consent_without_prior_yes, "FlowRecordUpdate.Primary_Consent_Without_Prior_Yes"),
        (primary_consent_with_prior_yes, "FlowRecordUpdate.Primary_Consent_With_Prior_Yes"),
        else_=ibis.null().cast("string"),
    ).name("FlowDecision_Primary_Consent_Account_Update_target")

    ehr_consent_without_prior_yes = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent"
    ) & Record["FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id"].isnull()
    ehr_consent_with_prior_yes = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent"
    ) & ~Record["FlowRecordLookup.Earliest_Other_Yes_EHR_Consent.Id"].isnull()
    ehr_consent_account_update_flow_decision = ibis.cases(
        (ehr_consent_without_prior_yes, "FlowRecordUpdate.EHR_Consent_Without_Prior_Yes"),
        (ehr_consent_with_prior_yes, "FlowRecordUpdate.EHR_Consent_With_Prior_Yes"),
        else_=ibis.null().cast("string"),
    ).name("FlowDecision_EHR_Consent_Account_Update_target")

    assent_no_permission_and_no_primary_date = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.Pediatric_Permission_For_Assent"
    ) & (
        Record["FlowRecordLookup.Pediatric_Permission_For_Assent.Id"].isnull()
        & Record["Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c"].isnull()
    )
    assent_with_permission_or_primary_date = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.Pediatric_Permission_For_Assent"
    ) & ~(
        Record["FlowRecordLookup.Pediatric_Permission_For_Assent.Id"].isnull()
        & Record["Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c"].isnull()
    )
    assent_account_update_flow_decision = ibis.cases(
        (
            assent_no_permission_and_no_primary_date,
            "FlowRecordUpdate.Assent_No_Permission_And_No_Primary_Date",
        ),
        (
            assent_with_permission_or_primary_date,
            "FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date",
        ),
        else_=ibis.null().cast("string"),
    ).name("FlowDecision_Assent_Account_Update_target")

    Record = Record.mutate(
        primary_consent_account_update_flow_decision,
        ehr_consent_account_update_flow_decision,
        assent_account_update_flow_decision,
    )
    return Record.mutate(
        FlowFormula_Age_At_Execution=FlowFormula_Age_At_Execution(Record, flow_run_date)
    )


def derived_account_expressions(Record: ir.Table) -> tuple[ir.Value, ...]:
    """Define the 19 expected Account fields as ordinary named Ibis CASE values.

    Input is add_flow_context() output. Each condition selects an authored Flow
    assignment. Each ELSE explicitly retains the Account BEFORE value. A selected
    NULL value stays NULL. No query executes here. Bind again when changing the
    Record relation. Provenance is independent in ACCOUNT_FIELD_LINEAGE.
    """
    set_age_at_flow_execution = Record.FlowDecision_Survey_Completion_Route_target.isin(
        [
            "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent",
            "FlowRecordLookup.Pediatric_Permission_For_Assent",
        ]
    )
    age_at_flow_execution = ibis.cases(
        (set_age_at_flow_execution, Record.FlowFormula_Age_At_Execution),
        else_=Record["Participant__r.Account.Age_at_Time_of_Consent__pc"],
    ).name("Age_at_Time_of_Consent__pc")

    set_california_signature_from_primary_consent = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent"
    )
    set_california_signature_from_pediatric_permission = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.Pediatric_Permission_For_Assent"
    )
    california_signature_timestamp = ibis.cases(
        (set_california_signature_from_primary_consent, Record.California_Signature__c),
        (
            set_california_signature_from_pediatric_permission,
            Record["FlowRecordLookup.Pediatric_Permission_For_Assent.California_Signature__c"],
        ),
        else_=Record["Participant__r.Account.CABOR_Completion_Date__c"],
    ).name("CABOR_Completion_Date__c")

    set_earliest_primary_consent_report_timestamp = (
        Record.FlowDecision_Primary_Consent_Account_Update_target
        == "FlowRecordUpdate.Primary_Consent_With_Prior_Yes"
    ) | (
        Record.FlowDecision_Assent_Account_Update_target
        == "FlowRecordUpdate.Assent_With_Permission_Or_Primary_Date"
    )
    earliest_primary_consent_report_timestamp = ibis.cases(
        (set_earliest_primary_consent_report_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Earliest_Primary_Consent_Date_for_Report__c"],
    ).name("Earliest_Primary_Consent_Date_for_Report__c")

    set_latest_primary_consent_report_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target.isin(
            [
                "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent",
                "FlowRecordLookup.Pediatric_Permission_For_Assent",
            ]
        )
    )
    latest_primary_consent_report_timestamp = ibis.cases(
        (set_latest_primary_consent_report_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Latest_Primary_Consent_Date_for_Report__c"],
    ).name("Latest_Primary_Consent_Date_for_Report__c")

    set_ehr_consent_timestamp = (
        Record.FlowDecision_EHR_Consent_Account_Update_target
        == "FlowRecordUpdate.EHR_Consent_With_Prior_Yes"
    )
    ehr_consent_timestamp = ibis.cases(
        (set_ehr_consent_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.EHR_Consent_Date_Time__c"],
    ).name("EHR_Consent_Date_Time__c")

    set_ehr_reconsent_timestamp = (
        Record.FlowDecision_EHR_Consent_Account_Update_target
        == "FlowRecordUpdate.EHR_Consent_Without_Prior_Yes"
    )
    ehr_reconsent_timestamp = ibis.cases(
        (set_ehr_reconsent_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.EHR_Reconsent_Date_Time__c"],
    ).name("EHR_Reconsent_Date_Time__c")

    set_primary_consent_update_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Primary_Consent_Update_Completion"
    )
    primary_consent_update_timestamp = ibis.cases(
        (set_primary_consent_update_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Update_to_Primary_Consent_Completed__c"],
    ).name("Update_to_Primary_Consent_Completed__c")

    set_basics_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target == "FlowRecordUpdate.Basics_Completion"
    )
    basics_completion_timestamp = ibis.cases(
        (set_basics_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Basics_Date_Time__c"],
    ).name("Basics_Date_Time__c")

    set_overall_health_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Overall_Health_Completion"
    )
    overall_health_completion_timestamp = ibis.cases(
        (set_overall_health_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Overall_Health_Date_Time__c"],
    ).name("Overall_Health_Date_Time__c")

    set_lifestyle_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Lifestyle_Completion"
    )
    lifestyle_completion_timestamp = ibis.cases(
        (set_lifestyle_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Lifestyle_Date_Time__c"],
    ).name("Lifestyle_Date_Time__c")

    set_personal_and_family_history_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Personal_And_Family_History_Completion"
    )
    personal_and_family_history_completion_timestamp = ibis.cases(
        (
            set_personal_and_family_history_completion_timestamp,
            Record.Completion_Status_Timestamp__c,
        ),
        else_=Record["Participant__r.Account.Personal_and_Family_History_Complete__c"],
    ).name("Personal_and_Family_History_Complete__c")

    set_healthcare_access_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Healthcare_Access_Completion"
    )
    healthcare_access_completion_timestamp = ibis.cases(
        (set_healthcare_access_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.HC_Access_Date_Time__c"],
    ).name("HC_Access_Date_Time__c")

    set_life_functioning_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Life_Functioning_Completion"
    )
    life_functioning_completion_timestamp = ibis.cases(
        (set_life_functioning_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Life_Functioning_Date_Time__c"],
    ).name("Life_Functioning_Date_Time__c")

    set_first_remote_physical_measurement_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.First_Remote_Physical_Measurement"
    )
    first_remote_physical_measurement_timestamp = ibis.cases(
        (
            set_first_remote_physical_measurement_timestamp,
            Record[
                "FlowRecordLookup.First_Remote_Physical_Measurement.Completion_Status_Timestamp__c"
            ],
        ),
        else_=Record["Participant__r.Account.First_Physical_Measurement_Date_Time__c"],
    ).name("First_Physical_Measurement_Date_Time__c")

    set_latest_processed_remote_physical_measurement_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordLookup.First_Remote_Physical_Measurement"
    )
    latest_processed_remote_physical_measurement_timestamp = ibis.cases(
        (
            set_latest_processed_remote_physical_measurement_timestamp,
            Record.Completion_Status_Timestamp__c,
        ),
        else_=Record["Participant__r.Account.Last_Physical_Measurement_Date_Time__c"],
    ).name("Last_Physical_Measurement_Date_Time__c")

    set_emotional_health_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Emotional_Health_Completion"
    )
    emotional_health_completion_timestamp = ibis.cases(
        (set_emotional_health_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.EH_Date_Time__c"],
    ).name("EH_Date_Time__c")

    set_behavioral_health_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Behavioral_Health_Completion"
    )
    behavioral_health_completion_timestamp = ibis.cases(
        (set_behavioral_health_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Behavioral_Health_Completion__c"],
    ).name("Behavioral_Health_Completion__c")

    set_environmental_exposures_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Environmental_Exposures_Completion"
    )
    environmental_exposures_completion_timestamp = ibis.cases(
        (set_environmental_exposures_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Environmental_Exposures_Date_Time__c"],
    ).name("Environmental_Exposures_Date_Time__c")

    set_social_determinants_completion_timestamp = (
        Record.FlowDecision_Survey_Completion_Route_target
        == "FlowRecordUpdate.Social_Determinants_Completion"
    )
    social_determinants_completion_timestamp = ibis.cases(
        (set_social_determinants_completion_timestamp, Record.Completion_Status_Timestamp__c),
        else_=Record["Participant__r.Account.Social_Determinants_of_Health_Completion__c"],
    ).name("Social_Determinants_of_Health_Completion__c")

    return (
        age_at_flow_execution,
        california_signature_timestamp,
        earliest_primary_consent_report_timestamp,
        latest_primary_consent_report_timestamp,
        ehr_consent_timestamp,
        ehr_reconsent_timestamp,
        primary_consent_update_timestamp,
        basics_completion_timestamp,
        overall_health_completion_timestamp,
        lifestyle_completion_timestamp,
        personal_and_family_history_completion_timestamp,
        healthcare_access_completion_timestamp,
        life_functioning_completion_timestamp,
        first_remote_physical_measurement_timestamp,
        latest_processed_remote_physical_measurement_timestamp,
        emotional_health_completion_timestamp,
        behavioral_health_completion_timestamp,
        environmental_exposures_completion_timestamp,
        social_determinants_completion_timestamp,
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
    """Select expected Account AFTER values and available Flow routing evidence.

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
    evidence = [
        "FlowDecision_Survey_Completion_Route_target",
        "FlowDecision_Primary_Consent_Account_Update_target",
        "FlowDecision_EHR_Consent_Account_Update_target",
        "FlowDecision_Assent_Account_Update_target",
        "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
    ]
    expressions = {field.get_name(): field for field in fields}
    if "CABOR_Completion_Date__c" in expressions:
        permission_route = (
            Record.FlowDecision_Survey_Completion_Route_target
            == "FlowRecordLookup.Pediatric_Permission_For_Assent"
        )
        expressions["CABOR_Completion_Date__c_is_deterministic"] = ~permission_route.fill_null(
            False
        ) | (Record["FlowRecordLookup.Pediatric_Permission_For_Assent.match_count"] <= 1)
    return Record.select(
        Record.Id.name("Record.Id"),
        Record["Participant__r.Account.Id"].name("Account.Id"),
        Record.Participant__c,
        Record.Survey_Index_Number__c,
        *[Record[column] for column in evidence if column in Record.columns],
        **expressions,
    )


def survey_rollup_expressions(Record: ir.Table) -> dict[str, ir.Value]:
    """Compose SUM(CASE WHEN predicate THEN 1 ELSE 0 END) for each rollup."""
    return {indicator.get_name(): indicator.sum() for indicator in survey_rollup_indicators(Record)}


def expected_survey_rollups(Account: ir.Table, Survey_Result__c: ir.Table) -> ir.Table:
    """Compose expected rollups at ONE ROW PER PERSON ACCOUNT, a separate grain.

    Lineage: Account.PersonContactId -> Survey_Result__c.Participant__c -> the
    conditional aggregates in survey_rollup_expressions(). A left join retains
    person Accounts without children and CASE ELSE 0 gives each count zero.
    Inputs must be complete current snapshots, with deleted survey rows excluded
    upstream. This is a snapshot aggregation, independent of the per-event Flow
    projection; no arbitrary event is selected to consolidate Account state.
    """
    Account = Account.filter(Account.IsPersonAccount).select("Id", "PersonContactId")
    Survey_Result__c = Survey_Result__c.select(
        "Participant__c",
        "Completion_Status__c",
        "Survey_Index_Number__c",
        "Consent_Status__c",
        "Consent_Revoked__c",
    )
    Record = Account.left_join(
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
    return Record.group_by("Account.Id", "PersonContactId").aggregate(
        **survey_rollup_expressions(Record)
    )


def to_sqlglot(expression: ir.Table) -> exp.Query:
    """Compile the completed Ibis query to Athena's AST, then annotate projections.

    All Ibis composition happens first. Stable output aliases connect the final
    SELECT list to authoritative lineage. Branch provenance is nested metadata;
    compiler-generated WHEN positions and table aliases are never used as keys.

    Unknown/custom projected fields are left unannotated. The query-level record
    lists annotated and unannotated outputs. This helper returns the AST: render
    it with query.sql(dialect="athena"), rather than recompiling the Ibis table.
    Native AST copy()/dump()/load() retain the annotations. SQL text does not.
    """
    from ibis.backends.sql.compilers.athena import compiler

    query = compiler.to_sqlglot(expression)
    # Ibis can emit tuple-valued window arguments. SQLGlot's serializer expects
    # list containers for AST children; normalize them without rewriting the SQL.
    for node in query.walk():
        for key, value in list(node.args.items()):
            if isinstance(value, tuple):
                node.set(key, list(value))
    annotated = []
    unannotated = []
    sources = []
    for projection in query.selects:
        name = projection.alias_or_name
        lineage = PROJECTION_LINEAGE.get(name)
        if lineage is None:
            unannotated.append(name)
            continue
        metadata = deepcopy(lineage)
        projection.meta["ppsc"] = metadata
        original_sources = metadata.get("source_entities", [])
        sources.extend(original_sources)
        comment = metadata["description"]
        if original_sources:
            comment += "; source: " + ", ".join(original_sources)
        projection.add_comments([comment])
        annotated.append(name)
    query.meta["ppsc"] = {
        "entity_type": "ExpectedValuesQuery",
        "dialect": "athena",
        "annotated_fields": annotated,
        "unannotated_fields": unannotated,
        "source_entities": list(dict.fromkeys(sources)),
    }
    return query
