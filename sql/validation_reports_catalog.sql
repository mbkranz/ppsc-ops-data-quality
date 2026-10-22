-- Catalog deployment template: replace every REPLACE_WITH_* value before execution.
-- Register only these Parquet prefixes, never runs/ (HTML, JSON and suites).
-- run_date is the validation-run date in UTC, not a survey completion date.
-- SQL DDL is deployment configuration; it is not authored validation SQL input.

CREATE EXTERNAL TABLE IF NOT EXISTS quality_validation_results (
  report_schema_version INT,
  run_id STRING,
  run_name STRING,
  run_time_utc TIMESTAMP,
  run_status STRING,
  gx_version STRING,
  validation_definition_name STRING,
  validation_definition_id STRING,
  suite_name STRING,
  data_source_name STRING,
  data_asset_name STRING,
  source_tables ARRAY<STRING>,
  source_query_dialect STRING,
  source_query STRING,
  source_query_sha256 STRING,
  source_query_uri STRING,
  raw_result_uri STRING,
  data_docs_uri STRING,
  run_metadata_json STRING,
  expectation_parameters_json STRING,
  validation_status STRING,
  success BOOLEAN,
  evaluated_expectations BIGINT,
  successful_expectations BIGINT,
  unsuccessful_expectations BIGINT,
  success_percent DOUBLE,
  statistics_json STRING
)
PARTITIONED BY (run_date STRING)
STORED AS PARQUET
LOCATION 's3://REPLACE_WITH_REPORTS_BUCKET/ppsc-data-quality/analytics/validations/'
TBLPROPERTIES (
  'projection.enabled' = 'true',
  'projection.run_date.type' = 'date',
  'projection.run_date.format' = 'yyyy-MM-dd',
  'projection.run_date.range' = 'REPLACE_WITH_FIRST_RUN_DATE,NOW',
  'storage.location.template' = 's3://REPLACE_WITH_REPORTS_BUCKET/ppsc-data-quality/analytics/validations/run_date=${run_date}/'
);

CREATE EXTERNAL TABLE IF NOT EXISTS quality_expectation_results (
  report_schema_version INT,
  run_id STRING,
  run_name STRING,
  run_time_utc TIMESTAMP,
  run_status STRING,
  gx_version STRING,
  validation_definition_name STRING,
  validation_definition_id STRING,
  suite_name STRING,
  data_source_name STRING,
  data_asset_name STRING,
  source_tables ARRAY<STRING>,
  source_query_dialect STRING,
  source_query STRING,
  source_query_sha256 STRING,
  source_query_uri STRING,
  raw_result_uri STRING,
  data_docs_uri STRING,
  run_metadata_json STRING,
  expectation_parameters_json STRING,
  expectation_index BIGINT,
  check_id STRING,
  expectation_type STRING,
  column_name STRING,
  column_a STRING,
  column_b STRING,
  success BOOLEAN,
  element_count BIGINT,
  missing_count BIGINT,
  unexpected_count BIGINT,
  unexpected_percent DOUBLE,
  raised_exception BOOLEAN,
  row_condition_json STRING,
  expectation_kwargs_json STRING,
  expectation_meta_json STRING,
  result_json STRING,
  exception_info_json STRING
)
PARTITIONED BY (run_date STRING)
STORED AS PARQUET
LOCATION 's3://REPLACE_WITH_REPORTS_BUCKET/ppsc-data-quality/analytics/expectations/'
TBLPROPERTIES (
  'projection.enabled' = 'true',
  'projection.run_date.type' = 'date',
  'projection.run_date.format' = 'yyyy-MM-dd',
  'projection.run_date.range' = 'REPLACE_WITH_FIRST_RUN_DATE,NOW',
  'storage.location.template' = 's3://REPLACE_WITH_REPORTS_BUCKET/ppsc-data-quality/analytics/expectations/run_date=${run_date}/'
);
