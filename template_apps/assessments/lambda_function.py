"""
    - Include all dependencies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import os
import json
import traceback
import requests

# Include response_objects and BaseAdapter
import response_objects
from base_adapter import BaseAdapter

# Optional: implement an Adapter for your system/ third-party system so that it is easier to replace implementations in the future. 
class AssessmentAdapter(BaseAdapter):
    def __init__(self, app_settings):
        """
            Initialize any attributes required for setting up the adapter such as app settings - API base URL, credential validation, class properties, etc.
            An example is shown below. 
        """
        self.api_key = app_settings.get('api_key')

    def get_logo_url(self):
        """
            Return a URL pointing to your assessment system's logo
        """
        return ''

    def is_webhook_supported(self):
        """
            Return a boolean depending on your use case.
        """
        return False

    def list_tests(self):
        """
            - Fetch assessments from your system
            - Instantiate and return response_objects.AssessmentTestType objects for each assessment returned
            An example with hardcoded data is listed below. In your application, this may be an API call to your system or a third party system where the assesments are listed.
        """
        tests = [
            {
                'test_id': '8129',
                'assessment_name': 'Sample Test 1',
            }
        ]
        return [
            response_objects.AssessmentTestType(
                test_id=test.get('test_id'),
                name=test.get('assessment_name'),
                published=True,
            ).to_dict()
            for test in tests
        ]

    def invite_candidate(self, test_id, invite_metadata):
        """
            - Send the specified test to the selected candidate, using any metadata provided that your system requires
            - Instantiate a response_objects.AssessmentInviteCandidateResponseType object and set the properties
            - Return the object as a dictionay

            An example is provided below
        """
        return response_objects.AssessmentInviteCandidateResponseType(
            email=invite_metadata.get('email'),
            invite_already_sent=True,
            assessment_id='1234',
            vendor_candidate_id='1234'
        ).to_dict()

    def fetch_candidate_report(self, test_id):
        """
           	- Fetch an assessment report for a specific candidate's assessment instance	
            - Instantiate response_objects.ApplicationAssessmentData and set the properties as needed
            - Return the object as a dict

            Example provided below
        """
        report = response_objects.ApplicationAssessmentData()
        report.report_url = 'https://your-assessment-system.com'
        report.status = 'completed'
        return report.to_dict()

"""
    - Provide an entry point function for your app. This is the event handler that handles different triggers that are invoked in the Eightfold system.
    - In this function, accept two arguments -> event and context.
    - The event argument will contain all needed params to properly invoke your app.
    - Instantiate an instance of your implemented BaseAdapter.
    - Invoke the correct function on your Adapter object based on which trigger was sent in request_data
"""
def app_handler(event, context):
 
    # Extract request_data -> this is the dynamic, per-invocation data for your app. E.g. profile info, message to be sent, etc.
    request_data = event.get('request_data', {})

    # Extract app_settings -> this are the static params for your app configured for each unique installation. E.g. API keys, allow/deny lists, etc.
    app_settings = event.get('app_settings', {})

    Adapter = AssessmentAdapter(app_settings)

    trigger_name = request_data.get('trigger_name')

    data = None
    """
        Handle different triggers. Note that you do not need to use all the triggers listed below. Read the doc here to understand what  each trigger does
        and in your app, implement the triggers that fit your use case: https://docs.eightfold.ai/trigger-guides/assessment-triggers#Get_Candidate_Report_trigger
    """
    try:
        if trigger_name == 'assessment_get_logo_url':
            data = Adapter.get_logo_url()
        elif trigger_name == 'assessment_is_webhook_supported':
            data = Adapter.is_webhook_supported()
        elif trigger_name == 'assessment_list_tests':
            data = Adapter.list_tests()
        elif trigger_name == 'assessment_invite_candidate':
            test_id = request_data.get('test_id')
            invite_metadata = request_data.get('invite_metadata')
            data = Adapter.invite_candidate(test_id, invite_metadata)
        elif trigger_name == 'assessment_fetch_candidate_report':
            test_id = request_data.get('test_id')
            data = Adapter.fetch_candidate_report(test_id)
        else:
            raise ValueError('Unsupported trigger name.')
    except Exception as e:
        err_msg = 'Handler for trigger_name: {} failed with error: {}, traceback: {}'.format(
            trigger_name, str(e), traceback.format_exc())
        print(err_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(e),
                'stacktrace': traceback.format_exc(),
            }),
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
