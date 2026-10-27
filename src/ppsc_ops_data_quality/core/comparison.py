"""Explicit expected/observed column bindings over native Ibis tables.

Source adapters compute expectations before calling this module. No metadata
format, object name, business rule, timestamp selection or data access lives here.
"""

import operator
from functools import reduce

import ibis
import ibis.expr.types as ir
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    def validate_bindings(self) -> "ComparisonSpec":
        for bindings in (self.keys, self.values):
            if len({item.name for item in bindings}) != len(bindings):
                raise ValueError("Binding names must be unique within each role")
        for side in ("expected", "observed"):
            if len({getattr(item, side) for item in self.keys}) != len(self.keys):
                raise ValueError("Composite keys must bind distinct source columns")
        outputs = [
            f"{side}_key__{key.name}" for key in self.keys for side in ("expected", "observed")
        ]
        for value in self.values:
            outputs.extend([f"expected__{value.name}", f"observed__{value.name}"])
            outputs.extend(
                f"expected__{value.name}__{role}"
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
    expected_columns = {f"expected_key__{key.name}": Expected[key.expected] for key in spec.keys}
    observed_columns = {f"observed_key__{key.name}": Observed[key.observed] for key in spec.keys}
    for value in spec.values:
        expected_columns[f"expected__{value.name}"] = Expected[value.expected]
        observed_columns[f"observed__{value.name}"] = Observed[value.observed]
        for role in ("deterministic", "assigned", "required", "must_be_null"):
            if (column := getattr(value, role)) is not None:
                expected_columns[f"expected__{value.name}__{role}"] = Expected[column]
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
            Expected[f"expected_key__{key.name}"] == Observed[f"observed_key__{key.name}"]
            for key in spec.keys
        ],
    )
    Comparison = Joined.select(Expected, Observed)
    complete = [Comparison._expected_present.notnull()]
    for value in spec.values:
        for role in ("deterministic", "assigned", "required", "must_be_null"):
            if getattr(value, role) is not None:
                column = Comparison[f"expected__{value.name}__{role}"]
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
                    Comparison[f"{side}_key__{key.name}"].notnull()
                    for key in spec.keys
                    for side in ("expected", "observed")
                ],
                Comparison._expected_unique,
                Comparison._observed_unique,
            ]
        ).fill_null(False),
        comparison_evidence_is_complete=_all(complete).fill_null(False),
    ).drop("_expected_present", "_expected_unique", "_observed_unique")
