"""Detached source evidence, supplied explicitly by domain orchestration."""

from .metadata import metadata_inputs

_inputs = metadata_inputs()
ACCOUNT_FIELD_LINEAGE = _inputs.lineage["ACCOUNT_FIELD_LINEAGE"]
PROJECTION_LINEAGE = _inputs.lineage["PROJECTION_LINEAGE"]
BRANCH_LINEAGE = _inputs.lineage["BRANCH_LINEAGE"]
FLOW_ENTITY_LINEAGE = _inputs.lineage["FLOW_ENTITY_LINEAGE"]
ROLLUP_FIELD_LINEAGE = {
    key: value
    for key, value in PROJECTION_LINEAGE.items()
    if value.get("entity_type") == "AccountRollup" and key.startswith("expected__")
}
# Preserve the domain's original keyed rollup names, without reinterpreting source metadata.
ROLLUP_FIELD_LINEAGE = {
    "Account." + key.removeprefix("expected__"): value
    for key, value in ROLLUP_FIELD_LINEAGE.items()
}
