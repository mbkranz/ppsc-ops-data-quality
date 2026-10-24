# ODCS foreign key boundary

`normalize_foreign_keys(contract)` accepts validated ODCS v3.2.0 contracts and
returns validated `ForeignKey` values with ordered source and target fields.
Object declarations specify `from` and `to`; property declarations infer their
single source property. An omitted type has the standard `foreignKey` meaning.
Composite relationships stay one relationship. Equivalent declarations collapse;
conflicting mappings, missing targets, mismatched arity, unbound external targets,
and unsupported syntax fail before query construction.

Stable `authoritativeDefinitions` field references describe provenance. They do
not create foreign keys. ODCS property relationships do not permit `from`, and a
composite key belongs at object level. Standard relationship references and
stable provenance pointers are validated under their respective standard forms.

The three application join bindings are checked against this normalized result,
so equivalent property and object declarations load identically. Arbitrary
additional contract relationships are not automatically executed by the fixed
Account/Survey workflow.

Executed regression coverage includes native Ibis/DuckDB composite joins and GX
keyed findings. A crossed pair whose individual values exist in the parent fails;
an actual pair passes. A nullable composite reference is outside the relationship
match check (SQL MATCH SIMPLE); requiredness remains a separate native check.

PPSC review: the existing ODCS boundary owns normalization, Pydantic owns the
key's invariants, and native tables remain the query interface. No generic query
runtime, expectation subclass, registry, or relational DSL was added.
