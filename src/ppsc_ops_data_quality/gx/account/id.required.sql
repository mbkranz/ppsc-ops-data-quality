-- Each selected Account row has an identifier.
-- Source: docs/sources.md (pilot contract; not yet live acceptance).
-- An absent identifier prevents reliable record linkage.
-- selected Account row
-- Inspect the source identifier and its extraction mapping.
SELECT * FROM {batch} WHERE id IS NULL
