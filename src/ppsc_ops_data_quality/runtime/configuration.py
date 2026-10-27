"""Validated Athena inputs. Model construction performs no external work."""

from typing import Annotated, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
