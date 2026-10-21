-- Each selected Survey Result has a non-null, nonblank Participant__c reference.
-- Source: docs/sources.md (pinned relationship metadata and authored pilot contract).
-- Grain: one selected Survey Result row, including repeated records.
-- Investigate the failing hop and completed-delivery coverage before changing data.
SELECT * FROM batch
WHERE participant_id IS NULL OR TRIM(participant_id) = ''
