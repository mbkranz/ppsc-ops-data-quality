"""Serialize the actual native GX suite used by a validation definition."""

import json
from pathlib import Path

import great_expectations as gx


def save_suite(suite: gx.ExpectationSuite, path: str | Path) -> Path:
    """Write native GX suite JSON, preserving expectations, IDs and metadata.

    Provenance: ExpectationSuite.to_json_dict(). The input is the registered suite
    attached to the Validation Definition, after builder arguments such as source
    row counts have been applied. This does not rebuild the suite or mutate it.
    GX $PARAMETER placeholders remain symbolic; record their runtime values in
    the run metadata separately. No dataframe or connection configuration is saved.

    Existing files are rejected so another run's audit snapshot is not replaced.
    Serialization and I/O errors propagate before that definition is evaluated.
    Reload with gx.ExpectationSuite(**json.loads(path.read_text())).
    """
    payload = json.dumps(suite.to_json_dict(), indent=2, ensure_ascii=False, allow_nan=False)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as output:
        output.write(payload + "\n")
    return destination
