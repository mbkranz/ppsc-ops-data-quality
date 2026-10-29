# Explicit foreign key boundary

Historical record. Current interfaces and acceptance are described in [the native Flow SQL plan](specs/minimal-implementation-plan.md).

`normalize_foreign_keys(bindings)` validates a selected APMP `LakeBindings` and
returns native `RelationshipBinding` values with ordered source/target fields.
Each relationship explicitly names source/target objects and ordered field tuples.
Missing fields, mismatched arity, duplicate/conflicting declarations, external
unbound targets and unsupported configuration fail before query construction.

Native source field references describe provenance. They do not create foreign
keys. The three Account/Survey application joins are checked against explicit
ordered APMP bindings. Additional relationships are not automatically executed by
that workflow.

Executed regression coverage includes native Ibis/DuckDB composite joins and GX
keyed findings. A crossed pair whose individual values exist in the parent fails;
an actual pair passes. A nullable composite reference is outside the relationship
match check (SQL MATCH SIMPLE); requiredness remains a separate native check.

The prior ODCS normalization and shorthand encodings are retired with v1 inputs.
Pydantic owns the binding invariants; native relations remain the query interface.
