-- Provisional synthetic schema profile; not deployable storage DDL.
CREATE EXTERNAL TABLE `survey_results_history` (
  `id` STRING,
  `participant__c` STRING,
  `survey_index_number__c` STRING,
  `completion_status__c` STRING,
  `consent_status__c` STRING,
  `consent_revoked__c` BOOLEAN,
  `completion_status_timestamp__c` TIMESTAMP,
  `consent_status_timestamp__c` TIMESTAMP,
  `california_signature__c` TIMESTAMP,
  `valid_from` TIMESTAMP,
  `valid_to` TIMESTAMP,
  `is_current` BOOLEAN,
  `loaded_at` TIMESTAMP
);
