"""AccountContactRelation identity in the explicitly selected state."""

import great_expectations as gx

from . import sql_expectations

_EVIDENCE = {
    "sources": [{"kind": "pilot_contract", "path": "docs/sources.md"}],
    "assumptions": ["The batch represents one declared AccountContactRelation state."],
}


def build_suite(relations: dict[str, str] | None = None) -> gx.ExpectationSuite:
    """Keep structural validation native; discover one SQL check per file."""
    return gx.ExpectationSuite(
        name="account_contact_relation",
        expectations=[
            gx.expectations.ExpectTableColumnsToMatchSet(
                column_set=[
                    "id",
                    "account_id",
                    "valid_from",
                    "valid_to",
                    "is_current",
                    "loaded_at",
                ],
                exact_match=False,
                description="The ACR batch includes its identity, reference, and temporal columns.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account_contact_relation.columns",
                    "rationale": "The selected batch must expose the fields its checks use.",
                    "violation_grain": "batch",
                    "investigation": "Compare the batch projection with the verified bindings.",
                },
            ),
            *sql_expectations("account_contact_relation", relations),
        ],
    )
