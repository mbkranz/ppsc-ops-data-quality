-- Each populated Participant__c resolves to at most one selected Contact version.
-- Source: docs/sources.md (pinned relationship metadata and authored pilot contract).
-- Grain: one selected Survey Result row, including repeated records.
-- Investigate the failing hop and completed-delivery coverage before changing data.
SELECT * FROM batch
WHERE participant_id IS NOT NULL AND TRIM(participant_id) <> '' AND matching_contact_versions > 1
