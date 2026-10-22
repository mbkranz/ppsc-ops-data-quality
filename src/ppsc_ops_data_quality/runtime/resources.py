"""Fetch and verify hash-pinned runtime configuration with an injected S3 client."""

import hashlib
from contextlib import closing
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .configuration import s3_location


class ConfigurationResource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    uri: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        s3_location(self.uri)
        return self


class VerifiedConfiguration(ConfigurationResource):
    content: bytes


def read_configuration(request: ConfigurationResource, *, s3_client: Any) -> VerifiedConfiguration:
    bucket, key = s3_location(request.uri)
    response = s3_client.get_object(Bucket=bucket, Key=key)
    with closing(response["Body"]) as stream:
        content = stream.read()
    digest = hashlib.sha256(content).hexdigest()
    if digest != request.sha256:
        raise ValueError("Runtime configuration SHA256 does not match submitted run")
    return VerifiedConfiguration(uri=request.uri, sha256=digest, content=content)
