"""Survey Result identity in the selected state."""

from . import make_suite


def build_suite(relations: dict[str, str] | None = None):
    return make_suite(
        "survey_result",
        ["id", "participant_id", "valid_from", "valid_to", "is_current", "loaded_at"],
        relations,
    )
