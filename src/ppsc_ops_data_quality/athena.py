"""Athena connection, physical inspection, and snapshot-bound SQL sources."""

import argparse
import json
import sys
from datetime import UTC, datetime

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL

from .config import Config, TableBinding, data_type, load_config, validate_config


def snapshot_time(value: str) -> datetime:
    """Parse an explicit physical snapshot timestamp and normalize it to UTC."""
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("--lake-as-of needs a timezone, for example 2026-10-17T12:00:00Z")
    return result.astimezone(UTC)


def _quote(value: str, delimiter: str = '"') -> str:
    return delimiter + value.replace(delimiter, delimiter * 2) + delimiter


def _table_name(binding: TableBinding, *, suffix: str = "") -> str:
    return ".".join(
        _quote(part) for part in (binding.catalog, binding.database, binding.name + suffix)
    )


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Physical snapshot selection must have a timezone")
    return value.astimezone(UTC).replace(tzinfo=None).isoformat(sep=" ")


def sqlalchemy_url(config: Config) -> URL:
    """Use the standard AWS credential chain; no access keys belong in configuration."""
    settings = config.athena
    query = {
        "catalog_name": settings.catalog,
        "work_group": settings.workgroup,
        "s3_staging_dir": settings.s3_staging_dir,
    }
    if settings.profile:
        query["profile_name"] = settings.profile
    return URL.create(
        "awsathena+rest",
        host=f"athena.{settings.region}.amazonaws.com",
        port=443,
        database=settings.database,
        query=query,
    )


def source_table(binding: TableBinding, lake_as_of: datetime) -> str:
    """Project canonical names from a pinned source without reading or casting data."""
    columns = ", ".join(
        f"{_quote(column.name)} AS {_quote(alias)}" for alias, column in binding.columns.items()
    )
    return (
        f"SELECT {columns} FROM {_table_name(binding)} "
        f"FOR TIMESTAMP AS OF TIMESTAMP '{_timestamp(lake_as_of)}'"
    )


def inspect_tables(
    config: Config, *, discover: bool = False, lake_as_of: datetime | None = None
) -> dict:
    """Inspect metadata only; optional snapshot metadata is recorded when available."""
    validate_config(config, live=True, discovery=discover)
    engine = create_engine(sqlalchemy_url(config))
    report = {"catalog": config.athena.catalog, "database": config.athena.database, "tables": {}}
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            if discover:
                report["table_names"] = inspector.get_table_names(schema=config.athena.database)
                return report
            if not config.tables:
                raise ValueError("Configure table names or use --discover")
            for subject, binding in config.tables.items():
                entry = {"name": binding.name}
                report["tables"][subject] = entry
                try:
                    columns = inspector.get_columns(binding.name, schema=binding.database)
                    entry["columns"] = [
                        {
                            "name": column["name"],
                            "type": str(column["type"]),
                            "declared_type": str(column["type"]),
                        }
                        for column in columns
                    ]
                    ddl_name = ".".join(_quote(p, "`") for p in (binding.database, binding.name))
                    entry["ddl"] = "\n".join(
                        str(row[0])
                        for row in connection.execute(text(f"SHOW CREATE TABLE {ddl_name}"))
                    )
                except Exception as error:
                    entry["error"] = f"{type(error).__name__}: {error}"
                    continue
                if lake_as_of is not None:
                    snapshots = _table_name(binding, suffix="$snapshots")
                    query = (
                        f"SELECT snapshot_id, committed_at FROM {snapshots} "
                        f"WHERE committed_at <= TIMESTAMP '{_timestamp(lake_as_of)}' "
                        "ORDER BY committed_at DESC LIMIT 1"
                    )
                    try:
                        rows = connection.execute(text(query)).mappings().all()
                        entry["snapshot_metadata"] = [dict(row) for row in rows]
                    except Exception as error:
                        entry["snapshot_metadata_unavailable"] = f"{type(error).__name__}: {error}"
    finally:
        engine.dispose()
    return report


def check_physical_schema(config: Config, report: dict) -> None:
    """Reject missing or mistyped physical input before projecting canonical columns."""
    problems = []
    for subject, binding in config.tables.items():
        entry = report["tables"].get(subject, {})
        if "error" in entry:
            problems.append(f"{subject}: {entry['error']}")
            continue
        actual = {
            column["name"]: data_type(column["declared_type"])
            for column in entry.get("columns", [])
        }
        for alias, column in binding.columns.items():
            if column.name not in actual:
                problems.append(f"{subject}.{alias}: physical column {column.name!r} is missing")
                continue
            expected = data_type(column.type)
            found = actual[column.name]
            # Reflection can omit timestamp precision; compare it when both report it.
            timestamps = {"TIMESTAMP", "TIMESTAMPNTZ", "TIMESTAMPTZ"}
            if expected.is_type(*timestamps) and found.is_type(*timestamps):
                matches = expected.this == found.this and (
                    not expected.expressions
                    or not found.expressions
                    or expected.expressions == found.expressions
                )
            else:
                matches = expected == found
            if not matches:
                problems.append(f"{subject}.{alias}: expected {expected}, found {found}")
    if problems:
        raise ValueError("Physical schema preflight failed: " + "; ".join(problems))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Athena metadata before binding pilot tables"
    )
    parser.add_argument("--config", default="params.local.yaml")
    parser.add_argument(
        "--discover", action="store_true", help="List tables without column bindings"
    )
    parser.add_argument("--lake-as-of", type=snapshot_time)
    args = parser.parse_args(argv)
    try:
        report = inspect_tables(
            load_config(args.config), discover=args.discover, lake_as_of=args.lake_as_of
        )
        print(json.dumps(report, indent=2, default=str))
        return 2 if any("error" in entry for entry in report["tables"].values()) else 0
    except Exception as error:
        print(f"Inspection error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
