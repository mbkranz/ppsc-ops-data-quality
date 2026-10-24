"""Verified Salesforce projections feeding the source-independent comparison."""

from collections.abc import Callable

import ibis.expr.types as ir
from ppsc_metadata.artifacts import MetadataBundle
from ppsc_metadata.contracts import property_references
from ppsc_metadata.sources.salesforce_flow import FlowRequest, flow_assignments
from ppsc_metadata.sources.salesforce_rollup import RollupRequest, rollup_values

from ppsc_ops_data_quality.core.comparison import (
    ComparisonSpec,
    KeyBinding,
    ValueBinding,
    compare_values,
)


def flow_comparison(
    Record: ir.Table,
    Observed: ir.Table,
    request: FlowRequest,
    spec: ComparisonSpec,
    *,
    inputs: MetadataBundle,
    eligibility: Callable[[ir.Table], ir.BooleanValue],
) -> ir.Table:
    """Compare arbitrary selected Flow targets, without QA2/application defaults.

    Record supplies BEFORE values, resolved relationship paths, lookup/formula
    context and independent presence predicates. Use the producer's flow_context
    with explicit lookup tables and execution date upstream when needed. Callers
    select source/observation snapshots and business scope. No implicit join,
    current-state fallback, trigger policy or metadata lookup is performed here.
    """
    if inputs.flow is None:
        raise ValueError("No verified Flow selected")
    if {value.name for value in spec.values} != set(request.fields):
        raise ValueError("Comparison fields must match the selected Flow fields")
    for field in request.fields:
        if f"{request.object_name}.{field}" not in property_references(inputs.contract):
            raise ValueError(f"Unbound Flow target: {request.object_name}.{field}")
    projection = flow_assignments(Record, inputs.flow["Metadata"], request, eligibility=eligibility)
    columns = {}
    for value in spec.values:
        if value.deterministic is None or value.assigned is None:
            raise ValueError("Flow comparisons require determinism and assignment evidence")
        for column, expression in (
            (value.expected, projection.expressions[value.name]),
            (value.deterministic, projection.deterministic[value.name]),
            (value.assigned, projection.assigned[value.name]),
        ):
            if column in columns or column in Record.columns:
                raise ValueError(f"Flow projection column collides: {column}")
            columns[column] = expression
    return compare_values(Record.mutate(**columns), Observed, spec)


def native_rollup_comparison(
    Parent: ir.Table,
    Child: ir.Table,
    Observed: ir.Table,
    request: RollupRequest,
    *,
    source_field: str,
    inputs: MetadataBundle,
) -> ir.Table:
    """Compare a verified native rollup on any object; no workbook fallback.

    Parent, Child and Observed are independent, caller-selected snapshots.
    The compiler preserves every parent input row; core checks duplicate keys
    before equality, including observations with no expected parent.
    """
    _, separator, field = source_field.partition(".")
    if not separator or field != request.output_field:
        raise ValueError("Bind the selected native rollup to its declared output field")
    if source_field not in property_references(inputs.contract):
        raise ValueError(f"Unbound rollup source field: {source_field}")
    if source_field not in inputs.rollups:
        raise ValueError(f"No verified native rollup selected: {source_field}")
    Expected = rollup_values(
        Parent.select(request.parent_key), Child, inputs.rollups[source_field], request
    )
    spec = ComparisonSpec(
        keys=(KeyBinding(name="parent", expected=request.parent_key, observed=request.parent_key),),
        values=(ValueBinding(name=field, expected=field, observed=field),),
    )
    return compare_values(Expected, Observed, spec)
