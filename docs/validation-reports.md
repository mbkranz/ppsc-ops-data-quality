# Validation evidence and discovery

Keep native GX output as audit evidence and publish two typed Parquet projections
for Glue/Athena discovery. Use an existing private S3 bucket/prefix. The runtime
does not create hosting, buckets, permissions, crawlers or catalog tables.

| Artifact | Format | Purpose |
| --- | --- | --- |
| Native result per returned validation | `.json.gz`, one compact JSON line | Preserve the complete `to_json_dict()` object, including GX metadata and expectation-specific details |
| Native Data Docs | HTML and the full generated static asset tree | Readable suites and validation results |
| Validation discovery | Snappy Parquet, one row per planned Validation Definition | Status, statistics, run identity and source/query provenance; includes definitions without a result |
| Expectation discovery | Snappy Parquet, one row per returned expectation result | Check identity, row condition, success, common metrics and lineage |
| Exact suites and queries | Native suite JSON and SQL | Preserve actual configured expectations and the comparison submitted by the adapter |
| Publication manifest | JSON, uploaded last | Enumerate the run artifacts and record execution status |

Parquet is the recommended catalog format. It provides typed nullable columns,
column selection and predicate pushdown, and avoids repeatedly inferring GX's
heterogeneous nested JSON. The existing PyArrow dependency writes it from the
ordinary Ibis schemas in `schemas/validation_reports.py`. Variable-shaped fields
(`observed_value`, unexpected samples, row-condition structures, kwargs, result
details and metadata) stay in JSON strings. Common scalar metrics have columns.
These projections are derived evidence, not replacements for raw native GX JSON.

If JSON must be queried directly, use one JSON object per line (JSONL/NDJSON),
optionally gzip compressed. Pretty-printed JSON is not suitable for the usual
Hive/OpenX JSON SerDes. The archived native result already meets that framing,
but its changing nested structures make it less convenient as the main catalog
table. There is no third, independently authored JSON discovery representation.

## S3 layout

```text
s3://REPORTS_BUCKET/ppsc-data-quality/
  runs/<run_uuid>/
    results/000_flow.json.gz
    suites/000_flow.suite.json
    queries/000_flow.sql
    data_docs/index.html
    data_docs/validations/...
    data_docs/static/...
    manifest.json
  analytics/validations/run_date=YYYY-MM-DD/<run_uuid>.parquet
  analytics/expectations/run_date=YYYY-MM-DD/<run_uuid>.parquet
```

Each invocation receives an artifact UUID. `run_name` remains the caller's GX
label, and `run_time_utc` comes from the shared GX RunIdentifier. The UTC run date
is independent of event/completion dates. One Parquet file per run per dataset
limits fragmentation; do not partition by UUID, definition or expectation. If run
volume grows, compact discovery files in a separate maintenance workflow before
adding Iceberg or another ingestion framework.

Both projections expose run UUID/name/time/status, report schema version, GX
version, Validation Definition name/ID, suite, data source/asset, source-table
identifiers, actual comparison query text/dialect/hash, artifact URIs, explicit
run metadata and runtime expectation parameters. The expectation projection also
exposes check ID, type, target columns, row condition, pass/fail and common metrics.
The query is the submitted comparison SELECT; GX metric SQL may wrap it.
Callers provide physical source-table names, source pins and temporal parameters.
SQL parsing is not used to guess source identities.

## Runtime use

The Athena example requires `[reports].s3_uri` in `params.local.toml`. It uses
`runtime.run_validations_with_reports()` and supplies catalog-qualified source
tables, the Query Asset's actual SQL, and temporal metadata. AWS authentication
uses the standard boto3 provider chain; callers can inject an existing S3 client.
The demo uses the same report builder locally and accepts optional `--s3-uri`.
The lower-level `run_validations()` remains usable without publication; supply
`result_directory` there to archive each native result immediately.

Use a fresh Context and local report directory per invocation. Native GX builds
Data Docs into a run-specific filesystem site; boto3 uploads that complete tree.
The upload allowlist excludes GX context/connection configuration and DataFrames.
The Data Docs S3 URI identifies a stored site; S3 publication does not itself set
up browser hosting. Existing authenticated hosting/access arrangements can serve
the files without changing this pipeline.

Ordinary failed expectations are exported and later definitions still execute.
On an execution error, earlier returned JSON survives; planned definitions
without archived results have `validation_status='no_result'`, `success=NULL`,
and no raw-result URI. This does not falsely attribute an error to an unevaluated
definition. `run_status='execution_error'` and the manifest carry the run error.
The original error is re-raised after reporting. If reporting also fails, both
errors propagate in an ExceptionGroup.

S3 writes refuse existing keys using `IfNoneMatch='*'`. Failed publication raises
an error and retains local files. The manifest is uploaded last and proves the
allowlisted uploads finished for that run. This is not an atomic multi-object
commit: Parquet can be visible before the marker. Consumers requiring confirmed
publication should verify the manifest; the Hive tables alone cannot guarantee
transactional visibility. There is no automatic resume or compaction, and no
completion marker is written when an earlier upload fails.

## Catalog registration

Use `sql/validation_reports_catalog.sql` as an explicit deployment template.
Replace the bucket/prefix and first UTC run date, then execute in the intended
Athena/Glue database. It registers two external Parquet tables over **only** the
corresponding analytics prefixes. Never point a crawler/table at `runs/` or the
mixed root containing JSON, HTML, suites and queries.

The template uses a STRING `run_date` partition with date projection so Athena
discovers new days without crawler runs or per-run Glue updates. Start the range
at the first retained run date, not the Flow launch date. Projection is Athena
query behavior: other Glue consumers may require explicit partitions. Keep
projection ranges and retention aligned. A deployment can use ordinary catalog
partitions instead when runs are sparse or other consumers need them.

```sql
SELECT run_date, run_id, validation_definition_name, check_id,
       source_tables, source_query_sha256, unexpected_count, raw_result_uri
FROM quality_expectation_results
WHERE run_date BETWEEN '2026-10-21' AND '2026-10-22'
  AND success = false;
```

Schemas and catalog templates are versioned together. Additive nullable columns
require a deliberate catalog update; incompatible schema/grain changes require a
new version/prefix. NULL counts mean GX did not return that metric, not zero.
No live S3 upload or catalog deployment is part of the synthetic acceptance run.

## Primary references

- [GX 1.24 Configure Data Docs](https://docs.greatexpectations.io/docs/core/configure_project_settings/configure_data_docs/) documents native filesystem sites and manual builds. Older S3 store examples are not the current supported guide, so this implementation stages locally and uploads through boto3.
- [Athena columnar storage](https://docs.aws.amazon.com/athena/latest/ug/columnar-storage.html) describes Parquet/ORC and predicate pushdown.
- [Athena JSON SerDes](https://docs.aws.amazon.com/athena/latest/ug/json-serde.html) describes one-object-per-line requirements and the Ion alternative for pretty JSON.
- [Athena compression](https://docs.aws.amazon.com/athena/latest/ug/compression-formats.html) documents gzip and Snappy support.
- [Athena partition projection](https://docs.aws.amazon.com/athena/latest/ug/partition-projection.html) explains Athena-only discovery, empty-range tradeoffs and catalog partition behavior.
- [Athena timestamp/partition types](https://docs.aws.amazon.com/athena/latest/ug/data-types-timestamps.html) recommends STRING partition keys.
