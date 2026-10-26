"""Explicit online compatibility checks and per-relation Iceberg snapshot evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from time import monotonic, sleep
from typing import Any, Literal

import ibis
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlglot import exp

from ppsc_ops_data_quality.sources.apmp import (
    RelationLocation,
    dataset_binding,
    physical_schema,
)


class DataVersionBinding(BaseModel):
    """A selected snapshot is applied to SQL, not merely recorded in a receipt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["mutable", "iceberg_snapshot"] = "mutable"
    snapshot_id: str | None = Field(default=None, pattern=r"^[1-9][0-9]*$")

    @model_validator(mode="after")
    def validate_snapshot(self):
        if (self.mode == "iceberg_snapshot") != (self.snapshot_id is not None):
            raise ValueError("Select a positive snapshot_id exactly for iceberg_snapshot mode")
        return self


class RelationPreflight(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_id: str
    location: RelationLocation
    compatible: bool
    checked_at: datetime
    catalog_sha256: str
    additional_columns: tuple[str, ...]
    data_version: DataVersionBinding
    source_sql: str
    schema_query_execution_id: str | None = None
    repeatability_established: bool
    limitations: tuple[str, ...]


def _column_type(column: dict[str, Any]) -> str:
    declared = column["Type"]
    if declared.casefold() == "decimal":
        precision = column.get("Precision")
        scale = column.get("Scale", 0)
        if (
            not isinstance(precision, int)
            or not isinstance(scale, int)
            or not 1 <= precision <= 38
            or not 0 <= scale <= precision
        ):
            raise ValueError(f"Exact decimal precision/scale unavailable for {column['Name']}")
        return f"decimal({precision},{scale})"
    return declared


def _catalog_schema(columns: list[dict[str, Any]], *, fields: tuple[str, ...] | None = None):
    if fields is not None:
        columns = [column for column in columns if column["Name"] in fields]
    schema = exp.Schema(
        expressions=[
            exp.ColumnDef(
                this=exp.to_identifier(column["Name"], quoted=True),
                kind=exp.DataType.build(_column_type(column), dialect="athena"),
            )
            for column in columns
        ]
    )
    return ibis.Schema.from_sqlglot(schema, dialect="athena")


def _qualified_table(location: RelationLocation) -> exp.Table:
    return exp.Table(
        this=exp.to_identifier(location.relation, quoted=True),
        db=exp.to_identifier(location.database, quoted=True),
        catalog=exp.to_identifier(location.catalog, quoted=True),
    )


def snapshot_sql(location: RelationLocation, columns: tuple[str, ...], snapshot_id: str) -> str:
    """Use SQLGlot's native Athena version node for a bounded schema probe."""
    table = _qualified_table(location)
    table.set(
        "version",
        exp.Version(this="VERSION", expression=exp.Literal.number(snapshot_id), kind="AS OF"),
    )
    return (
        exp.select(*(exp.column(column, quoted=True) for column in columns))
        .from_(table)
        .limit(0)
        .sql(dialect="athena")
    )


def _query_schema(athena_client: Any, sql: str, *, query_options: dict, timeout_seconds: float):
    execution = athena_client.start_query_execution(QueryString=sql, **query_options)[
        "QueryExecutionId"
    ]
    deadline = monotonic() + timeout_seconds
    while True:
        state = athena_client.get_query_execution(QueryExecutionId=execution)["QueryExecution"][
            "Status"
        ]
        if state["State"] == "SUCCEEDED":
            break
        if state["State"] in {"FAILED", "CANCELLED"}:
            raise ValueError(
                f"Snapshot schema preflight failed: {state.get('StateChangeReason', state['State'])}"
            )
        if monotonic() >= deadline:
            athena_client.stop_query_execution(QueryExecutionId=execution)
            raise TimeoutError("Snapshot schema preflight exceeded its bounded timeout")
        sleep(0.25)
    response = athena_client.get_query_results(QueryExecutionId=execution, MaxResults=1)
    columns = response["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
    return _catalog_schema(columns), execution


def check_catalog(
    inputs: dict,
    *,
    dataset_ids: tuple[str, ...],
    locations: dict[str, RelationLocation],
    data_versions: dict[str, DataVersionBinding],
    athena_client: Any,
    query_options: dict,
    require_repeatable_reads: bool = True,
    timeout_seconds: float = 45,
) -> tuple[RelationPreflight, ...]:
    """Block drift before validation queries; never claim saved hashes certify live tables.

    The supplied client performs the online operation. Snapshot schema probes use
    the exact selected ID later applied by the shared query renderer. Separate
    table snapshots do not establish business-time or cross-table atomicity.
    """
    if not dataset_ids or len(set(dataset_ids)) != len(dataset_ids):
        raise ValueError("Select nonempty unique dataset IDs for catalog preflight")
    if set(locations) != set(dataset_ids) or set(data_versions) != set(dataset_ids):
        raise ValueError("Each selected dataset requires one location and data-version binding")
    results = []
    for dataset_id in dataset_ids:
        binding = dataset_binding(inputs, dataset_id)
        location = locations[dataset_id]
        version = data_versions[dataset_id]
        expected = physical_schema(inputs, dataset_id)
        try:
            response = athena_client.get_table_metadata(
                CatalogName=location.catalog,
                DatabaseName=location.database,
                TableName=location.relation,
            )
        except Exception as error:
            raise ValueError(
                f"Catalog compatibility unestablished for {location.identity}: {type(error).__name__}"
            ) from error
        observed = response.get("TableMetadata")
        if not isinstance(observed, dict):
            raise ValueError(f"Catalog metadata unavailable for {location.identity}")
        if observed.get("Name") != location.relation:
            raise ValueError(f"Catalog identity changed for {location.identity}")
        if observed.get("TableType", "").upper() not in {
            "EXTERNAL_TABLE",
            "MANAGED_TABLE",
            "VIRTUAL_VIEW",
        }:
            raise ValueError(f"Catalog relation kind unavailable for {location.identity}")
        kind = "view" if observed["TableType"].upper() == "VIRTUAL_VIEW" else "table"
        if kind != binding["kind"]:
            raise ValueError(f"Catalog relation kind changed for {location.identity}")
        if kind == "view":
            # GetTableMetadata does not establish the deployed SQL/dependencies.
            # A matching column list alone cannot certify a changed view.
            raise ValueError(
                f"View definition/dependencies remain unverified for {location.identity}; capture and verify deployed view evidence"
            )
        partitions = tuple(column["Name"] for column in observed.get("PartitionKeys", []))
        if partitions != tuple(binding["partition_columns"]):
            raise ValueError(f"Catalog partition declarations changed for {location.identity}")
        # Permit the same exact partition declaration exposed in both API lists,
        # but never accept name collisions as harmless unreferenced additions.
        unique = {}
        casefolded = {}
        for declarations in (observed.get("Columns", []), observed.get("PartitionKeys", [])):
            group_names = set()
            for column in declarations:
                name = column["Name"]
                folded = name.casefold()
                if folded in casefolded and casefolded[folded] != name:
                    raise ValueError(
                        f"Catalog case-colliding column names changed for {location.identity}: {casefolded[folded]}, {name}"
                    )
                if name in group_names:
                    raise ValueError(f"Duplicate catalog column declaration: {name}")
                if name in unique and _column_type(unique[name]) != _column_type(column):
                    raise ValueError(f"Conflicting catalog declarations for {name}")
                group_names.add(name)
                casefolded[folded] = name
                unique[name] = column
        missing_names = set(expected.names).difference(unique)
        if missing_names:
            raise ValueError(
                f"Catalog schema changed for {location.identity}: missing={sorted(missing_names)}"
            )
        catalog_schema = _catalog_schema(list(unique.values()), fields=expected.names)
        missing = set(expected.names).difference(catalog_schema.names)
        changed = [
            name
            for name in expected.names
            if name in catalog_schema and expected[name] != catalog_schema[name]
        ]
        if missing or changed:
            raise ValueError(
                f"Catalog schema changed for {location.identity}: missing={sorted(missing)}, changed={changed}"
            )
        source_sql = (
            exp.select(*(exp.column(name, quoted=True) for name in expected.names))
            .from_(_qualified_table(location))
            .sql(dialect="athena")
        )
        query_id = None
        limitations = []
        repeatable = False
        if version.mode == "iceberg_snapshot":
            if str(observed.get("Parameters", {}).get("table_type", "")).upper() != "ICEBERG":
                raise ValueError(
                    f"Snapshot binding requires an observed Iceberg table: {location.identity}"
                )
            source_sql = snapshot_sql(location, expected.names, version.snapshot_id)
            historical_schema, query_id = _query_schema(
                athena_client,
                source_sql,
                query_options=query_options,
                timeout_seconds=timeout_seconds,
            )
            if historical_schema != expected:
                raise ValueError(
                    f"Selected Iceberg historical schema differs from saved definition: {location.identity}"
                )
            repeatable = True
            limitations.append(
                "Separate table snapshots establish no cross-table transaction or business-time alignment"
            )
        else:
            limitations.append(
                "Mutable input: observation window cannot guarantee repeatable reads across GX metric queries"
            )
            if require_repeatable_reads:
                raise ValueError(
                    f"Stable-input assertion unestablished for mutable relation {location.identity}; select an Iceberg snapshot or run explicitly diagnostic comparisons"
                )
        if binding["provisional"] or any(
            table["provisional"] for table in inputs["tables"].values()
        ):
            limitations.append(
                "Provisional source/mapping evidence; live semantic acceptance remains outstanding"
            )
        results.append(
            RelationPreflight(
                dataset_id=dataset_id,
                location=location,
                compatible=True,
                checked_at=datetime.now(UTC),
                catalog_sha256=sha256(
                    json.dumps(observed, sort_keys=True, default=str).encode()
                ).hexdigest(),
                additional_columns=tuple(name for name in unique if name not in expected.names),
                data_version=version,
                source_sql=source_sql,
                schema_query_execution_id=query_id,
                repeatability_established=repeatable,
                limitations=tuple(limitations),
            )
        )
    return tuple(results)
