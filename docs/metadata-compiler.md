# Native inputs and lake definitions

Source acquisition belongs to `ppsc-salesforce`. With an authenticated client:

```python
from salesforce.entities.field_definitions.api import download_api_export

receipt = download_api_export(
    client, ["Account", "Contact", "Survey_Result__c"], output_path="captures/fields.json"
)
```

Select saved native API records and their exact identities in `inputs.yaml` beside
`flow.json`, the field export and separately saved lake DDL. See the bundled offline
[manifest](../src/ppsc_ops_data_quality/account_to_survey_results/metadata/inputs.yaml)
for physical aliases, history fields, partition declarations and relation kinds. Set
`field_export` to the capture filename and `native_fields` to every selected scalar
`Object.Field` identity. Native component records are selected from their actual parent
`Particles.records` with parent identity retained. Missing/unsupported evidence fails;
compound parents cannot masquerade as scalar columns.

`io.load_inputs` parses the selected CREATE TABLE definitions, hashes all input bytes,
checks relation identity and invokes the Salesforce single-column compiler on selected
native fields/components. It never derives native types from lake DDL. The live workflow
requires native evidence for every mapped non-history field and rejects unreviewed or
lossy types. Decimal scale zero and source pointers/hashes survive in native ColumnDefs.
Explicit physical relation names override the lowercased native-object `_history`
convention. Exporting/discovering DDL never executes it.

The checked-in lake DDL was migrated from the previous synthetic profile and remains
`provisional: true`, with no invented field capture. It supports offline compilation and
synthetic tests. A real capture and independently reviewed DDL are required before a
live run. These are deployment inputs, not missing source compiler functionality.

`flows.to_sqlglot(..., simplify=True)` replaces the former FlowRequest/flow_context/
flow_assignments Ibis path. Ops retains the native source graph, node sequence, output
lineage, capture hash versus canonical Metadata hash, eligibility contract and simplified
required logical reads. Lookup-derived UPDATE targets, unsupported control effects and
unrepresentable temporal arithmetic remain explicit upstream failures.

Online `runtime.check_catalog` verifies selected catalog names/types, partition and table
identity, then probes selected immutable versions where required. Extra columns are
recorded; they do not redefine the selected schema. Every physical query occurrence gets
the corresponding version, with CTE references excluded by SQL scope resolution.
Mutable inputs require explicit diagnostic mode and establish no repeatability.
