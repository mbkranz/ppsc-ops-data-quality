"""Validated Athena inputs. Model construction performs no external work."""

from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ppsc_ops_data_quality.core.configuration import load_yaml

Name = Annotated[str, Field(min_length=1)]


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def s3_location(uri: str) -> tuple[str, str]:
    """Return bucket/key for an explicit S3 location, rejecting URL modifiers."""
    location = urlsplit(uri)
    if (
        location.scheme != "s3"
        or not location.netloc
        or not location.path.strip("/")
        or location.query
        or location.fragment
        or ".." in location.path.split("/")
    ):
        raise ValueError("Expected an explicit S3 bucket and key/prefix")
    return location.netloc, location.path.lstrip("/")


class AthenaConfiguration(Configuration):
    region: Name
    database: Name
    s3_staging_dir: Name
    work_group: Name
    catalog_name: Name = "AwsDataCatalog"
    connection_options: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_connection(self) -> Self:
        s3_location(self.s3_staging_dir)
        reserved = {"s3_staging_dir", "work_group", "catalog_name"}
        if reserved.intersection(self.connection_options):
            raise ValueError("Connection options must not override declared Athena settings")
        return self


class ReportConfiguration(Configuration):
    s3_uri: Name

    @model_validator(mode="after")
    def validate_destination(self) -> Self:
        s3_location(self.s3_uri)
        return self


class HistoryDatabases(Configuration):
    account_database: Name
    contact_database: Name
    survey_result_database: Name


class EventConfiguration(Configuration):
    survey_result_id: Name
    account_before_at: date | datetime
    execution_at: date | datetime
    account_after_at: date | datetime
    flow_run_date: date

    @model_validator(mode="after")
    def validate_temporal_order(self) -> Self:
        if isinstance(self.flow_run_date, datetime):
            raise ValueError("flow_run_date must be an org-local date")
        try:
            ordered = self.account_before_at < self.execution_at < self.account_after_at
        except TypeError as error:
            raise ValueError(
                "Temporal bindings must use comparable types and time zones"
            ) from error
        if not ordered:
            raise ValueError("Require account_before_at < execution_at < account_after_at")
        return self


class RollupConfiguration(Configuration):
    as_of: date | datetime


class SchemaOverrides(Configuration):
    account: dict[str, str] = Field(default_factory=dict)
    contact: dict[str, str] = Field(default_factory=dict)
    survey_result: dict[str, str] = Field(default_factory=dict)


class MetadataSelection(Configuration):
    org: Name
    flow_version_id: Name
    manifest_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ValidationConfiguration(Configuration):
    metadata: MetadataSelection
    athena: AthenaConfiguration
    reports: ReportConfiguration
    databases: HistoryDatabases
    event: EventConfiguration
    rollups: RollupConfiguration
    schema_overrides: SchemaOverrides = Field(default_factory=SchemaOverrides)


def load_validation_configuration(path: Path) -> ValidationConfiguration:
    values = load_yaml(path)
    if "REPLACE_WITH_" in str(values):
        raise ValueError("Replace the example configuration bindings before connecting")
    return ValidationConfiguration.model_validate(values)
