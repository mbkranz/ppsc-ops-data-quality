"""Survey Result → Contact → Account integrity at Survey Result row grain."""

from . import make_suite


def build_suite(relations: dict[str, str] | None = None):
    return make_suite(
        "survey_result_to_account",
        [
            "id",
            "participant_id",
            "matching_contact_versions",
            "missing_account_references",
            "matching_account_versions",
        ],
        relations,
        assumptions=(
            "Survey_Result__c.Participant__c → Contact.Id; Contact.AccountId → Account.Id.",
            "All three sources share the effective selection and physical snapshot timestamp.",
            "Selected Contact and Account populations are complete for the selected surveys.",
            "Each selected survey requires a participant and Account; no exclusions apply.",
            "An Account may have zero or many surveys; there is no reverse existence rule.",
        ),
    )
