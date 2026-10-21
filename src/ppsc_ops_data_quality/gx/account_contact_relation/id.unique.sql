-- An ACR identifier occurs at most once in the selected state.
-- Source: docs/sources.md (pilot contract; not yet live acceptance).
-- Each selected relationship needs a distinct identity.
-- selected ACR row
-- Inspect source duplicates and effective interval selection.
SELECT * FROM {batch} WHERE id IN (SELECT id FROM {batch} GROUP BY id HAVING COUNT(*) > 1)
