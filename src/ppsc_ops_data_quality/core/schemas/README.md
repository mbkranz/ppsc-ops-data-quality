# Athena schema profiles

`schema_from_ddl(text)` converts one schema-only Athena `CREATE TABLE` declaration
into an ordinary nullable `ibis.Schema`. It executes no SQL and discovers no data.
SQLGlot parses the Athena dialect; Ibis owns the type conversion. There is no
second authored Python type map.

The supported profile contains explicit scalar columns. Multiple statements,
CTAS, views, duplicate column names (including case collisions), constraints,
defaults, partitions and storage declarations are rejected. Those constructs
require separate reviewed semantics. DDL profiles are input-type declarations,
not deployable table provisioning scripts.

```python
from ppsc_ops_data_quality.core.schemas import schema_from_ddl

schema = schema_from_ddl("CREATE TABLE input (`Id` STRING, `amount` DECIMAL(12,2))")
```

Account/Contact/Survey profiles live in
[`account_to_survey_results/inputs`](../../account_to_survey_results/inputs).
Their source constants and native history composition live in
[`input_schemas.py`](../../account_to_survey_results/input_schemas.py), and their
explicit unbound/catalog bindings live in
[`history.py`](../../account_to_survey_results/history.py).

The profiles preserve the previous workflow's 41 Account fields, three Contact
fields, nine Survey Result fields and four history fields. All raw fields remain
nullable so GX can detect invalid records. Account consent age is DECIMAL(3,0),
counts are BIGINT, survey index is text, birthdate is DATE, and completion fields
are TIMESTAMP. Timestamp-grain validity is provisional; an earlier lake sample
used DATE. Verify deployed Glue/Athena types separately. Date-grain history cannot
reconstruct several states in a day.

Generic callers can construct native `ibis.table(schema, ...)` relations directly.
No Salesforce names, relationships or history defaults are selected by core.
Aliases, approved casts, physical versions and deletion semantics stay explicit
upstream. Ibis retains supported VARCHAR length and TIMESTAMP precision parameters;
these declarations do not create GX length or precision expectations. Unsupported
parameters on Boolean, integer, floating and binary types are rejected.

Derived schemas come from the actual expression's `.schema()`. Arrow is an
interchange conversion, not a second type authority. SQLGlot `.meta` and arbitrary
Arrow metadata do not survive ordinary schema or SQL-text round trips. Keep
lineage detached and supply it explicitly during final query compilation.
