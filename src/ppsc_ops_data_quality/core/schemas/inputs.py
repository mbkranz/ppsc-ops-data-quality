"""Legacy schema constants derived from the pinned provisional APMP handoff.

Live execution supplies its verified selection to the APMP adapter directly.
These offline convenience constants certify no deployed catalog.
"""

from importlib.resources import files
from pathlib import Path

import ibis

from ppsc_ops_data_quality.sources.apmp import load_inputs, logical_schema


def provisional_schema(native_object: str, *, include_history: bool) -> ibis.Schema:
    root = Path(str(files("ppsc_ops_data_quality"))) / "account_to_survey_results/metadata"
    inputs = load_inputs(root)
    matches = [
        (dataset_id, binding)
        for dataset_id, binding in inputs["tables"].items()
        if binding["native_object"] == native_object
    ]
    if len(matches) != 1:
        raise ValueError(f"Select one APMP dataset for {native_object}")
    dataset_id, binding = matches[0]
    schema = logical_schema(inputs, dataset_id)
    if include_history:
        return schema
    return ibis.schema(
        {name: dtype for name, dtype in schema.items() if name not in binding["history_fields"]}
    )


def provisional_history_schema() -> ibis.Schema:
    root = Path(str(files("ppsc_ops_data_quality"))) / "account_to_survey_results/metadata"
    inputs = load_inputs(root)
    schemas = [
        ibis.schema(
            {name: logical_schema(inputs, dataset_id)[name] for name in binding["history_fields"]}
        )
        for dataset_id, binding in inputs["tables"].items()
    ]
    if not schemas or any(schema != schemas[0] for schema in schemas[1:]):
        raise ValueError("Legacy common history profile requires identical selected history fields")
    return schemas[0]
