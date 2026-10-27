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
metadata. Flow-derived expectations should supply independent determinism and assignment bindings.

Pass `suite.meta["finding_key_columns"]` as native GX's
`unexpected_index_column_names` to retain all expected and observed composite-key
parts in findings. Orchestration supplies independent row counts, snapshot
freshness, exclusion/quarantine policy, detached source lineage, immutable input
receipts and run metadata. The suite builder creates no context or execution.
Use the existing runner's explicit result-format argument and report handoffs.


## Standalone source composition

Source interpretation belongs upstream. Supply the expected native Ibis relation
and its evidence columns directly to `compare_values(Expected, Observed, spec)`.
There is no runtime Salesforce/ODCS adapter or metadata compiler requirement.
For example, a caller-owned rollup can aggregate children, LEFT JOIN the result
to every parent (including zero-child parents), and compare that expected relation
to independently observed values using the same typed `ComparisonSpec`.

The Account workflow's local `flow.flow_assignments(Record)` returns native Ibis
values keyed by expected field, assignment and determinism names. It can be
composed into an expected relation with `Record.mutate(**values)` before calling
the generic comparison. It selects no snapshots or observations on the caller's
behalf. Other objects or surveys can provide their own native Ibis builders.

Core imports no application profiles or domain workflow. Standalone installation
checks run the wheel without Salesforce, the old metadata compiler or ODCS.
See [definition authoring](metadata-compiler.md) for optional producer tooling.
