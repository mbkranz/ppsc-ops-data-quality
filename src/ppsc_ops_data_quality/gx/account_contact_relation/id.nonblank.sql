-- Each non-null ACR identifier contains nonblank text.
-- Source: docs/sources.md (pilot contract; not yet live acceptance).
-- Empty identifiers cannot serve as record identities.
-- selected ACR row
-- Inspect empty or space-only identifiers without fixing them.
SELECT * FROM batch WHERE id IS NOT NULL AND TRIM(id) = ''
