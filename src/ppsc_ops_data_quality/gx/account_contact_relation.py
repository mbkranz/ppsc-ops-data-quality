"""AccountContactRelation identity in the selected state."""

from . import make_suite


def build_suite(relations: dict[str, str] | None = None):
    return make_suite(
        "account_contact_relation",
        ["id", "account_id", "valid_from", "valid_to", "is_current", "loaded_at"],
        relations,
    )
