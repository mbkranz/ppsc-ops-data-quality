"""AccountContactRelation identity in the explicitly selected state."""

import great_expectations as gx

_EVIDENCE = {
    "sources": [{"kind": "pilot_contract", "path": "docs/sources.md"}],
    "assumptions": ["The batch represents one declared AccountContactRelation state."],
}


def build_suite() -> gx.ExpectationSuite:
    """Build native ACR checks independently of Athena connection configuration."""
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
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column="id",
                description="Each selected ACR row has an identifier.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account_contact_relation.id.required",
                    "rationale": "An absent identifier prevents reliable investigation of a row.",
                    "violation_grain": "selected ACR row",
                    "investigation": "Inspect the source identifier and its extraction mapping.",
                },
            ),
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query=(
                    "SELECT * FROM {batch} WHERE id IS NOT NULL AND TRIM(id) = ''"
                ),
                description="Each non-null ACR identifier contains nonblank text.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account_contact_relation.id.nonblank",
                    "rationale": "Empty identifiers cannot serve as record identities.",
                    "violation_grain": "selected ACR row",
                    "investigation": "Inspect empty or space-only identifiers without fixing them.",
                },
            ),
            gx.expectations.ExpectColumnValuesToBeUnique(
                column="id",
                description="An ACR identifier occurs at most once in the selected state.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account_contact_relation.id.unique",
                    "rationale": "Each selected relationship needs a distinct identity.",
                    "violation_grain": "selected ACR row",
                    "investigation": "Inspect source duplicates and effective interval selection.",
                },
            ),
        ],
    )
