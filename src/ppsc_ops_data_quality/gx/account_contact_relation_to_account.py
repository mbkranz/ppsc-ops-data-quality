"""Account references, evaluated at ACR row grain without multiplying children."""

import great_expectations as gx

from . import sql_expectations

_EVIDENCE = {
    "sources": [{"kind": "pilot_contract", "path": "docs/sources.md"}],
    "violation_grain": "selected ACR row",
    "assumptions": [
        "Account and ACR states share the same declared effective selection.",
        "The parent population is complete for the applicable ACR references.",
        "Every selected ACR requires one Account reference; no business exclusions are applied.",
    ],
}


def build_suite(relations: dict[str, str] | None = None) -> gx.ExpectationSuite:
    """Keep structural validation native; discover one SQL check per file."""
    return gx.ExpectationSuite(
        name="account_contact_relation_to_account",
        expectations=[
            gx.expectations.ExpectTableColumnsToMatchSet(
                column_set=["id", "account_id", "matching_account_versions"],
                exact_match=False,
                description="The relationship batch retains child identity and parent counts.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account_contact_relation_to_account.columns",
                    "rationale": "The batch must retain the information needed to explain a match.",
                    "violation_grain": "batch",
                    "investigation": "Inspect the relationship batch projection.",
                },
            ),
            *sql_expectations("account_contact_relation_to_account", relations),
        ],
    )
