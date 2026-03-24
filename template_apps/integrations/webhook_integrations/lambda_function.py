# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import os
import json

import requests
from ef_app_sdk import EFAppSDK


"""
    - The entry point function for your app.
    - The context arg can be ignored completely
    - The event arg will contain all needed params to properly invoke your app
"""

def app_handler(event, context):
    # Extract request_data -> this is the dynamic, per-invocation data for your app.
    req_data = event.get('request_data', {})
    # Extract app_settings -> this are the static params for your app configured for each unique installation.
    # E.g. API keys, allow/deny lists, etc.
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    ef_sdk = EFAppSDK(context)

    # To add a message to log, call ef_sdk.log(msg=<msg>) method
    ef_sdk.log(f'Call received for trigger_name: {trigger_name}')
    data = {}
    if trigger_name == 'webhook_receive_event':
        # Request and response type for this trigger has been defined at
        # https://docs.eightfold.ai/trigger-guides/webhook-event-trigger-guide
        req_payload = req_data.get('request_payload', {})
        # extract the entity_type from req_payload and map it one of entity_types ('candidate', 'position') supported by Eightfold.

        # Extract the entity_id, and other fields from request payload and use API server to post/patch the entity.
        # For candidate create, post to url (https://apiv2.eightfold.ai/api/v2/core/ats-systems/systemId/ats-candidates);
        # ref: https://apidocs.eightfold.ai/v2.0/reference/create_ats_candidate
        # For candidate patch, patch to url (https://apiv2.eightfold.ai/api/v2/core/ats-systems/systemId/ats-candidates/atsCandidateId);
        # ref https://apidocs.eightfold.ai/v2.0/reference/patch_ats_candidate
        # For position create, post to url (https://apiv2.eightfold.ai/api/v2/core/ats-systems/systemId/ats-positions);
        # ref https://apidocs.eightfold.ai/v2.0/reference/create_ats_position
        # For position patch, patch to url (https://apiv2.eightfold.ai/api/v2/core/ats-systems/systemId/ats-positions/atsPositionId);
        # ref https://apidocs.eightfold.ai/v2.0/reference/patch_ats_position
    elif trigger_name ==  ['schedule_hourly']:
        # Fetch the open positions from remote system and use position post to create/update the position.
        # Fetch the list of candidates modified in last hour or (X hours to account for failure) and use ats candidate post to
        # create/update the candidate
        #
        # To make a remote http call, call ef_sdk.call_http_method()
        # Uses:
        # ef_sdk.call_http_method(
        #   http_method='GET',
        #   **kwargs)
        # kwargs: The necessary keyword arguments for the HTTP request being made
        # The above call helps Eightfold tracks the request and response details for the http calls that are being made from the app.
        # This will help Eightfold in debugging the issue in case of failures.
        #
        # For candidate create/update, post to url (https://apiv2.eightfold.ai/api/v2/core/ats-systems/systemId/ats-candidates);
        # ref: https://apidocs.eightfold.ai/v2.0/reference/create_ats_candidate
        # For position create/update, post to url (https://apiv2.eightfold.ai/api/v2/core/ats-systems/systemId/ats-positions);
        # ref https://apidocs.eightfold.ai/v2.0/reference/create_ats_position
    elif trigger_name in ['application_create', 'application_update']:
        # Request and response type for this trigger has been defined at
        # https://docs.eightfold.ai/trigger-guides/core-component-triggers
        # You can request for previous fields value, by adding fields in request_fields_previous in 
        # the app_settings. for  ex:
        # request_fields_previous: [
        #   "currentStage",
        #   "lastModifiedTime",
        #   "sourceType"
        # ]
        # This makes sure request_data has both current fields value as well as past field value prior to the update/create
        # request_data.previous.currentStage will have the value prior to the update 
        # If there is a currentStage change in the application and it matches with app_settings.get('notification_stage')
        # you can push the application update to remote system, where app_settings.get('notification_stage') denotes the stage
        # at which application should be pushed to remote system.
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'unsupported trigger ' + trigger_name
            })
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
