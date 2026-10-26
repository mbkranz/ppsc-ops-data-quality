-- Schema-only PROVISIONAL FIXTURE, not a captured lake definition. Not deployable.
CREATE EXTERNAL TABLE `contact_history` (
  `id` string,
  `accountid` string,
  `birthdate` date,
  `valid_from` timestamp,
  `valid_to` timestamp,
  `is_current` boolean,
  `loaded_at` timestamp
);
