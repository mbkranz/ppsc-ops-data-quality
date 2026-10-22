"""Serialize the actual native GX suite used by a validation definition."""

import gzip
import json
import re
from pathlib import Path

import great_expectations as gx
from great_expectations.core import ExpectationSuiteValidationResult


def validation_artifact_stem(index: int, name: str) -> str:
    """Use the sequence to disambiguate names that sanitize to the same label."""
    label = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")[:100]
    return f"{index:03d}_{label or 'validation'}"


def save_result(result: ExpectationSuiteValidationResult, path: str | Path) -> Path:
    """Archive native GX JSON as one UTF-8 JSON line in a gzip file.

    The decoded object is exactly result.to_json_dict(); no envelope or field
    normalization is added. This is an audit copy, not a GX ValidationResultsStore.
    Refuse overwrite. Compression has a deterministic header for reproducibility.
    """
    payload = (
        json.dumps(
            result.to_json_dict(), ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
        + "\n"
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as output:
        output.write(gzip.compress(payload.encode("utf-8"), mtime=0))
    return destination


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
