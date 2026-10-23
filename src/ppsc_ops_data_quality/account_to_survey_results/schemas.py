"""Derived schemas inferred from the real Ibis expressions, without execution.

These constants describe the supplied validation-input profile. Query parameters
below are symbolic typed values used only to build expression schemas. No survey
event or execution date is invented, no SQL is executed and no views are created.

For another catalog schema or a custom projection, use that relation's .schema()
directly. A published view has its defining query's schema. These inferred values
are useful to bind subsequent reads, but are not independent drift assertions.
"""

import ibis

from ppsc_ops_data_quality.account_to_survey_results.queries import (
    add_flow_context,
    expected_account_values,
    expected_survey_rollups,
    flow_account_comparison,
    join_account,
    rollup_account_comparison,
)
from ppsc_ops_data_quality.core.schemas.account import ACCOUNT_HISTORY_VALIDATION_INPUT
from ppsc_ops_data_quality.core.schemas.contact import CONTACT_HISTORY_VALIDATION_INPUT
from ppsc_ops_data_quality.core.schemas.survey_results import SURVEY_RESULT_HISTORY_VALIDATION_INPUT

_Account = ibis.table(ACCOUNT_HISTORY_VALIDATION_INPUT, name="AccountSnapshot")
_Contact = ibis.table(CONTACT_HISTORY_VALIDATION_INPUT, name="ContactSnapshot")
_Survey_Result__c = ibis.table(SURVEY_RESULT_HISTORY_VALIDATION_INPUT, name="SurveyResultSnapshot")

_JoinedRecord = join_account(_Survey_Result__c, _Contact, _Account)
JOINED_SURVEY_ACCOUNT_RECORD = _JoinedRecord.schema()

_FlowRecord = add_flow_context(_JoinedRecord, _Survey_Result__c, flow_run_date=ibis.param("date"))
FLOW_EXECUTION_RECORD = _FlowRecord.schema()

_ExpectedAccount = expected_account_values(_FlowRecord)
EXPECTED_ACCOUNT_BY_SURVEY_EVENT = _ExpectedAccount.schema()

_AccountAfterBySurveyEvent = _Account.mutate(survey_result_id=ibis.param("string"))
OBSERVED_ACCOUNT_AFTER_BY_SURVEY_EVENT = _AccountAfterBySurveyEvent.schema()

_ExpectedRollups = expected_survey_rollups(_Account, _Survey_Result__c)
EXPECTED_ACCOUNT_SURVEY_ROLLUPS = _ExpectedRollups.schema()

FLOW_ACCOUNT_COMPARISON = flow_account_comparison(_FlowRecord, _AccountAfterBySurveyEvent).schema()
ROLLUP_ACCOUNT_COMPARISON = rollup_account_comparison(
    _Account, _Survey_Result__c, _Account
).schema()
