"""Native GX checks for the source-independent prepared comparison columns."""

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.expectations.row_conditions import Column

from .comparison import ComparisonSpec


def equal_values(*, field: str, row_condition, meta: dict, description: str | None = None):
    """The shared native equality/null policy; callers supply applicability."""
    return gxe.ExpectColumnPairValuesToBeEqual(
        column_A=f"observed__{field}",
        column_B=f"expected__{field}",
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
    keys = [f"{side}_key__{key.name}" for key in spec.keys for side in ("expected", "observed")]
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
        expected, observed = f"expected__{value.name}", f"observed__{value.name}"
        columns.extend([expected, observed])
        applicable = valid
        for role in ("deterministic", "assigned", "required", "must_be_null"):
            if getattr(value, role) is not None:
                column = f"expected__{value.name}__{role}"
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
