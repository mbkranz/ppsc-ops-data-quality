"""Nullable validation inputs authored once as schema-only Athena DDL profiles."""

import ibis

from ppsc_ops_data_quality.core.schemas import schema_from_ddl

from .metadata import metadata_inputs


def _profile(name: str) -> ibis.Schema:
    return schema_from_ddl(
        metadata_inputs().schemas[f"account_to_survey_results/inputs/{name}.sql"]
    )


HISTORY_METADATA = _profile("history")
ACCOUNT_VALIDATION_INPUT = _profile("account")
CONTACT_VALIDATION_INPUT = _profile("contact")
SURVEY_RESULT_VALIDATION_INPUT = _profile("survey_results")


def _with_history(schema: ibis.Schema) -> ibis.Schema:
    if set(schema.names) & set(HISTORY_METADATA.names):
        raise ValueError("Object columns collide with history metadata")
    return ibis.schema({**schema.fields, **HISTORY_METADATA.fields})


ACCOUNT_HISTORY_VALIDATION_INPUT = _with_history(ACCOUNT_VALIDATION_INPUT)
CONTACT_HISTORY_VALIDATION_INPUT = _with_history(CONTACT_VALIDATION_INPUT)
SURVEY_RESULT_HISTORY_VALIDATION_INPUT = _with_history(SURVEY_RESULT_VALIDATION_INPUT)
ACCOUNT_SNAPSHOT_VALIDATION_INPUT = ACCOUNT_HISTORY_VALIDATION_INPUT
CONTACT_SNAPSHOT_VALIDATION_INPUT = CONTACT_HISTORY_VALIDATION_INPUT
SURVEY_RESULT_SNAPSHOT_VALIDATION_INPUT = SURVEY_RESULT_HISTORY_VALIDATION_INPUT
