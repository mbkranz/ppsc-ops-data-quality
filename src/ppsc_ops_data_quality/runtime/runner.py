"""Execute native GX Validation Definitions with parameters bound per definition."""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

import great_expectations as gx
from great_expectations.core import ExpectationSuiteValidationResult, RunIdentifier

from .artifacts import save_result, save_suite, validation_artifact_stem


def _validate_targets(definitions, **parameters):
    names = [definition.name for definition in definitions]
    if len(names) != len(set(names)):
        raise ValueError("Validation Definition names must be unique within a run")
    for label, mapping in parameters.items():
        unknown = set(mapping or {}) - set(names)
        if unknown:
            raise ValueError(f"{label} references unknown definitions: {sorted(unknown)}")


def run_validations(
    definitions: Sequence[gx.ValidationDefinition],
    *,
    suite_directory: str | Path,
    result_directory: str | Path | None = None,
    batch_parameters: Mapping[str, Mapping[str, object]] | None = None,
    expectation_parameters: Mapping[str, Mapping[str, object]] | None = None,
    run_id: RunIdentifier | None = None,
    result_format: str | dict = "SUMMARY",
) -> dict[str, ExpectationSuiteValidationResult]:
    """Run definitions sequentially and return native results keyed by name.

    Provenance: GX ValidationDefinition.run(). Parameters are keyed by definition
    name so separate DataFrame validations never receive another definition's
    data. A shared RunIdentifier groups the invocation. Immediately before each
    run, serialize definition.suite to the explicit run-scoped suite_directory.
    Filenames include sequence and a readable sanitized definition name. Existing
    snapshots are never overwritten. GX stores results through the Context.
    When result_directory is supplied, also archive each returned native result
    immediately as gzip JSON, including failed expectations. Completed earlier
    results survive a later execution error. Execution errors have no native result.
    The runner needs no Ibis expression or engine API.

    An expectation failure is a returned unsuccessful result and does not stop
    later definitions. Execution/configuration errors propagate immediately;
    earlier results can already be stored by GX. Duplicate names and unknown
    parameter targets are rejected before any validation runs. An empty sequence
    returns an empty result mapping. No implicit retries, Checkpoint actions or
    boolean-to-process-exit conversion are performed. Use a native Checkpoint
    directly if all definitions share compatible parameters and require actions.
    """
    definitions = tuple(definitions)
    _validate_targets(
        definitions,
        batch_parameters=batch_parameters,
        expectation_parameters=expectation_parameters,
    )
    if run_id is None:
        run_id = RunIdentifier(run_time=datetime.now(UTC))
    results = {}
    for index, definition in enumerate(definitions):
        stem = validation_artifact_stem(index, definition.name)
        suite_path = Path(suite_directory) / f"{stem}.suite.json"
        save_suite(definition.suite, suite_path)
        results[definition.name] = definition.run(
            batch_parameters=dict((batch_parameters or {}).get(definition.name, {})),
            expectation_parameters=dict((expectation_parameters or {}).get(definition.name, {})),
            run_id=run_id,
            result_format=result_format,
        )
        if result_directory is not None:
            save_result(results[definition.name], Path(result_directory) / f"{stem}.json.gz")
    return results
