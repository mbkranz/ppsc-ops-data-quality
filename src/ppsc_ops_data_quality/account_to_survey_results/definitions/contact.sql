-- Provisional synthetic schema profile; not deployable storage DDL.
CREATE EXTERNAL TABLE `contact_history` (
  `id` STRING,
  `accountid` STRING,
  `birthdate` DATE,
  `valid_from` TIMESTAMP,
  `valid_to` TIMESTAMP,
  `is_current` BOOLEAN,
  `loaded_at` TIMESTAMP
);
