# Schemas for the Account / Survey Result queries

Schemas are ordinary `ibis.Schema` objects. Each source declaration contains all
columns required by this validation workflow. `VALIDATION_INPUT` explicitly scopes
the relation: these are not full exports of every Salesforce object field and are
not catalog-discovered physical Athena schemas.

## Source and snapshot schemas

| Module | Constants | Columns |
|---|---|---:|
| `account.py` | `ACCOUNT_VALIDATION_INPUT` | 41 |
| | `ACCOUNT_HISTORY_VALIDATION_INPUT`, `ACCOUNT_SNAPSHOT_VALIDATION_INPUT` | 45 |
| `contact.py` | `CONTACT_VALIDATION_INPUT` | 3 |
| | `CONTACT_HISTORY_VALIDATION_INPUT`, `CONTACT_SNAPSHOT_VALIDATION_INPUT` | 7 |
| `survey_results.py` | `SURVEY_RESULT_VALIDATION_INPUT` | 9 |
| | `SURVEY_RESULT_HISTORY_VALIDATION_INPUT`, `SURVEY_RESULT_SNAPSHOT_VALIDATION_INPUT` | 13 |
| `history.py` | `HISTORY_METADATA` | 4 |

Field types are traced to `salesforce_schemas_combined_latest.xlsx`,
`datamodel-Fields`, with row numbers beside each declaration. In particular:

- Account consent age is Salesforce `Number(3,0)`, represented as `decimal(3,0)`.
- COUNT rollups are represented as `int64`; this is a logical count mapping.
- Survey index is text, preserving its source definition and string comparisons.
- Contact birthdate is a date; completion/signature fields are timestamps.
- Every raw field is nullable, including source-required IDs. Requiredness remains
  a data validation rule and does not remove invalid records from the input.

History metadata comes from the earlier Athena sample: `valid_from`, `valid_to`,
`is_current`, and `loaded_at`. This module provides a timestamp-grain history
profile for the event examples. The previous sample used date-grain validity;
verify which schema the producer actually writes. Timezone and timestamp precision
are unspecified in this profile. The module invents no partition/discriminator or
deletion columns, and performs no casts, reads or writes on import.

Snapshots filter rows without changing the schema. Account BEFORE and AFTER use
the same Account snapshot schema at distinct effective instants. Current and
historical snapshot reads have the same column definitions.

## Bind the inputs

```python
from ppsc_ops_data_quality.schemas import history_tables
from ppsc_ops_data_quality.queries import flow_account_query

history = history_tables(
    account_database="your_account_database",
    contact_database="your_contact_database",
    survey_result_database="your_survey_result_database",
)
Comparison = flow_account_query(
    history,
    survey_result_id=verified_event_id,
    account_before_at=verified_before_time,
    execution_at=verified_execution_time,
    account_after_at=verified_settled_after_time,
    flow_run_date=org_local_execution_date,
)
```

Each relation references a table named `history` in its configured object database.
It is unbound Ibis input for Athena compilation, not a live backend connection.

Supply real catalog schemas through `account_schema=`, `contact_schema=` and
`survey_result_schema=`. Extra columns are preserved; no automatic casting or
renaming occurs. If the catalog uses lowercase names, normalize/project aliases
upstream before calling the query builders. `queries.bind_history_tables()` remains
available when an existing backend can inspect the catalog.

For example, an explicitly date-grain input can be declared with native composition:

```python
import ibis
from ppsc_ops_data_quality.schemas import ACCOUNT_HISTORY_VALIDATION_INPUT

AccountDailyHistory = ibis.schema(
    {
        **ACCOUNT_HISTORY_VALIDATION_INPUT.fields,
        "valid_from": "date",
        "valid_to": "date",
    }
)
```

Pass `date` values when snapshotting that relation. Date-grain history cannot
reconstruct BEFORE/execution/AFTER states within a single day.

## Derived table and view schemas

`derived.py` exposes these schemas, inferred from the existing expression builders:

| Constant | Columns |
|---|---:|
| `JOINED_SURVEY_ACCOUNT_RECORD` | 29 |
| `FLOW_EXECUTION_RECORD` | 43 |
| `EXPECTED_ACCOUNT_BY_SURVEY_EVENT` | 29 |
| `OBSERVED_ACCOUNT_AFTER_BY_SURVEY_EVENT` | 46 |
| `EXPECTED_ACCOUNT_SURVEY_ROLLUPS` | 21 |
| `FLOW_ACCOUNT_COMPARISON` | 44 |
| `ROLLUP_ACCOUNT_COMPARISON` | 41 |

Symbolic Ibis parameters supply the DATE and event ID types needed for inference;
there is no fabricated event or runtime execution. These constants describe the
default source profiles. With catalog overrides or custom projections, obtain the
schema from the resulting expression:

```python
comparison_schema = Comparison.schema()
```

A GX Query Asset wraps the SELECT without changing its output columns. An optional
Athena view uses the defining query's schema; `views.create_view()` already returns
an Ibis relation with that schema. No duplicate view-schema declaration is needed.
Inferred schemas are not independent assertions of output stability. Add a
separately reviewed contract only for outputs whose consumers require one.

## Interchange and provenance

```python
from ppsc_ops_data_quality.schemas import ACCOUNT_HISTORY_VALIDATION_INPUT

arrow_schema = ACCOUNT_HISTORY_VALIDATION_INPUT.to_pyarrow()
column_defs = ACCOUNT_HISTORY_VALIDATION_INPUT.to_sqlglot_column_defs(dialect="athena")
```

Use `ibis.Schema.from_pyarrow(arrow_schema)` to import an Arrow schema. Use
`ibis.Schema.from_sqlglot(exp.Schema(expressions=column_defs), dialect="athena")`
for SQLGlot column definitions, rather than a SQLGlot `MappingSchema` object.
The schema-level `to_sqlglot()` method is deprecated.

Arrow can make previously unspecified timestamp precision concrete during
conversion. Arbitrary Arrow metadata is not carried through Ibis schema round
trips. Field/branch provenance remains in the independent lineage mapping and
schema declaration docstrings/comments, not in custom Ibis attributes. SQLGlot
column `.meta` also does not survive a SQLGlot -> Ibis -> SQLGlot schema
conversion, or rendering/reparsing ordinary SQL text. Keeping the original
metadata-bearing schema AST is possible, but still requires reattaching that
metadata to compiled query outputs. SQLGlot dump/load retains custom metadata
in the tested AST representation.

The schemas package depends on Ibis. Importing `schemas.derived` also requires the
existing derivation, lineage and query modules alongside it; the complete bundle
contains those files. Source schema imports do not load GX or evaluate data.

References:

- [Ibis schemas](https://ibis-project.org/reference/schemas)
- [Arrow schemas](https://arrow.apache.org/docs/python/generated/pyarrow.schema.html)
