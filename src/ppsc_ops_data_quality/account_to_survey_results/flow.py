"""Reviewed native Ibis builders for QA2 Flow 301SL00000dpJqKYAU.

The saved Flow is evidence, not an executable input. Changes to its selected
semantics require reviewing these functions and the independent acceptance cases.
"""

from collections.abc import Callable

import ibis
import ibis.expr.types as ir

from ppsc_ops_data_quality.core.projection import conditional_values

from .metadata import metadata_request

FLOW_FIELDS = metadata_request().fields

PRIMARY = "FlowRecordLookup.Earliest_Other_Yes_Primary_Consent"
EHR = "FlowRecordLookup.Earliest_Other_Yes_EHR_Consent"
PERMISSION = "FlowRecordLookup.Pediatric_Permission_For_Assent"
PHYSICAL = "FlowRecordLookup.First_Remote_Physical_Measurement"
AGE = "FlowFormula_Age_At_Execution"
BEFORE = "Participant__r.Account."
ROW = "__ppsc_flow_row"


def eligibility(record: ir.Table) -> ir.BooleanValue:
    """Observable guard; transition/exemption/settlement remain caller policy."""
    return record.Completion_Status__c == "Complete"


def _routes(record: ir.Table) -> dict[str, ir.BooleanValue]:
    """Survey_Index's ordered outcomes; native scalar comparisons treat NULL as false."""
    index = record.Survey_Index_Number__c
    yes = (record.Consent_Status__c == "Yes").fill_null(False)
    tests = {
        "primary": index.isin(("1001", "1002")).fill_null(False) & yes,
        "ehr": index.isin(("1003", "1004")).fill_null(False) & yes,
        "update": (index == "1005").fill_null(False),
        "assent": (index == "1008").fill_null(False)
        & record.Consent_Status__c.isin(("Yes", "N/A")).fill_null(False),
        "basics": index.isin(("2001", "2002")).fill_null(False),
        "health": index.isin(("2003", "2004")).fill_null(False),
        "lifestyle": (index == "2005").fill_null(False),
        "family": (index == "2006").fill_null(False),
        "access": (index == "2007").fill_null(False),
        "life": (index == "2008").fill_null(False),
        "physical": (index == "2009").fill_null(False),
        "emotional": (index == "2010").fill_null(False),
        "behavioral": (index == "2011").fill_null(False),
        "environment": (index == "2012").fill_null(False),
        "social": (index == "2013").fill_null(False),
    }
    previous = ibis.literal(False)
    result = {}
    for name, test in tests.items():
        result[name] = eligibility(record).fill_null(False) & ~previous & test
        previous = previous | test
    return result


def _first_lookup(
    record: ir.Table,
    candidates: ir.Table,
    *,
    alias: str,
    route: str,
    predicate: Callable[[ir.Table, ir.Table], ir.BooleanValue],
    value_field: str,
    ordered: bool,
) -> ir.Table:
    """Retain each input row and expose ambiguity without inventing a tiebreaker.

    The private identity distinguishes duplicate triggering events. A tied sort
    value is itself deterministic; unsorted payloads remain NULL when ambiguous.
    Id remains existence evidence even when the selected identity is ambiguous.
    """
    marker, rank = "__ppsc_match", "__ppsc_rank"
    if {marker, rank} & (set(record.columns) | set(candidates.columns)):
        raise ValueError("Reserved lookup column collision")
    candidate = candidates.alias(alias).mutate(**{marker: ibis.literal(1)})
    fields = sorted({"Id", value_field})
    joined = record.left_join(candidate, [predicate(record, candidate), _routes(record)[route]])
    joined = joined.select(
        record,
        **{f"{alias}.{field}": candidate[field] for field in fields},
        **{marker: candidate[marker]},
    )
    window = ibis.window(group_by=joined[ROW])
    count = joined[marker].sum().over(window).fill_null(0)
    value = joined[f"{alias}.{value_field}"]
    if ordered:
        ranking = ibis.window(group_by=joined[ROW], order_by=value.asc(nulls_first=True))
        ties = joined[marker].sum().over(ibis.window(group_by=[joined[ROW], value])).fill_null(0)
    else:
        ranking, ties = window, count
    additions = {f"{alias}.match_count": count, rank: ibis.row_number().over(ranking)}
    for field in fields:
        if ordered and field == value_field:
            continue
        known = ties <= 1
        additions[f"__known.{alias}.{field}"] = known
        if field != "Id":
            additions[f"{alias}.{field}"] = known.ifelse(value, ibis.null().cast(value.type()))
    ranked = joined.mutate(**additions)
    return ranked.filter(ranked[rank] == 0).drop(marker, rank)


def add_flow_context(
    record: ir.Table, surveys: ir.Table, *, flow_run_date: ir.DateValue
) -> ir.Table:
    """Bind the four selected native lookups and the explicit execution-date formula."""
    if ROW in record.columns:
        raise ValueError(f"Reserved compiler column: {ROW}")
    if not isinstance(flow_run_date, ir.DateValue):
        raise ValueError("flow_run_date must be an Ibis DATE expression")
    record = record.mutate(**{ROW: ibis.row_number().over(ibis.window())})
    for alias, route, indexes in (
        (PRIMARY, "primary", ("1001", "1002")),
        (EHR, "ehr", ("1003", "1004")),
        (PERMISSION, "assent", ("1007",)),
    ):
        record = _first_lookup(
            record,
            surveys,
            alias=alias,
            route=route,
            predicate=lambda r, s, indexes=indexes: (
                s.Survey_Index_Number__c.isin(indexes).fill_null(False)
                & (s.Consent_Status__c == "Yes").fill_null(False)
                & (s.Participant__c == r.Participant__c).fill_null(False)
                & (s.Id != r.Id).fill_null(False)
            ),
            value_field="California_Signature__c"
            if alias == PERMISSION
            else "Consent_Status_Timestamp__c",
            ordered=alias != PERMISSION,
        )
    record = _first_lookup(
        record,
        surveys,
        alias=PHYSICAL,
        route="physical",
        predicate=lambda r, s: (
            (s.Survey_Index_Number__c == "2009").fill_null(False)
            & (s.Participant__c == r.Participant__c).fill_null(False)
        ),
        value_field="Completion_Status_Timestamp__c",
        ordered=True,
    )
    return (
        record.mutate(
            **{
                AGE: (
                    flow_run_date.delta(record["Participant__r.Birthdate"], unit="day") / 365.25
                ).floor()
            }
        )
        .drop(ROW)
        .alias("Flow_Context")
    )


def flow_assignments(record: ir.Table) -> dict[str, ir.Value]:
    """Return expected values, assignment status and independent determinism columns."""
    routes = _routes(record)
    completion = record.Completion_Status_Timestamp__c
    before = {field: record[BEFORE + field] for field in FLOW_FIELDS}
    common_consent = {
        "Age_at_Time_of_Consent__pc": record[AGE],
        "Latest_Primary_Consent_Date_for_Report__c": completion,
    }
    permission_exists = record[f"{PERMISSION}.Id"].notnull()
    earliest_exists = before["Earliest_Primary_Consent_Date_for_Report__c"].notnull()
    assignments = [
        (
            routes["primary"] & record[f"{PRIMARY}.Id"].notnull(),
            {
                **common_consent,
                "CABOR_Completion_Date__c": record.California_Signature__c,
            },
        ),
        (
            routes["primary"] & record[f"{PRIMARY}.Id"].isnull(),
            {
                **common_consent,
                "CABOR_Completion_Date__c": record.California_Signature__c,
                "Earliest_Primary_Consent_Date_for_Report__c": completion,
            },
        ),
        (routes["ehr"] & record[f"{EHR}.Id"].notnull(), {"EHR_Reconsent_Date_Time__c": completion}),
        (routes["ehr"] & record[f"{EHR}.Id"].isnull(), {"EHR_Consent_Date_Time__c": completion}),
        (
            routes["assent"] & permission_exists & earliest_exists,
            {
                **common_consent,
                "CABOR_Completion_Date__c": record[f"{PERMISSION}.California_Signature__c"],
            },
        ),
        (
            routes["assent"] & ~(permission_exists & earliest_exists),
            {
                **common_consent,
                "CABOR_Completion_Date__c": record[f"{PERMISSION}.California_Signature__c"],
                "Earliest_Primary_Consent_Date_for_Report__c": completion,
            },
        ),
        (
            routes["physical"],
            {
                "First_Physical_Measurement_Date_Time__c": record[
                    f"{PHYSICAL}.Completion_Status_Timestamp__c"
                ],
                "Last_Physical_Measurement_Date_Time__c": completion,
            },
        ),
    ]
    for route, field in (
        ("update", "Update_to_Primary_Consent_Completed__c"),
        ("basics", "Basics_Date_Time__c"),
        ("health", "Overall_Health_Date_Time__c"),
        ("lifestyle", "Lifestyle_Date_Time__c"),
        ("family", "Personal_and_Family_History_Complete__c"),
        ("access", "HC_Access_Date_Time__c"),
        ("life", "Life_Functioning_Date_Time__c"),
        ("emotional", "EH_Date_Time__c"),
        ("behavioral", "Behavioral_Health_Completion__c"),
        ("environment", "Environmental_Exposures_Date_Time__c"),
        ("social", "Social_Determinants_of_Health_Completion__c"),
    ):
        assignments.append((routes[route], {field: completion}))
    assignments = [
        (guard, {field: value.cast(before[field].type()) for field, value in values.items()})
        for guard, values in assignments
    ]
    expected = conditional_values(before, assignments)
    result = {f"expected__{field}": expected[field] for field in FLOW_FIELDS}
    for field in FLOW_FIELDS:
        guards = [guard for guard, values in assignments if field in values]
        assigned = ibis.literal(False)
        for guard in guards:
            assigned = assigned | guard
        result[f"expected__{field}__assigned"] = ibis.cases(
            (~eligibility(record), ibis.literal(False)),
            (eligibility(record).notnull(), assigned),
            else_=ibis.null().cast("boolean"),
        )
        result[f"expected__{field}__deterministic"] = (
            ibis.cases(
                (routes["assent"], record[f"__known.{PERMISSION}.California_Signature__c"]),
                else_=True,
            ).fill_null(False)
            if field == "CABOR_Completion_Date__c"
            else ibis.literal(True)
        )
    return result
