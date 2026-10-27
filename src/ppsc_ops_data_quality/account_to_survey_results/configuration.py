"""Validated inputs to the explicit Account/Survey Athena workflow."""

from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Self

from pydantic import Field, model_validator

from ppsc_ops_data_quality.core.configuration import load_yaml
from ppsc_ops_data_quality.runtime.configuration import (
    AthenaConfiguration,
    Configuration,
    Name,
    ReportConfiguration,
)


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
