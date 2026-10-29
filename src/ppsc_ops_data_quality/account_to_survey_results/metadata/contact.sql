-- Provisional offline lake profile; not native type evidence.
CREATE TABLE `fixture_catalog`.`fixture_lake`.`contact_history` (
  `id` STRING,
  `accountid` STRING,
  `birthdate` DATE,
  `valid_from` TIMESTAMP,
  `valid_to` TIMESTAMP,
  `is_current` BOOLEAN,
  `loaded_at` TIMESTAMP
);
