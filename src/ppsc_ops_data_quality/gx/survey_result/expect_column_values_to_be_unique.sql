-- A Survey Result identifier occurs at most once in the selected state.
-- Source: docs/sources.md (pilot contract; not yet live acceptance).
-- Multiple selected versions make record identities ambiguous.
-- selected Survey Result row
-- Inspect source duplicates and effective interval selection.
SELECT * FROM batch WHERE id IN (SELECT id FROM batch GROUP BY id HAVING COUNT(*) > 1)
