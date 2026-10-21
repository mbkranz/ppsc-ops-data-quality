"""One YAML configuration for connection settings and explicit physical bindings."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import ibis
import yaml


@dataclass(frozen=True)
class Column:
    name: str
    type: str


@dataclass(frozen=True)
class TableBinding:
    catalog: str
    database: str
    name: str
    columns: dict[str, Column]


@dataclass(frozen=True)
class AthenaSettings:
    region: str
    catalog: str
    database: str
    workgroup: str
    s3_staging_dir: str
    profile: str | None = None


@dataclass(frozen=True)
class Config:
    athena: AthenaSettings
    tables: dict[str, TableBinding]
    output: Path
    interval_convention_confirmed: bool = False
    load_completion_evidence: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return non-secret settings suitable for run provenance."""
        result = asdict(self)
        result["output"] = str(self.output)
        return result


def _mapping(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{name} cannot contain control characters")
    return value


def load_config(path: str | Path) -> Config:
    """Load settings; discovery does not require table schemas to be populated."""
    with Path(path).open() as stream:
        data = _mapping(yaml.safe_load(stream), "configuration")
    settings = _mapping(data.get("athena"), "athena")
    allowed = {"region", "catalog", "database", "workgroup", "s3_staging_dir", "profile"}
    unknown = settings.keys() - allowed
    if unknown:
        raise ValueError(f"Unknown Athena settings: {', '.join(sorted(unknown))}")
    values = {key: _string(settings.get(key), f"athena.{key}") for key in allowed - {"profile"}}
    profile = settings.get("profile")
    if profile is not None:
        profile = _string(profile, "athena.profile")
    athena = AthenaSettings(**values, profile=profile)
    tables = {}
    for subject, raw in _mapping(data.get("tables", {}), "tables").items():
        raw = _mapping(raw, f"tables.{subject}")
        columns = {}
        for alias, column in _mapping(raw.get("columns", {}), f"{subject}.columns").items():
            _string(alias, "column alias")
            column = _mapping(column, f"{subject}.{alias}")
            columns[alias] = Column(
                _string(column.get("name"), f"{subject}.{alias}.name"),
                _string(column.get("type"), f"{subject}.{alias}.type"),
            )
        tables[subject] = TableBinding(
            catalog=athena.catalog,
            database=athena.database,
            name=raw.get("name", ""),
            columns=columns,
        )
    confirmed = data.get("interval_convention_confirmed", False)
    if not isinstance(confirmed, bool):
        raise ValueError("interval_convention_confirmed must be true or false")
    evidence = data.get("load_completion_evidence")
    if evidence is not None:
        evidence = _string(evidence, "load_completion_evidence")
    return Config(
        athena=athena,
        tables=tables,
        output=Path(_string(data.get("output", "build/runs"), "output")),
        interval_convention_confirmed=confirmed,
        load_completion_evidence=evidence,
    )


def validate_config(config: Config, *, live: bool, discovery: bool = False) -> None:
    """Require actual connection values only for live operations."""
    if live:
        for name, value in asdict(config.athena).items():
            if value is not None and ("<" in value or "REPLACE_ME" in value):
                raise ValueError(f"Replace the placeholder in athena.{name} before connecting")
        if not config.athena.s3_staging_dir.startswith("s3://"):
            raise ValueError("athena.s3_staging_dir must be an s3:// location")
    if discovery:
        return
    for subject, binding in config.tables.items():
        _string(binding.name, f"tables.{subject}.name")
        if live and ("<" in binding.name or "REPLACE_ME" in binding.name):
            raise ValueError(f"Replace the placeholder in tables.{subject}.name")
        if live:
            for alias, column in binding.columns.items():
                if "<" in column.name or "REPLACE_ME" in column.name:
                    raise ValueError(
                        f"Replace the placeholder in tables.{subject}.columns.{alias}.name"
                    )


def validate_bindings(config: Config) -> None:
    """Check the declared types used by Ibis without accessing AWS."""
    required = {"id", "valid_from", "valid_to", "is_current", "loaded_at"}
    for subject in ("account", "account_contact_relation"):
        if subject not in config.tables:
            raise ValueError(f"Missing tables.{subject}")
        binding = config.tables[subject]
        needed = required | ({"account_id"} if subject == "account_contact_relation" else set())
        missing = needed - binding.columns.keys()
        if missing:
            raise ValueError(f"{subject}: missing column bindings {', '.join(sorted(missing))}")
        physical = [column.name for column in binding.columns.values()]
        if len(physical) != len(set(physical)):
            raise ValueError(f"{subject}: physical column bindings must be unique")
        types = {alias: ibis.dtype(column.type) for alias, column in binding.columns.items()}
        for name in ("id", "account_id"):
            if name in types and not types[name].is_string():
                raise ValueError(
                    f"{subject}.{name} must be a string; do not cast IDs into compliance"
                )
        if not types["is_current"].is_boolean():
            raise ValueError(f"{subject}.is_current must be boolean")
        start, end = types["valid_from"], types["valid_to"]
        if not (start.is_date() or start.is_timestamp()) or start != end:
            raise ValueError(
                f"{subject}: valid_from and valid_to need the same date/timestamp type"
            )
        if not (types["loaded_at"].is_date() or types["loaded_at"].is_timestamp()):
            raise ValueError(f"{subject}.loaded_at must be a date/timestamp")
