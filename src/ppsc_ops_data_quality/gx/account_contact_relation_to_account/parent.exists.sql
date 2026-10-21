-- Each nonblank ACR reference exists in the selected Account state.
-- Source: docs/sources.md (pilot contract; not yet live acceptance).
-- A populated key should resolve to an eligible Account.
-- Check parent coverage, completed loads, and state timing.
SELECT * FROM {batch} WHERE account_id IS NOT NULL AND TRIM(account_id) <> '' AND matching_account_versions = 0
