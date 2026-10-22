"""Version 1 discovery projections over native GX results, authored as Ibis schemas.

Source: GX ExpectationSuiteValidationResult.to_json_dict(). Query/table identity
comes from explicit caller metadata, not SQL parsing. Arrow is only the Parquet
interchange. Timestamps are UTC, timezone-free, millisecond precision for Athena.
Variable-shaped GX fields remain JSON strings rather than inferred structs.
"""

import ibis

REPORT_IDENTITY = {
    "report_schema_version": "int32",
    "run_id": "string",
    "run_name": "string",
    "run_time_utc": "timestamp(3)",
    "run_status": "string",
    "gx_version": "string",
    "validation_definition_name": "string",
    "validation_definition_id": "string",
    "suite_name": "string",
    "data_source_name": "string",
    "data_asset_name": "string",
    "source_tables": "array<string>",
    "source_query_dialect": "string",
    "source_query": "string",
    "source_query_sha256": "string",
    "source_query_uri": "string",
    "raw_result_uri": "string",
    "data_docs_uri": "string",
    "run_metadata_json": "string",
    "expectation_parameters_json": "string",
}

VALIDATION_RUN_RESULTS = ibis.schema(
    {
        **REPORT_IDENTITY,
        "validation_status": "string",
        "success": "boolean",
        "evaluated_expectations": "int64",
        "successful_expectations": "int64",
        "unsuccessful_expectations": "int64",
        "success_percent": "float64",
        "statistics_json": "string",
    }
)

EXPECTATION_RUN_RESULTS = ibis.schema(
    {
        **REPORT_IDENTITY,
        "expectation_index": "int64",
        "check_id": "string",
        "expectation_type": "string",
        "column_name": "string",
        "column_a": "string",
        "column_b": "string",
        "success": "boolean",
        "element_count": "int64",
        "missing_count": "int64",
        "unexpected_count": "int64",
        "unexpected_percent": "float64",
        "raised_exception": "boolean",
        "row_condition_json": "string",
        "expectation_kwargs_json": "string",
        "expectation_meta_json": "string",
        "result_json": "string",
        "exception_info_json": "string",
    }
)
