-- Nullable validation-input profile; deployed catalog types require verification.
CREATE TABLE survey_results (
  `Id` STRING,
  `Participant__c` STRING,
  `Survey_Index_Number__c` STRING,
  `Completion_Status__c` STRING,
  `Consent_Status__c` STRING,
  `Consent_Revoked__c` BOOLEAN,
  `Completion_Status_Timestamp__c` TIMESTAMP,
  `Consent_Status_Timestamp__c` TIMESTAMP,
  `California_Signature__c` TIMESTAMP
);
