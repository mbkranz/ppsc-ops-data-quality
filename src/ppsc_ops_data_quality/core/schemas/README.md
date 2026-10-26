# Selected APMP input schemas

The input schema authority is the generated, pinned APMP handoff under
`account_to_survey_results/metadata`. Salesforce/APMP owns its source definitions.
Ops verifies every selected byte through `projection-inputs/v2`, reads Athena DDL
with `ppsc_metadata.schemas.athena_schema`, and builds native Ibis relations.
There is no independently authored Ops schema copy.

The packaged Account, Contact and Survey Results selection is a **provisional
fixture** migrated from the previous compatibility profile. Its catalog names,
physical types, history resolution and native equivalence have not been accepted
against a real lake. Source metadata capture and data snapshots have separate
identities.

`account.py`, `contact.py`, `survey_results.py` and `history.py` retain public
schema constants for offline examples. They derive from the same verified handoff;
module imports acquire no Salesforce or AWS data. Derived comparison schemas come
from the actual Ibis expressions in `account_to_survey_results.schemas`.

```python
from ppsc_ops_data_quality.core.queries import history_tables
from ppsc_ops_data_quality.sources.apmp import RelationLocation

# verified_inputs is an explicitly selected MetadataBundle.
history = history_tables(
    inputs=verified_inputs,
    locations={
        dataset_id: RelationLocation(
            catalog=selected_catalog,
            database=selected_database,
            relation=selected_relation,
        )
        for dataset_id in selected_dataset_ids
    },
)
```

The physical relation uses the real catalog, database, table and columns. A
`select` then executes physical-to-native aliases. Relabeling only schema names
would leave SQL reading nonexistent columns and is not supported. Raw NULLs stay
nullable; requiredness, value membership and conditional rules belong to checks.

No implicit casts are introduced. The initial mapping profile supports direct
projections. A conversion requires a reviewed producer definition and explicit
failure evidence before it can be selected. Free-form runtime `schema_overrides`
are retired and rejected with a migration message.

Runtime preflight compares selected live names/types, partition declarations and
table/view kind before GX queries. Additional unreferenced columns are recorded
and allowed with explicit projections. A view requires verified output-schema
metadata and real registered relation bindings; live view compatibility remains
unestablished until deployed SQL/dependencies can also be verified.

Timestamp history is required for the existing intra-day Flow workflow. DATE
history remains valid source evidence but cannot establish arbitrary
BEFORE/execution/AFTER states. The runtime reports that gap before connecting.
