-- Each nonblank ACR reference resolves to at most one Account version.
-- Source: docs/sources.md (pilot contract; not yet live acceptance).
-- Duplicate parents make one child reference ambiguous.
-- Inspect duplicate Accounts and effective interval overlaps.
SELECT * FROM batch WHERE account_id IS NOT NULL AND TRIM(account_id) <> '' AND matching_account_versions > 1
