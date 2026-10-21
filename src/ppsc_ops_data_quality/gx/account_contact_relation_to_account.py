"""Account references at child-row grain, including missing and duplicate parents."""

from . import make_suite


def build_suite(relations: dict[str, str] | None = None):
    return make_suite(
        "account_contact_relation_to_account",
        ["id", "account_id", "matching_account_versions"],
        relations,
        assumptions=(
            "Account and ACR share the same effective selection and physical snapshot timestamp.",
            "The eligible parent population is complete for the selected references.",
            "Every selected ACR requires an Account reference; no business exclusions apply.",
        ),
    )
