-- A uniquely resolved Contact with a populated AccountId resolves to a selected Account.
-- Source: docs/sources.md (pinned relationship metadata and authored pilot contract).
-- Grain: one selected Survey Result row, including repeated records.
-- Investigate the failing hop and completed-delivery coverage before changing data.
SELECT * FROM batch
WHERE matching_contact_versions = 1 AND missing_account_references = 0 AND matching_account_versions = 0
