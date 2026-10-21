-- Each selected Survey Result row has an identifier.
-- Source: docs/sources.md (pilot contract; not yet live acceptance).
-- An absent identifier prevents reliable record linkage.
-- selected Survey Result row
-- Inspect the source identifier and its extraction mapping.
SELECT * FROM batch WHERE id IS NULL
