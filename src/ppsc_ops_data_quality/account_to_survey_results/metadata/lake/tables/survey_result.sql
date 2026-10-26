-- Schema-only PROVISIONAL FIXTURE, not a captured lake definition. Not deployable.
CREATE EXTERNAL TABLE `survey_results_history` (
  `id` string,
  `participant__c` string,
  `survey_index_number__c` string,
  `completion_status__c` string,
  `consent_status__c` string,
  `consent_revoked__c` boolean,
  `completion_status_timestamp__c` timestamp,
  `consent_status_timestamp__c` timestamp,
  `california_signature__c` timestamp,
  `valid_from` timestamp,
  `valid_to` timestamp,
  `is_current` boolean,
  `loaded_at` timestamp
);
