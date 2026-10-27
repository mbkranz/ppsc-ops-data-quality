"""Validated Athena inputs. Model construction performs no external work."""

from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ppsc_ops_data_quality.core.configuration import load_yaml
from ppsc_ops_data_quality.sources.apmp import RelationLocation

from .preflight import DataVersionBinding

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


class MetadataSelection(Configuration):
    org: Name
    flow_version_id: Name


class ValidationConfiguration(Configuration):
    metadata: MetadataSelection
    athena: AthenaConfiguration
    reports: ReportConfiguration
    locations: dict[str, RelationLocation]
    data_versions: dict[str, DataVersionBinding]
    require_repeatable_reads: bool = True
    event: EventConfiguration
    rollups: RollupConfiguration

    @model_validator(mode="before")
    @classmethod
    def reject_legacy_types(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if "schema_overrides" in values:
            overrides = values.pop("schema_overrides")
            if not isinstance(overrides, dict) or any(overrides.values()):
                raise ValueError(
                    "schema_overrides is retired; change the reviewed Ops Athena definition and rebuild its pinned release"
                )
        if "databases" in values:
            raise ValueError(
                "Database-only history bindings are retired; supply explicit APMP dataset locations with catalog/database/relation"
            )
        return values

    @model_validator(mode="after")
    def validate_selected_locations(self) -> Self:
        if not self.locations or set(self.locations) != set(self.data_versions):
            raise ValueError("Select exactly one location and data-version binding per dataset")
        identities = [location.identity for location in self.locations.values()]
        if len(set(identities)) != len(identities):
            raise ValueError("Selected dataset locations must be distinct")
        return self


def load_validation_configuration(path: Path) -> ValidationConfiguration:
    values = load_yaml(path)
    if "REPLACE_WITH_" in str(values):
        raise ValueError("Replace the example configuration bindings before connecting")
    return ValidationConfiguration.model_validate(values)
