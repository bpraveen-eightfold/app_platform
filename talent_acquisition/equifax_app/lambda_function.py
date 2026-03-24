from __future__ import absolute_import

import json
import pytz
import traceback
import requests
from datetime import datetime
from ef_app_sdk import EFAppSDK


def format_response(status_code, data):
    """
    Formats the response with the given status code and data.
    """
    return {
        'statusCode': status_code,
        'body': json.dumps({'data': data})
    }

def error_response(error_code, error_str, app_sdk=None):
    """
    Generates an error response with the given error code and error string.
    """
    data = {'error': error_str, 'error_code': error_code}
    app_sdk.log(json.dumps(data))
    return format_response(error_code, data)

def success_response(data):
    """
    Generates a success response with the given data.
    """
    return format_response(200, data)

def get_oauth_token(client_id, client_secret, base_url, scope):
    """
    Gets OAuth token from Equifax API
    """
    data = {
        'grant_type': 'client_credentials',
        'scope': scope,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(f'{base_url}/oauth/token', data=data, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get OAuth token: {response.text}")
    
    return response.json().get('access_token')

def get_logo_url(app_sdk=None):
    """
    Returns the Equifax logo URL (static)
    """
    logo_url = 'https://www.equifax.com/favicon.ico'
    data = {'logo_url': logo_url}
    app_sdk.log(f'Equifax Logo URL is: {data}')
    return success_response(data)

def list_tests(request_data={}, app_settings={}, app_sdk=None):
    """
    Returns list of available background check packages (static)
    """
    if not request_data or not app_settings:
        return error_response(400, 'request_data or app_settings cannot be empty', app_sdk)

    # Static package list from app_settings
    packages = app_settings.get('background_check_packages', [
        {
            'duration_minutes': '',
            'id': 'STANDARD',
            'name': 'Standard Background Check',
            'published': True
        },
        {
            'duration_minutes': '',
            'id': 'PREMIUM',
            'name': 'Premium Background Check',
            'published': True
        }
    ])

    app_sdk.log(f'Available packages: {packages}')
    return success_response(packages)

def invite_candidate(request_data={}, app_settings={}, app_sdk=None):
    app_sdk.log(f'Invite candidate request data: {request_data}')
    """
    Initiates a background check for a candidate
    """
    if not request_data or not app_settings:
        return error_response(400, 'request_data or app_settings cannot be empty', app_sdk)

    try:
        # Get OAuth token
        oauth_token = get_oauth_token(
            app_settings.get('client_id'),
            app_settings.get('client_secret'),
            app_settings.get('oauth_base_url'),
            app_settings.get('oauth_scope')
        )

        # Extract candidate information
        invite_metadata = request_data.get('invite_metadata', {})
        first_name = request_data.get('firstname')
        last_name = request_data.get('lastname')
        email = invite_metadata.get('email')
        test_id = invite_metadata.get('test_id')
        profile_id = invite_metadata.get('profile_id')
        pid = invite_metadata.get('pid')
        ats_candidate_id = invite_metadata.get('ats_candidate_id')

        # Create product request payload
        payload = {
            "packetTemplateInformation": {
                "packetTemplateId": test_id
            },
            "packetEmployerInformation": {
                "employerCode": app_settings.get('employer_code'),
                "externalEmployerId": app_settings.get('employer_code')
            },
            "startDate": datetime.now().strftime("%m/%d/%Y"),
            "language": "EN",
            "i9Anywhere": False,
            "sendSMS": True,
            "location": {
                "locationCode": "Default"
            },
            "personalInformation": {
                "firstName": first_name,
                "lastName": last_name,
                "email": email
            },
            "extendedFields": [
                {
                    "fieldName": "AltPersonID",
                    "fieldValue": profile_id
                },
                {
                    "fieldName": "pid",
                    "fieldValue": pid
                }
            ],
            "metadata": {
                "email": email,
                "username": email
            }
        }

        # Make API request to create product request
        headers = {
            'Authorization': f'Bearer {oauth_token}',
            'Content-Type': 'application/json'
        }
        app_sdk.log(f'Equifax payload: {payload}')
        response = requests.post(
            f"{app_settings.get('base_url')}/v1/employers/product-requests",
            json=payload,
            headers=headers
        )
        app_sdk.log(f'Equifax response: {response.status_code}')
        if response.status_code != 201:
            return error_response(response.status_code, f"Failed to create product request: {response.text}", app_sdk)

        return success_response({
            'assessment_id': "",
            'invite_already_sent': False,
            'email': email,
            'test_url': "",
            'vendor_candidate_id': ats_candidate_id
        })

    except Exception as e:
        app_sdk.log(f"Error in invite_candidate: {str(e)}")
        return error_response(500, str(e), app_sdk)

def is_webhook_supported(app_sdk=None):
    """
    Indicates whether webhooks are supported
    """
    return success_response({'is_webhook_supported': 'true'})

def map_form_status_to_assessment_status(form_status):
    """
    Maps Equifax form status to assessment status
    """
    status_mapping = {
        'COMPLETED': 'completed',
        'IN_PROGRESS': 'in_progress',
        'PENDING': 'pending',
        'ERROR': 'error'
    }
    return status_mapping.get(form_status, 'unknown')

def convert_local_time_to_utc_timestamp(local_time, webhook_timezone):
    """
    Converts local time to UTC timestamp
    """
    timezone_obj = pytz.timezone(webhook_timezone)
    local_time = timezone_obj.localize(datetime.strptime(local_time, '%Y-%m-%d %H:%M:%S'))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp())

def handle_webhook_event(request_data={}, app_settings={}, app_sdk=None):
    """
    Handles webhook notifications from Equifax
    """
    if not request_data or not app_settings:
        return error_response(400, 'request_data or app_settings cannot be empty', app_sdk)

    webhook_timezone = app_settings.get('webhook_timezone')
    try:
        webhook_payload = request_data.get('request_payload')
        app_sdk.log(f'Webhook payload: {webhook_payload}')

        form_status = webhook_payload.get('formStatus')
        form_type = webhook_payload.get('formType')
        packet_id = webhook_payload.get('packetId')
        person_id = webhook_payload.get('personId')
        employer_code = webhook_payload.get('employerCode')
        timestamp = webhook_payload.get('timeStamp')
        email = webhook_payload.get('email')
        pid = webhook_payload.get('pid')

        unix_timestamp = convert_local_time_to_utc_timestamp(timestamp, webhook_timezone)

        assessment_status = map_form_status_to_assessment_status(form_status)

        response_data = {
            'stacktrace': '',
            'actions': [{
                'action_name': 'save_assessment_to_profile_data',
                'request_data': {
                    'invite_metadata': {
                        'email': email,
                        'profile_id': person_id,
                        'pid': pid,
                        'employer_code': employer_code,
                        "test_id": "STANDARD"
                    },
                    'assessment_report': {
                        'status': assessment_status,
                        'vendor_report_status': form_status,
                        'assigned_ts': None,
                        'start_ts': None,
                        'completed_ts': unix_timestamp if form_status == 'COMPLETED' else None,
                        'comments': f'Form {form_type} status: {form_status}',
                        'response_json': webhook_payload,
                        'vendor_status': form_status,
                        "test_id": "STANDARD"
                    }
                }
            }],
            'is_success': True,
            'error': False
        }

        return success_response(response_data)

    except Exception as e:
        app_sdk.log(f"Error in handle_webhook_event: {str(e)}")
        return error_response(500, str(e), app_sdk)

def app_handler(event, context):
    """
    Main handler for the Lambda function
    """
    app_sdk = EFAppSDK(context)
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    app_sdk.log(f'Trigger name is {trigger_name}')

    try:
        if trigger_name == 'assessment_get_logo_url':
            return get_logo_url(app_sdk)
        elif trigger_name == 'assessment_list_tests':
            return list_tests(request_data, app_settings, app_sdk)
        elif trigger_name == 'assessment_invite_candidate':
            return invite_candidate(request_data, app_settings, app_sdk)
        elif trigger_name == 'assessment_is_webhook_supported':
            return is_webhook_supported(app_sdk)
        elif trigger_name == 'webhook_receive_event':
            return handle_webhook_event(request_data, app_settings, app_sdk)
        else:
            return error_response(400, 'Unknown trigger name', app_sdk)
    except Exception as e:
        error_str = 'Something went wrong, traceback: {}'.format(traceback.format_exc())
        app_sdk.log(json.dumps({'error_str': error_str}))
        app_sdk.log(f'Unable to handle equifax error: {e}')
        return error_response(500, error_str, app_sdk)
