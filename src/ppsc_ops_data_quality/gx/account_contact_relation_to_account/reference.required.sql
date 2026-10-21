-- Each selected ACR has a non-null, nonblank Account reference.
-- Source: docs/sources.md (pilot contract; not yet live acceptance).
-- A missing key cannot identify the expected Account.
-- Inspect the source AccountId and reference mapping.
SELECT * FROM {batch} WHERE account_id IS NULL OR TRIM(account_id) = ''
