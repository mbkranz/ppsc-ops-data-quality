"""Account identity in the explicitly selected state."""

import great_expectations as gx

_EVIDENCE = {
    "sources": [{"kind": "pilot_contract", "path": "docs/sources.md"}],
    "assumptions": ["The batch represents one declared Account state."],
}


def build_suite() -> gx.ExpectationSuite:
    """Build structural checks without a connection or physical table binding."""
    return gx.ExpectationSuite(
        name="account",
        expectations=[
            gx.expectations.ExpectTableColumnsToMatchSet(
                column_set=["id", "valid_from", "valid_to", "is_current", "loaded_at"],
                exact_match=False,
                description="The Account batch includes its identity and temporal columns.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account.columns",
                    "rationale": "The selected batch must expose the fields its checks use.",
                    "violation_grain": "batch",
                    "investigation": "Compare the batch projection with the verified bindings.",
                },
            ),
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column="id",
                description="Each selected Account row has an identifier.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account.id.required",
                    "rationale": "An absent identifier prevents reliable record linkage.",
                    "violation_grain": "selected Account row",
                    "investigation": "Inspect the source identifier and its extraction mapping.",
                },
            ),
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query=(
                    "SELECT * FROM {batch} WHERE id IS NOT NULL AND TRIM(id) = ''"
                ),
                description="Each non-null Account identifier contains nonblank text.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account.id.nonblank",
                    "rationale": "Empty identifiers cannot serve as record identities.",
                    "violation_grain": "selected Account row",
                    "investigation": "Inspect empty or space-only identifiers without fixing them.",
                },
            ),
            gx.expectations.ExpectColumnValuesToBeUnique(
                column="id",
                description="An Account identifier occurs at most once in the selected state.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account.id.unique",
                    "rationale": "Multiple selected versions make parent references ambiguous.",
                    "violation_grain": "selected Account row",
                    "investigation": "Inspect source duplicates and effective interval selection.",
                },
            ),
        ],
    )
