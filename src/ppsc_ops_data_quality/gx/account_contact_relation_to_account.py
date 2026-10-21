"""Account references, evaluated at ACR row grain without multiplying children."""

import great_expectations as gx

_EVIDENCE = {
    "sources": [{"kind": "pilot_contract", "path": "docs/sources.md"}],
    "violation_grain": "selected ACR row",
    "assumptions": [
        "Account and ACR states share the same declared effective selection.",
        "The parent population is complete for the applicable ACR references.",
        "Every selected ACR requires one Account reference; no business exclusions are applied.",
    ],
}


def build_suite() -> gx.ExpectationSuite:
    """Keep invalid keys, absent parents, and ambiguous parents separate."""
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
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query=(
                    "SELECT * FROM {batch} WHERE account_id IS NULL OR TRIM(account_id) = ''"
                ),
                description="Each selected ACR has a non-null, nonblank Account reference.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account_contact_relation_to_account.reference.required",
                    "rationale": "A missing key cannot identify the expected Account.",
                    "investigation": "Inspect the source AccountId and reference mapping.",
                },
            ),
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query=(
                    "SELECT * FROM {batch} WHERE account_id IS NOT NULL "
                    "AND TRIM(account_id) <> '' AND matching_account_versions = 0"
                ),
                description="Each nonblank ACR reference exists in the selected Account state.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account_contact_relation_to_account.parent.exists",
                    "rationale": "A populated key should resolve to an eligible Account.",
                    "investigation": "Check parent coverage, completed loads, and state timing.",
                },
            ),
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query=(
                    "SELECT * FROM {batch} WHERE account_id IS NOT NULL "
                    "AND TRIM(account_id) <> '' AND matching_account_versions > 1"
                ),
                description="Each nonblank ACR reference resolves to at most one Account version.",
                meta={
                    **_EVIDENCE,
                    "rule_id": "account_contact_relation_to_account.parent.unambiguous",
                    "rationale": "Duplicate parents make one child reference ambiguous.",
                    "investigation": "Inspect duplicate Accounts and effective interval overlaps.",
                },
            ),
        ],
    )
