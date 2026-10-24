# Reusing expected-value comparisons across sources

The shared consumer accepts native Ibis relations and explicit, validated column
bindings. Object names, field lists, Flow IDs, survey launch dates, eligibility,
lookup resolution and source interpretation stay outside core. There is no
source registry, rule DSL, automatic discovery or replacement GX engine.

## Source-independent comparison

`core.comparison.ComparisonSpec` declares the complete comparison grain and value
bindings. Keys and values can have different source and target names. Composite
keys remain ordered typed columns, never concatenated strings. Each value may
bind separate source-computation determinism, assignment, required and
must-be-null evidence columns. These must be boolean; unknown remains NULL.

```python
from ppsc_ops_data_quality.core.comparison import (
    ComparisonSpec,
    KeyBinding,
    ValueBinding,
    compare_values,
)
from ppsc_ops_data_quality.core.comparison_gx import comparison_suite

spec = ComparisonSpec(
    keys=(
        KeyBinding(name="tenant", expected="source_tenant", observed="target_tenant"),
        KeyBinding(name="response", expected="response_id", observed="external_id"),
    ),
    values=(
        ValueBinding(
            name="answer",
            expected="mapped_answer",
            observed="QID42",
            deterministic="mapping_is_known",
            required="display_rule_is_true",
            must_be_null="hide_rule_is_true",
        ),
    ),
    scope="source_is_in_scope",
)
Comparison = compare_values(Expected, Observed, spec)
suite = comparison_suite(spec, name="response_migration")
```

`Expected` must already contain independently computed mapping/rule outputs.
`Observed` is the separately selected target snapshot. A full outer join retains
missing parents, extra target records, missing keys and duplicate matches. Window
checks partition by the full comparison key on each input before joining. They
do not deduplicate rows. Invalid grain blocks equality and fails the independent
structural check. An unexpected target row stays in scope and fails reconciliation.
Select the intended observed cohort upstream; unrelated records are not silently
excluded by this API. Scope false excludes value checks, while scope NULL fails
completeness. Select approved key and value types upstream; implicit casts are rejected.
This prevents typed false and numeric zero, or text and numeric answers, from
passing through backend coercion. Explicitly cast both sides to the reviewed
comparison type, including decimal precision/scale and temporal timezone.

Value equality, requiredness and must-be-null are distinct native GX checks.
Assignment false still compares a retained BEFORE value. Determinism false,
unknown assignment or unknown presence evidence fails completeness. Both-NULL
pairs use GX's native missing count and scoped denominator; one-sided NULLs fail.
No normalization removes physical invalid answers, false, zero or sentinels.
Absent optional evidence is an explicit producer claim, not inferred missing
metadata. The Salesforce Flow adapter requires determinism and assignment bindings.

Pass `suite.meta["finding_key_columns"]` as native GX's
`unexpected_index_column_names` to retain all expected and observed composite-key
parts in findings. Orchestration supplies independent row counts, snapshot
freshness, exclusion/quarantine policy, ODCS source definitions, immutable input
receipts and run metadata. The suite builder creates no context or execution.
Use the existing runner's explicit result-format argument and report handoffs.

## Salesforce adapters

`sources.salesforce.flow_comparison` accepts a verified `MetadataBundle`, a
producer `FlowRequest`, the comparison specification and explicit native Ibis
eligibility predicate. It compiles the selected object and fields once through
`ppsc_metadata`. It never selects the Account workflow, QA2 files or cached global
request. Prepare relationship paths and BEFORE state upstream. When lookups or
formulas are needed, call the producer's `flow_context` with the selected Flow,
request, source tables and execution date first. Requested target fields must
exist in the supplied contract; missing assignments and unsupported native
constructs retain compiler diagnostics. Output/evidence collisions fail explicitly.

`sources.salesforce.native_rollup_comparison` accepts any contracted parent
object, child object, selected native rollup and explicit parent key. The caller
chooses snapshots and the empty/all-null aggregate policy. Keys use source-neutral
`expected_key__parent` and `observed_key__parent` names. The Account module retains
its existing public wrapper with compatibility aliases. The active 19 workbook
rollups remain unchanged pending reviewed org definitions and policies.

The existing Account event builder and runtime configuration remain one explicit
workflow. Their field list, join paths, launch cutoff and CABOR-specific evidence
are application policy, not shared defaults for new flows. New workflows compose
native source queries, adapters and suite builders explicitly; adding a workflow
does not mean editing an Account field list or introducing a dispatcher. Existing
Account suites and the generic suite share the native equality/null constructor.

## Migration mappings and Qualtrics

A mapping producer or Qualtrics compiler can feed the same boundary by preparing
native expected columns and independent rule evidence. Display-required and
hide/must-be-null are independent nullable predicates; one is never inferred as
the complement of the other. Preserve source IDs, rule paths, dependency and
transformation definitions in the producer's contract/lineage handoff.

This change does not implement a Qualtrics parser, mapping interpreter or universal
metadata manifest. The current producer `projection-inputs/v1` manifest explicitly
requires a Salesforce Flow; do not relabel it as a Qualtrics handoff. A future
source adapter needs its own reviewed parser, validated immutable evidence,
source semantics and executable parity fixtures. It can then call the same
comparison/suite functions. Source acquisition, survey ownership and governance
policy remain separate work.

## Review and validation

Independent verified Case and Order Flows exercise different target objects,
fields, Flow identities and literal assignments. Invoice rollups use a custom
parent key. Migration/Qualtrics-shaped fixtures use differently named composite
keys and columns, shared response IDs across tenants, retained values, typed
false/zero, serialized answers and sentinels. Native DuckDB and GX execute the
comparisons, including duplicate fanout, unmatched observations, missing keys,
unknown scope/evidence, NULL coverage and keyed findings. The shared SQL renderer
is also executed against DuckDB. These fixtures establish boundary reuse; they
are not acceptance of a real Qualtrics schema or mapping policy.

PPSC review: structured inputs are validated, all source/table dependencies are
explicit, native Ibis/GX interfaces are retained, and core imports neither the
Account workflow nor Salesforce metadata parsers. Source adapters perform no
acquisition or execution. Poe and the four DVC release producers retain ownership.
