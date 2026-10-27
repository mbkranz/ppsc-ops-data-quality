-- Nullable validation-input profile; deployed catalog types require verification.
CREATE TABLE history (
  `valid_from` TIMESTAMP,
  `valid_to` TIMESTAMP,
  `is_current` BOOLEAN,
  `loaded_at` TIMESTAMP
);
