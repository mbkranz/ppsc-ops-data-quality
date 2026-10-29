"""Explicit account_to_survey_results queries operations."""

from __future__ import annotations

import operator
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, date, datetime, time
from functools import reduce
from hashlib import sha256
from pathlib import Path
from re import fullmatch

import ibis
import ibis.expr.types as ir
from pydantic import BaseModel, ConfigDict, Field, model_validator
from salesforce.entities.flows import to_sqlglot as flow_to_sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope

from ppsc_ops_data_quality.io import RelationLocation, load_inputs
from ppsc_ops_data_quality.runtime import prepare_query

ROLLUP_FIELD_LINEAGE = {
    "Account.EHR_Authorized__pc": {
        "source_entity": "Account.EHR_Authorized__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 442,
        "expression": "ehr_authorized_indicator",
        "branches": ["count_completed_ehr_authorization"],
        "entity_type": "AccountRollup",
    },
    "Account.Count_of_Completed_EHR_Auth__pc": {
        "source_entity": "Account.Count_of_Completed_EHR_Auth__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 465,
        "expression": "count_of_completed_ehr_auth_indicator",
        "branches": ["count_completed_ehr_authorization"],
        "entity_type": "AccountRollup",
    },
    "Account.Count_of_Completed_Primary_Consent__pc": {
        "source_entity": "Account.Count_of_Completed_Primary_Consent__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 466,
        "expression": "count_of_completed_primary_consent_indicator",
        "branches": ["count_completed_primary_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.Count_of_Completed_Reconsent__pc": {
        "source_entity": "Account.Count_of_Completed_Reconsent__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 467,
        "expression": "count_of_completed_reconsent_indicator",
        "branches": ["count_completed_primary_consent_updates"],
        "entity_type": "AccountRollup",
    },
    "Account.PPI_2_Completion_Count__pc": {
        "source_entity": "Account.PPI_2_Completion_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 468,
        "expression": "ppi_2_completion_count_indicator",
        "branches": ["count_completed_lifestyle_surveys"],
        "entity_type": "AccountRollup",
    },
    "Account.PPI_3_Completion_Count__pc": {
        "source_entity": "Account.PPI_3_Completion_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 469,
        "expression": "ppi_3_completion_count_indicator",
        "branches": ["count_completed_overall_health_surveys"],
        "entity_type": "AccountRollup",
    },
    "Account.EHR_Consent_Active__pc": {
        "source_entity": "Account.EHR_Consent_Active__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 443,
        "expression": "ehr_consent_active_indicator",
        "branches": ["count_active_ehr_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.EHR_Consent_Declined__pc": {
        "source_entity": "Account.EHR_Consent_Declined__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 540,
        "expression": "ehr_consent_declined_indicator",
        "branches": ["count_declined_ehr_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.PP1_Basics_Survey_Complete__pc": {
        "source_entity": "Account.PP1_Basics_Survey_Complete__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 541,
        "expression": "pp1_basics_survey_complete_indicator",
        "branches": ["count_completed_unrevoked_basics_surveys"],
        "entity_type": "AccountRollup",
    },
    "Account.Re_Consent_Declined__pc": {
        "source_entity": "Account.Re_Consent_Declined__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 542,
        "expression": "re_consent_declined_indicator",
        "branches": ["count_declined_primary_consent_updates"],
        "entity_type": "AccountRollup",
    },
    "Account.Re_consent_Active__pc": {
        "source_entity": "Account.Re_consent_Active__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 543,
        "expression": "re_consent_active_indicator",
        "branches": ["count_active_primary_consent_updates"],
        "entity_type": "AccountRollup",
    },
    "Account.Primary_Consent_Declined__pc": {
        "source_entity": "Account.Primary_Consent_Declined__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 555,
        "expression": "primary_consent_declined_indicator",
        "branches": ["count_declined_primary_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.EHR_Consent_Ever__pc": {
        "source_entity": "Account.EHR_Consent_Ever__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 562,
        "expression": "ehr_consent_ever_indicator",
        "branches": ["count_ever_authorized_ehr_consent"],
        "entity_type": "AccountRollup",
    },
    "Account.Assent_Completion_Count__pc": {
        "source_entity": "Account.Assent_Completion_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 594,
        "expression": "assent_completion_count_indicator",
        "branches": ["count_completed_active_assent"],
        "entity_type": "AccountRollup",
    },
    "Account.Pediatric_Permission_Completion_Count__pc": {
        "source_entity": "Account.Pediatric_Permission_Completion_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 595,
        "expression": "pediatric_permission_completion_count_indicator",
        "branches": ["count_completed_active_pediatric_permission"],
        "entity_type": "AccountRollup",
    },
    "Account.X0_6_Peds_Permission_Count__pc": {
        "source_entity": "Account.X0_6_Peds_Permission_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 622,
        "expression": "x0_6_peds_permission_count_indicator",
        "branches": ["count_active_permission_ages_zero_to_six"],
        "entity_type": "AccountRollup",
    },
    "Account.X0_6_Peds_Permission_Declined_Count__pc": {
        "source_entity": "Account.X0_6_Peds_Permission_Declined_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 623,
        "expression": "x0_6_peds_permission_declined_count_indicator",
        "branches": ["count_declined_permission_ages_zero_to_six"],
        "entity_type": "AccountRollup",
    },
    "Account.X0_6_Peds_Permission_Revoked_Count__pc": {
        "source_entity": "Account.X0_6_Peds_Permission_Revoked_Count__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 624,
        "expression": "x0_6_peds_permission_revoked_count_indicator",
        "branches": ["count_revoked_permission_ages_zero_to_six"],
        "entity_type": "AccountRollup",
    },
    "Account.EHR_Pediatric_Complete__pc": {
        "source_entity": "Account.EHR_Pediatric_Complete__pc",
        "workbook_tab": "datamodel-Fields",
        "workbook_row": 626,
        "expression": "ehr_pediatric_complete_indicator",
        "branches": ["count_completed_active_pediatric_ehr_consent"],
        "entity_type": "AccountRollup",
    },
}

BRANCH_LINEAGE = {
    "count_completed_ehr_authorization": {
        "output_fields": ["Account.EHR_Authorized__pc", "Account.Count_of_Completed_EHR_Auth__pc"],
        "source_entities": [
            "Account.EHR_Authorized__pc",
            "Account.Count_of_Completed_EHR_Auth__pc",
        ],
        "workbook_rows": [442, 465],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_primary_consent": {
        "output_fields": ["Account.Count_of_Completed_Primary_Consent__pc"],
        "source_entities": ["Account.Count_of_Completed_Primary_Consent__pc"],
        "workbook_rows": [466],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_primary_consent_updates": {
        "output_fields": ["Account.Count_of_Completed_Reconsent__pc"],
        "source_entities": ["Account.Count_of_Completed_Reconsent__pc"],
        "workbook_rows": [467],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_lifestyle_surveys": {
        "output_fields": ["Account.PPI_2_Completion_Count__pc"],
        "source_entities": ["Account.PPI_2_Completion_Count__pc"],
        "workbook_rows": [468],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_overall_health_surveys": {
        "output_fields": ["Account.PPI_3_Completion_Count__pc"],
        "source_entities": ["Account.PPI_3_Completion_Count__pc"],
        "workbook_rows": [469],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_active_ehr_consent": {
        "output_fields": ["Account.EHR_Consent_Active__pc"],
        "source_entities": ["Account.EHR_Consent_Active__pc"],
        "workbook_rows": [443],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_declined_ehr_consent": {
        "output_fields": ["Account.EHR_Consent_Declined__pc"],
        "source_entities": ["Account.EHR_Consent_Declined__pc"],
        "workbook_rows": [540],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_unrevoked_basics_surveys": {
        "output_fields": ["Account.PP1_Basics_Survey_Complete__pc"],
        "source_entities": ["Account.PP1_Basics_Survey_Complete__pc"],
        "workbook_rows": [541],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_declined_primary_consent_updates": {
        "output_fields": ["Account.Re_Consent_Declined__pc"],
        "source_entities": ["Account.Re_Consent_Declined__pc"],
        "workbook_rows": [542],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_active_primary_consent_updates": {
        "output_fields": ["Account.Re_consent_Active__pc"],
        "source_entities": ["Account.Re_consent_Active__pc"],
        "workbook_rows": [543],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_declined_primary_consent": {
        "output_fields": ["Account.Primary_Consent_Declined__pc"],
        "source_entities": ["Account.Primary_Consent_Declined__pc"],
        "workbook_rows": [555],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_ever_authorized_ehr_consent": {
        "output_fields": ["Account.EHR_Consent_Ever__pc"],
        "source_entities": ["Account.EHR_Consent_Ever__pc"],
        "workbook_rows": [562],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_active_assent": {
        "output_fields": ["Account.Assent_Completion_Count__pc"],
        "source_entities": ["Account.Assent_Completion_Count__pc"],
        "workbook_rows": [594],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_active_pediatric_permission": {
        "output_fields": ["Account.Pediatric_Permission_Completion_Count__pc"],
        "source_entities": ["Account.Pediatric_Permission_Completion_Count__pc"],
        "workbook_rows": [595],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_active_permission_ages_zero_to_six": {
        "output_fields": ["Account.X0_6_Peds_Permission_Count__pc"],
        "source_entities": ["Account.X0_6_Peds_Permission_Count__pc"],
        "workbook_rows": [622],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_declined_permission_ages_zero_to_six": {
        "output_fields": ["Account.X0_6_Peds_Permission_Declined_Count__pc"],
        "source_entities": ["Account.X0_6_Peds_Permission_Declined_Count__pc"],
        "workbook_rows": [623],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_revoked_permission_ages_zero_to_six": {
        "output_fields": ["Account.X0_6_Peds_Permission_Revoked_Count__pc"],
        "source_entities": ["Account.X0_6_Peds_Permission_Revoked_Count__pc"],
        "workbook_rows": [624],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
    "count_completed_active_pediatric_ehr_consent": {
        "output_fields": ["Account.EHR_Pediatric_Complete__pc"],
        "source_entities": ["Account.EHR_Pediatric_Complete__pc"],
        "workbook_rows": [626],
        "entity_type": "AccountRollup",
        "workbook_tab": "datamodel-Fields",
    },
}

ROLLUP_SOURCE_NOTES = (
    "\n"
    "Comma-separated metadata indexes are interpreted as IN lists. Row 555 repeats\n"
    "1005 and omits 1001; the distinct set 1005/1002 is preserved, pending confirmation\n"
    "against raw rollup metadata. The three 0-6 permission counters deliberately omit\n"
    "Complete when the source does. Primary_Consent_Active__pc is omitted because the\n"
    "exported LIKE predicate is corrupted. Sample and clinical-measurement rollups\n"
    "require other child objects. Formula fields with blank bodies cannot be derived.\n"
)


def dataset_binding(inputs: dict, dataset_id: str) -> dict:
    if dataset_id not in inputs["tables"]:
        raise ValueError(f"Unknown APMP dataset selection: {dataset_id}")
    return inputs["tables"][dataset_id]


def physical_schema(inputs: dict, dataset_id: str) -> ibis.Schema:
    table = dataset_binding(inputs, dataset_id)
    schema = ibis.schema(table["fields"])
    columns = table["columns"]
    for names in (schema.names, tuple(columns.values())):
        if not names or len({name.casefold() for name in names}) != len(names):
            raise ValueError(f"Duplicate/case-colliding generated schema fields: {dataset_id}")
    if set(columns) != set(schema.names):
        raise ValueError(f"Generated schema/mapping fields disagree: {dataset_id}")
    return schema


def logical_schema(inputs: dict, dataset_id: str) -> ibis.Schema:
    table = dataset_binding(inputs, dataset_id)
    schema = physical_schema(inputs, dataset_id)
    return ibis.schema(
        {logical: schema[physical] for physical, logical in table["columns"].items()}
    )


def source_relation(
    inputs: dict, dataset_id: str, *, location: RelationLocation | None = None
) -> ir.Table:
    table = dataset_binding(inputs, dataset_id)
    selected = location or RelationLocation(
        **{name: table[name] for name in ("catalog", "database", "relation")}
    )
    physical = ibis.table(
        physical_schema(inputs, dataset_id),
        name=selected.relation,
        database=selected.database,
        catalog=selected.catalog,
    )
    return physical.select(
        **{logical: physical[name] for name, logical in table["columns"].items()}
    )


def history_tables(
    *,
    inputs: dict,
    locations: Mapping[str, RelationLocation] | None = None,
) -> dict[str, ir.Table]:
    """Project real physical names through the supplied reviewed or provisional input set.

    No schema, database or relation is invented here. Offline examples deliberately
    supply their pinned fixture bundle. Runtime separately verifies the exact
    selection, live catalog compatibility and chosen data versions before GX.
    """
    bindings = inputs["tables"]
    if locations is not None and set(locations) != set(bindings):
        raise ValueError("Locations must match the selected APMP dataset IDs")
    return {
        binding["native_object"]: source_relation(
            inputs, dataset_id, location=locations[dataset_id] if locations is not None else None
        )
        for dataset_id, binding in bindings.items()
    }


def snapshot(
    history: ir.Table,
    *,
    as_of: date | datetime | None = None,
    valid_from: str = "valid_from",
    valid_to: str = "valid_to",
    is_current: str = "is_current",
) -> ir.Table:
    """Return the SCD2 snapshot as a composable, schema-preserving Ibis table.

    Lineage: translates the prior state_predicate() into Ibis without changing
    its half-open interval semantics. as_of=None selects is_current == TRUE;
    otherwise valid_from <= as_of AND (valid_to > as_of OR valid_to IS NULL).
    All source columns and all matching versions survive. NULL bounds/flags
    follow SQL's three-valued logic. A NULL valid_from never matches as_of.

    Date history requires a date. Timestamp history accepts a datetime, or a
    date interpreted at midnight in the column's time zone. Naive timestamps
    require naive datetimes; zoned timestamps require aware datetimes. Values
    are never truncated to dates. Column names can be mapped explicitly.

    This is business-effective state, not an immutable materialized snapshot.
    Late corrections to history can change results even with a fixed as_of.
    Deletion/tombstone semantics remain those of the history producer.
    """
    schema = history.schema()
    if as_of is None:
        if is_current not in schema or not schema[is_current].is_boolean():
            raise ValueError(f"Current history requires boolean {is_current!r}")
        query = history.filter(history[is_current] == True)
    else:
        if not isinstance(as_of, date):
            raise TypeError("as_of must be a date, datetime, or None")
        if valid_from not in schema or valid_to not in schema:
            raise ValueError(
                "History requires valid_from and valid_to columns (or explicit mappings)"
            )
        dtype = schema[valid_from]
        if dtype != schema[valid_to] or not (dtype.is_date() or dtype.is_timestamp()):
            raise ValueError("Validity bounds must have identical date or timestamp types")
        if dtype.is_date():
            if isinstance(as_of, datetime):
                raise TypeError("Date history requires date as_of; refusing to discard time")
            point = ibis.literal(as_of, type=dtype)
        else:
            if not isinstance(as_of, datetime):
                # Ibis interprets a naive literal in the requested column time zone.
                as_of = datetime.combine(as_of, time.min)
                if dtype.timezone:
                    from zoneinfo import ZoneInfo

                    as_of = as_of.replace(tzinfo=ZoneInfo(dtype.timezone))
            aware = as_of.tzinfo is not None and as_of.utcoffset() is not None
            if bool(dtype.timezone) != aware:
                raise ValueError("as_of timezone awareness must match the timestamp columns")
            if aware:
                as_of = as_of.astimezone(UTC)
            point = ibis.literal(as_of, type=dtype)
        query = history.filter(
            (history[valid_from] <= point)
            & ((history[valid_to] > point) | history[valid_to].isnull())
        )
    return query


class KeyBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    expected: str = Field(min_length=1)
    observed: str = Field(min_length=1)


class ValueBinding(KeyBinding):
    """Evidence names refer exclusively to the independent expected relation.

    Omit evidence only when the producer can establish it without a column.
    Assignment false is valid provenance; assignment NULL is incomplete evidence.
    Required and must-be-null are independent predicates, never complements.
    """

    deterministic: str | None = Field(default=None, min_length=1)
    assigned: str | None = Field(default=None, min_length=1)
    required: str | None = Field(default=None, min_length=1)
    must_be_null: str | None = Field(default=None, min_length=1)


class ComparisonSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    keys: tuple[KeyBinding, ...] = Field(min_length=1)
    values: tuple[ValueBinding, ...] = Field(min_length=1)
    scope: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_bindings(self) -> ComparisonSpec:
        for bindings in (self.keys, self.values):
            if len({item.name for item in bindings}) != len(bindings):
                raise ValueError("Binding names must be unique within each role")
        for side in ("expected", "observed"):
            if len({getattr(item, side) for item in self.keys}) != len(self.keys):
                raise ValueError("Composite keys must bind distinct source columns")
        outputs = [
            f"{side}.key.{key.name}" for key in self.keys for side in ("expected", "observed")
        ]
        for value in self.values:
            outputs.extend([f"expected.{value.name}", f"observed.{value.name}"])
            outputs.extend(
                f"expected.{value.name}__{role}"
                for role in ("deterministic", "assigned", "required", "must_be_null")
                if getattr(value, role) is not None
            )
        if len(set(outputs)) != len(outputs):
            raise ValueError("Comparison output names collide")
        return self


def _all(values):
    return reduce(operator.and_, values, ibis.literal(True))


def compare_values(Expected: ir.Table, Observed: ir.Table, spec: ComparisonSpec) -> ir.Table:
    """Full reconciliation at an explicit, possibly composite, comparison grain.

    All input rows survive. Missing keys, duplicate keys, unmatched records and
    join fanout invalidate equality rather than being filtered or deduplicated.
    Windows partition by the entire typed key, without concatenating values.
    Callers bind source and observation snapshots and any approved casts upstream.
    """
    for key in spec.keys:
        if Expected[key.expected].type().copy(nullable=True) != Observed[key.observed].type().copy(
            nullable=True
        ):
            raise ValueError(f"Comparison key types must match: {key.name}")
    for value in spec.values:
        if Expected[value.expected].type().copy(nullable=True) != Observed[
            value.observed
        ].type().copy(nullable=True):
            raise ValueError(
                f"Comparison value types must match; supply an explicit approved cast: {value.name}"
            )
    evidence = {
        column
        for value in spec.values
        for role in ("deterministic", "assigned", "required", "must_be_null")
        if (column := getattr(value, role)) is not None
    }
    for column in evidence | ({spec.scope} if spec.scope else set()):
        if not Expected[column].type().is_boolean():
            raise ValueError(f"Comparison evidence must be boolean: {column}")
    expected_columns = {f"expected.key.{key.name}": Expected[key.expected] for key in spec.keys}
    observed_columns = {f"observed.key.{key.name}": Observed[key.observed] for key in spec.keys}
    for value in spec.values:
        expected_columns[f"expected.{value.name}"] = Expected[value.expected]
        observed_columns[f"observed.{value.name}"] = Observed[value.observed]
        for role in ("deterministic", "assigned", "required", "must_be_null"):
            if (column := getattr(value, role)) is not None:
                expected_columns[f"expected.{value.name}__{role}"] = Expected[column]
    expected_columns.update(
        _expected_present=ibis.literal(True),
        _expected_unique=(
            Expected.count().over(
                ibis.window(group_by=[Expected[key.expected] for key in spec.keys])
            )
            == 1
        ),
        comparison_scope=Expected[spec.scope] if spec.scope else ibis.literal(True),
    )
    observed_columns["_observed_unique"] = (
        Observed.count().over(ibis.window(group_by=[Observed[key.observed] for key in spec.keys]))
        == 1
    )
    Expected = Expected.select(**expected_columns).alias("Expected_Comparison")
    Observed = Observed.select(**observed_columns).alias("Observed_Comparison")
    Joined = Expected.outer_join(
        Observed,
        [
            Expected[f"expected.key.{key.name}"] == Observed[f"observed.key.{key.name}"]
            for key in spec.keys
        ],
    )
    Comparison = Joined.select(Expected, Observed)
    complete = [Comparison._expected_present.notnull()]
    for value in spec.values:
        for role in ("deterministic", "assigned", "required", "must_be_null"):
            if getattr(value, role) is not None:
                column = Comparison[f"expected.{value.name}__{role}"]
                complete.append(column if role == "deterministic" else column.notnull())
    return Comparison.mutate(
        # An unexpected observation is always reconciled, even when expected rows
        # are scoped. A genuinely unknown source scope stays NULL.
        comparison_scope=ibis.ifelse(
            Comparison._expected_present.isnull(), True, Comparison.comparison_scope
        ),
        comparison_keys_are_valid=_all(
            [
                *[
                    Comparison[f"{side}.key.{key.name}"].notnull()
                    for key in spec.keys
                    for side in ("expected", "observed")
                ],
                Comparison._expected_unique,
                Comparison._observed_unique,
            ]
        ).fill_null(False),
        comparison_evidence_is_complete=_all(complete).fill_null(False),
    ).drop("_expected_present", "_expected_unique", "_observed_unique")


def _resolve_final_projection(query: exp.Query) -> exp.Query:
    """Remove a column-only projection over an aggregate without regrouping rows."""
    if not isinstance(query, exp.Select) or any(
        value for key, value in query.args.items() if key not in ("expressions", "from_", "with_")
    ):
        return query
    source = query.args.get("from_")
    if source is None or not isinstance(source.this, exp.Subquery):
        return query
    subquery = source.this
    inner = subquery.this
    if (
        not isinstance(inner, exp.Select)
        or not inner.args.get("group")
        or inner.args.get("with_")
        or inner.args.get("order")
        or inner.args.get("distinct")
        or inner.args.get("having")
        or inner.args.get("qualify")
    ):
        return query
    projections = {projection.alias_or_name: projection for projection in inner.selects}
    resolved = []
    for projection in query.selects:
        column = projection.unalias()
        if (
            not isinstance(column, exp.Column)
            or column.table != subquery.alias
            or column.name not in projections
        ):
            return query
        resolved.append(
            exp.alias_(
                projections[column.name].unalias().copy(), projection.alias_or_name, quoted=True
            )
        )
    # Ibis groups by SELECT ordinals. Resolve them before changing projection order.
    group = inner.args["group"]
    group.set(
        "expressions",
        [
            inner.selects[int(value.this) - 1].unalias().copy()
            if isinstance(value, exp.Literal) and value.is_int
            else value
            for value in group.expressions
        ],
    )
    inner.set("expressions", resolved)
    inner.set("with_", query.args.get("with_"))
    return inner


def _name_relation_aliases(query: exp.Query) -> None:
    """Replace compiler aliases with source names without crossing SQL scopes."""
    scopes = list(traverse_scope(query))
    reserved = {name.casefold() for scope in scopes for name in scope.selected_sources}
    source_names: dict[Scope, str] = {}
    for scope in scopes:
        for alias, (node, source) in list(scope.selected_sources.items()):
            name = node.name if isinstance(node, exp.Table) else source_names.get(source, "Rows")
            source_names.setdefault(scope, name)
            if not fullmatch(r"t\d+", alias):
                continue
            candidate = name
            suffix = 2
            while candidate.casefold() in reserved:
                candidate = f"{name}_{suffix}"
                suffix += 1
            reserved.add(candidate.casefold())
            relation = node if isinstance(node, exp.Table) else node.parent
            if not isinstance(relation, (exp.Table, exp.Subquery)):
                raise ValueError(f"Unsupported SQL relation for alias {alias!r}")
            relation.set("alias", exp.TableAlias(this=exp.to_identifier(candidate, quoted=True)))
            for column in scope.columns:
                if column.table == alias:
                    column.set("table", exp.to_identifier(candidate, quoted=True))
            scope.rename_source(alias, candidate)
            scope.clear_cache()


def to_sqlglot(
    expression: ir.Table,
    *,
    projection_lineage: Mapping[str, Mapping[str, object]] | None = None,
    table_versions: Mapping[tuple[str, str, str], str] | None = None,
) -> exp.Query:
    """Compile the completed Ibis query to Athena's AST, then annotate projections.

    All Ibis composition happens first. Query-local CTEs stay shared inside an explicit derived relation,
    so the result starts with SELECT and never uses a SELECT-* wrapper. A column-only
    projection over an aggregate is folded into its original grouping, exposing
    the conditional aggregate expressions without merging or deduplicating groups.
    Named Ibis relations supply readable SQL
    source aliases; numeric suffixes disambiguate repeated references. Stable
    output aliases connect the final SELECT list to authoritative lineage.
    Branch provenance is nested metadata;
    compiler-generated WHEN positions and table aliases are never used as keys.

    Unknown/custom projected fields are left unannotated. The query-level record
    lists annotated and unannotated outputs. This helper returns the AST: render
    it with query.sql(dialect="athena"), rather than recompiling the Ibis table.
    Native AST copy()/dump()/load() retain the annotations. SQL text does not.
    """
    from ibis.backends.sql.compilers.athena import compiler

    query = (
        expression.copy() if isinstance(expression, exp.Select) else compiler.to_sqlglot(expression)
    )
    if isinstance(expression, ir.Table) and any(p.is_star for p in query.selects):
        query.set("expressions", [exp.column(name, quoted=True) for name in expression.columns])
    # Ibis can emit tuple-valued window arguments. SQLGlot's serializer expects
    # list containers for AST children; normalize them without rewriting the SQL.
    for node in query.walk():
        for key, value in list(node.args.items()):
            if isinstance(value, tuple):
                node.set(key, list(value))
    _name_relation_aliases(query)
    query = _resolve_final_projection(query)
    query = prepare_query(query, table_versions=table_versions)
    if projection_lineage is None:
        return query
    annotated = []
    unannotated = []
    sources = []
    for projection in query.selects:
        name = projection.alias_or_name
        lineage = projection_lineage.get(name)
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
        **query.meta.get("ppsc", {}),
        "entity_type": "ExpectedValuesQuery",
        "dialect": "athena",
        "annotated_fields": annotated,
        "unannotated_fields": unannotated,
        "source_entities": list(dict.fromkeys(sources)),
    }
    return query


FLOW_FIELDS = (
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
        Contact.Id.name("Participant__r.Contact.Id"),
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


def survey_rollup_expressions(Record: ir.Table) -> dict[str, ir.Value]:
    """Compose SUM(CASE WHEN predicate THEN 1 ELSE 0 END) for each rollup."""
    return {indicator.get_name(): indicator.sum() for indicator in survey_rollup_indicators(Record)}


def _survey_rollup_record(Account: ir.Table, Survey_Result__c: ir.Table) -> ir.Table:
    Account = (
        Account.filter(Account.IsPersonAccount)
        .select("Id", "PersonContactId")
        .alias("Person_Account")
    )
    Account = Account.mutate(
        _source_parent_key_is_unique=(
            Account.Id.count().over(ibis.window(group_by=Account.Id)) == 1
        )
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
        Account._source_parent_key_is_unique,
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
    return Record.group_by(
        Id=Record["Account.Id"], PersonContactId=Record.PersonContactId
    ).aggregate(
        source_parent_keys_are_valid=Record._source_parent_key_is_unique.all(),
        **survey_rollup_expressions(Record),
    )


ROLLUP_ACCOUNT_FIELDS = tuple(field.removeprefix("Account.") for field in ROLLUP_FIELD_LINEAGE)


SURVEY_COMPLETION_FLOW_LAUNCH_DATE = date(2024, 12, 16)


def observed_account_query(
    history: Mapping[str, ir.Table], *, fields: tuple[str, ...], as_of: date | datetime | None
) -> ir.Table:
    """Independently observed Account snapshot with canonical field names."""
    return snapshot(history["Account"], as_of=as_of).select("Id", *fields)


def rollup_account_comparison(Expected: ir.Table, Observed: ir.Table) -> ir.Table:
    """Add dotted GX labels only when joining canonical expected/observed rows.

    Expected aggregation is complete before the observation join. Full reconciliation
    preserves missing/extra observations and every duplicate observation occurrence.
    """
    Expected, Observed = Expected.alias("expected"), Observed.alias("observed")
    Joined = Expected.outer_join(Observed, Expected.Id == Observed.Id)
    Comparison = Joined.select(
        Expected.Id.name("validation_record_id"),
        Expected.Id.name("expected.Id"),
        Expected.PersonContactId.name("person_contact_id"),
        Observed.Id.name("observed.Id"),
        Expected.source_parent_keys_are_valid,
        **{f"expected.{field}": Expected[field] for field in ROLLUP_ACCOUNT_FIELDS},
        **{f"observed.{field}": Observed[field] for field in ROLLUP_ACCOUNT_FIELDS},
    )
    return Comparison.mutate(
        comparison_keys_are_valid=(
            Comparison["expected.Id"].notnull()
            & Comparison.person_contact_id.notnull()
            & Comparison["observed.Id"].notnull()
            & Comparison.source_parent_keys_are_valid
            & (
                Comparison["expected.Id"]
                .count()
                .over(ibis.window(group_by=Comparison["expected.Id"]))
                == 1
            )
        )
    )


def rollup_account_query(
    history: Mapping[str, ir.Table], *, as_of: date | datetime | None = None
) -> ir.Table:
    """Compose canonical rollup and observation queries at the GX join boundary."""
    expected = expected_survey_rollups(
        snapshot(history["Account"], as_of=as_of),
        snapshot(history["Survey_Result__c"], as_of=as_of),
    )
    observed = observed_account_query(history, fields=ROLLUP_ACCOUNT_FIELDS, as_of=as_of)
    return rollup_account_comparison(expected, observed)


def metadata_inputs(directory: Path | None = None) -> dict:
    """Explicitly load the selected inputs; default is the documented offline fixture."""
    from importlib.resources import files

    return load_inputs(
        directory
        or Path(str(files("ppsc_ops_data_quality"))) / "account_to_survey_results/metadata"
    )


def metadata_receipt(inputs: dict | None = None) -> dict:
    inputs = metadata_inputs() if inputs is None else inputs
    return {
        key: inputs[key]
        for key in ("source_org", "source_revision", "inputs_sha256", "flow_sha256")
    } | {
        "flow_version_id": inputs["flow"]["Id"],
        "flow_name": inputs["flow"]["FullName"],
        "compiler_commit": "4ce491c3266e052bf1e1f6a70e8f7d2aed86f9f1",
        "compiler_wheel_sha256": "c625b6f4273241ee29bde7b4cdfbcebc9ddf4ab5b0e2caf1840727de4fb67c9b",
        "provisional": any(t["provisional"] for t in inputs["tables"].values()),
        "native_definitions_available": bool(inputs["field_definitions"]),
    }


def projection_lineage(query: exp.Select) -> dict:
    return {
        column.alias_or_name: deepcopy(
            column.meta.get(
                "ppsc",
                {
                    "description": column.alias_or_name,
                    "rule_id": column.alias_or_name,
                    "source_entities": [],
                    "comparison_role": "evidence",
                },
            )
        )
        for column in query.selects
    }


def _col(name, table=None):
    return exp.column(name, table=table, quoted=True)


def _named(value, name):
    return exp.alias_(value, name, quoted=True)


def expected_flow_account_query(
    history: Mapping[str, ir.Table],
    *,
    survey_result_id: str,
    account_before_at: date | datetime,
    execution_at: date | datetime,
    flow_run_date: date,
    eligibility: bool | None,
    inputs: dict,
    simplify: bool = True,
) -> exp.Select:
    """Bind native Flow to BEFORE/execution inputs; expose canonical Account fields.

    Eligibility is an explicit verified trigger fact (None is unknown). Inputs
    may be provisional for offline evaluation; live workflow requires native evidence.
    """
    if not survey_result_id.strip():
        raise ValueError("Select a triggering event identity")
    if isinstance(flow_run_date, datetime) or not isinstance(flow_run_date, date):
        raise ValueError("flow_run_date must be an org-local date")
    if any(not isinstance(v, date) for v in (account_before_at, execution_at)):
        raise TypeError("Bind explicit temporal values")
    try:
        ordered = account_before_at < execution_at
    except TypeError as error:
        raise ValueError("Temporal bindings must use comparable types and time zones") from error
    if not ordered:
        raise ValueError("Require account_before_at < execution_at")
    if eligibility is not None and not isinstance(eligibility, bool):
        raise ValueError("eligibility must be Boolean or unknown")
    native = flow_to_sqlglot(
        inputs["flow"],
        object_name="Account",
        target_reference="$Record.Participant__r.AccountId",
        fields=FLOW_FIELDS,
        field_definitions=[exp.Expression.load(d) for d in inputs["field_definitions"]],
        source={"source_sha256": inputs["flow_sha256"], "source_org": inputs["source_org"]},
        simplify=simplify,
    )
    before = snapshot(history["Account"], as_of=account_before_at)
    contact = snapshot(history["Contact"], as_of=execution_at)
    surveys = snapshot(history["Survey_Result__c"], as_of=execution_at)
    trigger = surveys.filter(surveys.Id == survey_result_id)
    record = join_account(trigger, contact, before)
    supplied = {}
    for item in native.meta["ppsc"]["required_inputs"]:
        if item["table"].casefold() != "flow_record":
            continue
        name = item["column"]
        if name == "__eligible":
            supplied[name] = ibis.literal(eligibility, type="boolean")
        elif name == "__flow_run_date":
            supplied[name] = ibis.literal(flow_run_date, type="date")
        elif name.startswith("Before."):
            supplied[name] = record["Participant__r.Account." + name.removeprefix("Before.")]
        elif name.startswith("__known."):
            reference = name.removeprefix("__known.")
            # A NULL scalar on an existing row is known; a missing relationship is not.
            supplied[name] = (
                record["Participant__r.Account.Id"].notnull()
                if reference.startswith("Participant__r.Account")
                else record["Participant__r.Contact.Id"].notnull()
                if reference.startswith("Participant__r.")
                else ibis.literal(True)
            )
        else:
            supplied[name] = record[name]
    context = {
        "participant_contact_id": record.Participant__c,
        "survey_index_number": record.Survey_Index_Number__c,
        "survey_completion_timestamp": record.Completion_Status_Timestamp__c,
    }
    supplied.update({"__ops." + name: value for name, value in context.items()})
    record_sql = to_sqlglot(record.select(**supplied))
    lookup_sql = to_sqlglot(surveys)
    # Carry only comparison context alongside the native stable event identity.
    # This is a projection extension, with no join back to a nonunique event ID.
    for select in native.find_all(exp.Select):
        identity = next((p for p in select.selects if p.alias_or_name == "flow_record_id"), None)
        if identity is None:
            continue
        value = identity.unalias()
        if not isinstance(value, exp.Column):
            raise ValueError("Unsupported upstream event identity projection")
        select.select(
            *[
                _named(_col("__ops." + name, value.table or None), "__ops." + name)
                for name in context
            ],
            append=True,
            copy=False,
        )
    lookup_columns = {}
    for item in native.meta["ppsc"]["required_inputs"]:
        if item["role"] == "lookup":
            lookup_columns.setdefault(item["table"], []).append(item["column"])
    sources = [("Flow_Record", record_sql)]
    if lookup_columns:
        # All selected lookup roles share this independently bound execution snapshot.
        # Keep their native role names while avoiding repeated physical source text.
        sources.append(("Ops_Execution_Surveys", lookup_sql))
        sources.extend(
            (
                name,
                exp.select(*[_col(column) for column in dict.fromkeys(columns)]).from_(
                    exp.Table(this=exp.to_identifier("Ops_Execution_Surveys", quoted=True))
                ),
            )
            for name, columns in lookup_columns.items()
        )
    ctes = [
        exp.CTE(this=query.copy(), alias=exp.TableAlias(this=exp.to_identifier(name, quoted=True)))
        for name, query in sources
    ]
    with_clause = native.args.pop("with_", None)
    ctes.extend(with_clause.expressions if with_clause else [])
    # Rename only the native final projection; keep its CTEs and expression tree.
    # An extra SELECT wrapper would repeat every field and lookup diagnostic.
    final = native.copy()
    outputs = []
    identities = {"flow_target_id": "Id", "flow_record_id": "survey_result_id"}
    for projection in native.selects:
        name = projection.alias_or_name
        if name == "flow_row_id":
            continue
        canonical = identities.get(name, name.removeprefix("expected__").removeprefix("__ops."))
        output = _named(projection.unalias().copy(), canonical)
        field = canonical.removesuffix("__assigned").removesuffix("__deterministic")
        if name.startswith("expected__") and field in native.meta["ppsc"]["outputs"]:
            output.meta["ppsc"] = deepcopy(native.meta["ppsc"]["outputs"][field])
        outputs.append(output)
    final.set("expressions", outputs)
    final.set("with_", exp.With(expressions=ctes))
    final.meta["ppsc"] = {
        **deepcopy(native.meta["ppsc"]),
        "lake_bindings": metadata_receipt(inputs),
        "temporal_roles": {"before": str(account_before_at), "execution": str(execution_at)},
        "eligibility": eligibility,
    }
    return final


def flow_account_comparison(Expected: exp.Select, Observed: exp.Select) -> exp.Select:
    """Join canonical queries, adding literal dotted output labels for native GX.

    The observation never feeds the expected computation. This left join retains
    every triggering event and all matching AFTER occurrences, as before.
    """
    Expected = Expected.copy()
    comparison_fields = {
        field + suffix
        for field in FLOW_FIELDS
        for suffix in ("", "__assigned", "__deterministic", "_required", "_must_be_null")
    }
    expected_lineage = projection_lineage(Expected)
    ctes = [
        exp.CTE(
            this=Expected,
            alias=exp.TableAlias(this=exp.to_identifier("Expected_Account", quoted=True)),
        )
    ]
    final = exp.select(
        _named(_col("survey_result_id", "expected"), "survey_result_id"),
        _named(_col("survey_result_id", "expected"), "validation_record_id"),
        _named(_col("Id", "expected"), "expected.Id"),
        _named(_col("Id", "observed"), "observed.Id"),
        *[
            _col(name, "expected")
            for name in (
                "participant_contact_id",
                "survey_index_number",
                "survey_completion_timestamp",
            )
        ],
        *[
            _named(_col(name, "expected"), "expected." + name)
            if name in comparison_fields
            else _col(name, "expected")
            for name in Expected.named_selects
            if name
            not in {
                "Id",
                "survey_result_id",
                "participant_contact_id",
                "survey_index_number",
                "survey_completion_timestamp",
            }
        ],
        *[_named(_col(field, "observed"), "observed." + field) for field in FLOW_FIELDS],
        _named(
            _col("CABOR_Completion_Date__c__deterministic", "expected"),
            "cabor_lookup_is_deterministic",
        ),
        _named(
            exp.GTE(
                this=exp.cast(_col("survey_completion_timestamp", "expected"), "DATE"),
                expression=exp.cast(exp.Literal.string("2024-12-16"), "DATE"),
            ),
            "survey_completion_occurred_on_or_after_launch",
        ),
        _named(
            exp.and_(
                *[
                    exp.Is(
                        this=_col(field + "__deterministic", "expected"),
                        expression=exp.true(),
                    )
                    for field in FLOW_FIELDS
                ],
                *[
                    exp.Not(
                        this=exp.Is(
                            this=_col(field + "__assigned", "expected"),
                            expression=exp.Null(),
                        )
                    )
                    for field in FLOW_FIELDS
                ],
            ),
            "flow_evidence_is_complete",
        ),
        _named(
            exp.and_(
                *[
                    exp.Not(this=exp.Is(this=_col(name, alias), expression=exp.Null()))
                    for name, alias in [
                        ("survey_result_id", "expected"),
                        ("Id", "expected"),
                        ("participant_contact_id", "expected"),
                        ("Id", "observed"),
                    ]
                ],
                exp.EQ(
                    this=exp.Window(
                        this=exp.Count(this=exp.Star()),
                        partition_by=[_col("survey_result_id", "expected")],
                    ),
                    expression=exp.Literal.number(1),
                ),
            ),
            "comparison_keys_are_valid",
        ),
    ).from_(
        exp.Table(
            this=exp.to_identifier("Expected_Account", quoted=True),
            alias=exp.TableAlias(this=exp.to_identifier("expected", quoted=True)),
        )
    )
    final = final.join(
        Observed.copy().subquery("observed"),
        on=_col("Id", "expected").eq(_col("Id", "observed")),
        join_type="LEFT",
    )
    final.set("with_", exp.With(expressions=ctes))
    final.meta["ppsc"] = deepcopy(Expected.meta["ppsc"])
    for column in final.selects:
        name = column.alias_or_name
        if name.startswith("expected."):
            column.meta["ppsc"] = deepcopy(expected_lineage[name.removeprefix("expected.")])
        elif name.startswith("observed."):
            column.meta["ppsc"] = {
                "target_field": "Account." + name.removeprefix("observed."),
                "source_entities": ["Account." + name.removeprefix("observed.")],
                "comparison_role": "observed",
                "description": "Independently observed " + name,
            }
    return final


def flow_account_query(
    history: Mapping[str, ir.Table],
    *,
    survey_result_id: str,
    account_before_at: date | datetime,
    execution_at: date | datetime,
    account_after_at: date | datetime,
    flow_run_date: date,
    eligibility: bool | None,
    inputs: dict,
    simplify: bool = True,
) -> exp.Select:
    """Bind native Flow SELECT to independent BEFORE/execution/AFTER lake roles.

    Eligibility is an explicit verified trigger fact (None is unknown). Inputs
    may be provisional for offline evaluation; live workflow requires native evidence.
    """
    if not isinstance(account_after_at, date) or not isinstance(execution_at, date):
        raise TypeError("Bind explicit temporal values")
    try:
        ordered = execution_at < account_after_at
    except TypeError as error:
        raise ValueError("Temporal bindings must use comparable types and time zones") from error
    if not ordered:
        raise ValueError("Require account_before_at < execution_at < account_after_at")
    expected = expected_flow_account_query(
        history,
        survey_result_id=survey_result_id,
        account_before_at=account_before_at,
        execution_at=execution_at,
        flow_run_date=flow_run_date,
        eligibility=eligibility,
        inputs=inputs,
        simplify=simplify,
    )
    observed = observed_account_query(history, fields=FLOW_FIELDS, as_of=account_after_at)
    comparison = flow_account_comparison(expected, to_sqlglot(observed))
    comparison.meta["ppsc"]["temporal_roles"]["after"] = str(account_after_at)
    return comparison


class SqlParameter(BaseModel):
    """Declared scalar values; identifiers are bound separately as relations."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    type: str
    nullable: bool
    precision: int | None = None
    scale: int | None = None

    @model_validator(mode="after")
    def validate_type(self):
        if self.type not in {"string", "boolean", "integer", "decimal", "date", "timestamp"}:
            raise ValueError("Unsupported SQL parameter type")
        if self.type == "decimal":
            if (
                self.precision is None
                or self.scale is None
                or (not 0 <= self.scale <= self.precision <= 38)
            ):
                raise ValueError("Decimal requires exact precision and scale")
        elif self.precision is not None or self.scale is not None:
            raise ValueError("Precision/scale apply only to decimal")
        return self


class SqlOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    role: str
    rule_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_entities: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_role(self):
        if self.role not in {"key", "expected", "observed", "evidence"}:
            raise ValueError("Unsupported output role")
        return self


class SqlContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: int
    definition_id: str = Field(min_length=1)
    suite_name: str = Field(min_length=1)
    dialect: str
    parameters: dict[str, SqlParameter]
    relations: dict[str, RelationLocation]
    outputs: dict[str, SqlOutput]

    @model_validator(mode="after")
    def validate_version(self):
        if self.schema_version != 1 or self.dialect != "athena":
            raise ValueError("Expected SQL contract version 1 and Athena dialect")
        return self


def bind_authored_select(
    sql: str, contract: SqlContract, *, values: Mapping, suite_name: str
) -> exp.Select:
    """Bind one explicitly selected authored comparison; never infer execution from text."""
    from decimal import Context, Decimal

    import sqlglot

    from ppsc_ops_data_quality.runtime import prepare_query

    if suite_name != contract.suite_name:
        raise ValueError("Supplied native suite does not match SQL contract")
    statements = sqlglot.parse(sql, read=contract.dialect)
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError("Supply exactly one SELECT")
    query = statements[0]
    aliases = [p.alias_or_name for p in query.selects]
    if set(aliases) != set(contract.outputs) or len(aliases) != len(set(aliases)):
        raise ValueError("Output aliases must match lineage exactly")
    if any(not isinstance(p, (exp.Column, exp.Alias)) for p in query.selects):
        raise ValueError("Expressions require explicit output aliases")
    parameters = {p.name for p in query.find_all(exp.Placeholder)}
    if parameters != set(contract.parameters) or parameters != set(values):
        raise ValueError("Declared, used and supplied parameters must match exactly")
    literals = {}
    for name, declaration in contract.parameters.items():
        value = values[name]
        kind = declaration.type
        if value is None:
            if not declaration.nullable:
                raise ValueError(f"NULL forbidden: {name}")
            node = exp.Null()
        elif kind == "string" and isinstance(value, str):
            node = exp.Literal.string(value)
        elif kind == "boolean" and isinstance(value, bool):
            node = exp.convert(value)
        elif kind == "integer" and isinstance(value, int) and (not isinstance(value, bool)):
            node = exp.Literal.number(value)
        elif kind == "decimal" and isinstance(value, (str, Decimal)):
            decimal = Decimal(value)
            if (
                not decimal.is_finite()
                or decimal.copy_abs() >= Decimal(10) ** (declaration.precision - declaration.scale)
                or decimal
                != decimal.quantize(Decimal(1).scaleb(-declaration.scale), context=Context(prec=38))
            ):
                raise ValueError("Decimal would lose precision/scale")
            node = exp.Literal.number(str(decimal))
        elif kind == "date" and isinstance(value, date) and (not isinstance(value, datetime)):
            node = exp.Literal.string(value.isoformat())
        elif (
            kind == "timestamp" and isinstance(value, datetime) and (value.utcoffset() is not None)
        ):
            node = exp.Literal.string(
                value.astimezone(UTC).replace(tzinfo=None).isoformat(sep=" ") + " UTC"
            )
        else:
            raise ValueError(f"Invalid scalar value for {name}: {kind}")
        dtype = {
            "string": "VARCHAR",
            "boolean": "BOOLEAN",
            "integer": "BIGINT",
            "date": "DATE",
            "timestamp": "TIMESTAMP WITH TIME ZONE",
            "decimal": f"DECIMAL({declaration.precision},{declaration.scale})",
        }[kind]
        literals[name] = exp.Cast(this=node, to=exp.DataType.build(dtype, dialect="athena"))
    for placeholder in list(query.find_all(exp.Placeholder)):
        placeholder.replace(literals[placeholder.name].copy())
    used = set()
    for scope in traverse_scope(query):
        for node, source in scope.selected_sources.values():
            if not isinstance(node, exp.Table) or isinstance(source, Scope):
                continue
            if node.catalog or node.db or node.name not in contract.relations:
                raise ValueError("Authored SQL must read declared logical relation names")
            name = node.name
            location = contract.relations[name]
            used.add(name)
            if not node.alias:
                node.set("alias", exp.TableAlias(this=exp.to_identifier(name, quoted=True)))
            for key, value in [
                ("this", location.relation),
                ("db", location.database),
                ("catalog", location.catalog),
            ]:
                node.set(key, exp.to_identifier(value, quoted=True))
    if used != set(contract.relations):
        raise ValueError("Unused physical relation binding")
    query = prepare_query(query, locations=contract.relations)
    query.meta["ppsc"] = {
        "sql_contract": contract.model_dump(mode="json"),
        "source_sql_sha256": sha256(sql.encode()).hexdigest(),
        "typed_parameters": {name: node.sql(dialect="athena") for name, node in literals.items()},
    }
    for column in query.selects:
        column.meta["ppsc"] = contract.outputs[column.alias_or_name].model_dump(mode="json")
    return query


def check_native_columns(inputs: dict) -> None:
    """Require independently captured native definitions for selected scalar lake fields.

    Lake history columns are exempt. Exact types or explicitly widening conversions
    are accepted; missing, compound, and lossy mappings require reviewed inputs.
    """
    definitions = {}
    for dump in inputs["field_definitions"]:
        column = exp.Expression.load(dump)
        identity = column.meta["ppsc"]["target_field"]
        if identity in definitions:
            raise ValueError(f"Duplicate native definition: {identity}")
        definitions[identity] = column
    for dataset, binding in inputs["tables"].items():
        physical = physical_schema(inputs, dataset)
        for name, logical in binding["columns"].items():
            if logical in binding["history_fields"]:
                continue
            identity = binding["native_object"] + "." + logical
            if identity not in definitions:
                raise ValueError(f"Missing native type evidence: {identity}")
            native = ibis.Schema.from_sqlglot(
                exp.Schema(expressions=[definitions[identity]]), dialect="athena"
            )[definitions[identity].name]
            lake = physical[name]
            compatible = native == lake
            if native.is_decimal() and lake.is_decimal():
                compatible = (
                    lake.scale >= native.scale
                    and lake.precision - lake.scale >= native.precision - native.scale
                )
            if not compatible:
                raise ValueError(
                    f"Unreviewed/lossy native-to-lake type: {identity}: {native} -> {lake}"
                )


def rollup_projection_lineage() -> dict:
    """Explicit authored-rule provenance for the remaining workbook rollups."""
    outputs = {}
    for target, record in ROLLUP_FIELD_LINEAGE.items():
        field = target.removeprefix("Account.")
        outputs["expected." + field] = {
            **deepcopy(record),
            "target_field": target,
            "description": record["expression"].replace("_", " "),
            "comparison_role": "expected",
            "source_entities": [record["source_entity"]],
            "branches": [{**BRANCH_LINEAGE[name], "rule_id": name} for name in record["branches"]],
        }
        outputs["observed." + field] = {
            "description": "Independently observed " + target,
            "source_entities": [target],
            "comparison_role": "observed",
            "target_field": target,
        }
    return outputs
