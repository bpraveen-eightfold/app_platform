# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import json
from datetime import datetime

from fadv_adapter import FirstAdvantageAdapter
from fadv_constants import FADVConstants
from fadv_data_classes import FADVCandidate, FADVInviteRequest, FADVPackage
from ef_app_sdk import EFAppSDK

"""
    - Provide an entry point function for your app.
    - Your function name must be 'app_handler'
    - Your function must accept two args -> event and context
    - The context arg can be ignored, if you want to use EFAppSDK for improved logging then pass in this value
    - The event arg will contain all needed params to properly invoke your app
"""

def format_response(status_code, data):
    """
    Formats the response with the given status code and data.

    Parameters:
    - status_code (int): The HTTP status code.
    - data (dict): The data to be included in the response body.

    Returns:
    - dict: The formatted response dictionary.
    """
    return {
        'statusCode': status_code,
        'body': json.dumps({'data': data})
    }

def error_response(error_code, error_str, app_sdk=None):
    """
    Generates an error response with the given error code and error string.

    Parameters:
    error_code (int): The error code to be included in the response.
    error_str (str): The error string to be included in the response.
    app_sdk: Instance of EFAppSDK for logging.

    Returns:
    dict: A dictionary containing the error code and error string.

    """
    data = {'error': error_str, 'error_code': error_code}
    if app_sdk:
        app_sdk.log(json.dumps(data))
    return format_response(error_code, data)

def success_response(data):
    """
    Generates a success response with the given data.

    Parameters:
    - data: The data to be included in the response.

    Returns:
    The formatted success response with the given data.
    """
    return format_response(200, data)

def get_logo_url(app_sdk=None):
    """
    Retrieves the logo URL for the talent acquisition app.

    Args:
        app_sdk: Instance of EFAppSDK for logging.
        
    Returns:
        dict: A dictionary containing the logo URL.
    """
    logo_url = 'https://fadv.com/wp-content/uploads/First-Advantage-logo-2024.svg'
    data = {'logo_url': logo_url}
    if app_sdk:
        app_sdk.log(f'First Advantage Logo URL is: {data}')
    return success_response(data)

def list_tests(request_data = {}, app_settings = {}, app_sdk = None):
    """
    Retrieves a list of assessments/tests using API key for authorization.
    Fetches packages from all accounts under the parent account.
    
    Args:
        request_data (dict, optional): The request data. Defaults to {}.
        app_settings (dict, optional): The application settings. Defaults to {}.
        app_sdk: Instance of EFAppSDK for logging.
    
    Returns:
        dict: The list of assessments/tests.
    
    Raises:
        ValueError: If request_data or app_settings is empty.
        ValueError: If the response status code is not 200.
    """
    if not app_settings:
        return error_response(400, 'app_settings cannot be empty', app_sdk)
    
    try:
        # Initialize the adapter
        fadv_adapter = FirstAdvantageAdapter(app_settings, app_sdk)
        
        # Get all packages from all accounts
        all_packages = fadv_adapter.list_all_packages()
        
        return success_response(all_packages)
    except Exception as e:
        if app_sdk:
            app_sdk.log(f"Error in list_tests: {str(e)}")
        return error_response(500, f"Error listing tests: {str(e)}", app_sdk)

def invite_candidate(request_data = {}, app_settings = {}, app_sdk = None):
    """
    Initiates a background check for a candidate using a two-step process:
    1. Create a candidate
    2. Send an invite to the candidate
    
    Args:
        request_data (dict, optional): The request data containing information about the candidate. Defaults to {}.
        app_settings (dict, optional): The application settings. Defaults to {}.
        app_sdk: Instance of EFAppSDK for logging.
    
    Returns:
        dict: The response containing the assessment details including applicant_id.
    """
    if app_sdk:
        app_sdk.log(f'Invite candidate request data: {request_data}')

    if not request_data or not app_settings:
        return error_response(400, 'request_data or app_settings cannot be empty', app_sdk)

    try:
        # Initialize the adapter
        fadv_adapter = FirstAdvantageAdapter(app_settings, app_sdk)
        
        # Extract candidate information
        invite_metadata = request_data.get('invite_metadata', {})
        first_name = request_data.get('firstname')
        last_name = request_data.get('lastname')
        email = invite_metadata.get('email')
        ats_job_id = invite_metadata.get('ats_job_id')
        ats_candidate_id = invite_metadata.get('ats_candidate_id')
        test_id = invite_metadata.get('test_id')
        profile_id = invite_metadata.get('profile_id')
        pid = invite_metadata.get('pid')
        application_id = invite_metadata.get('application_id')
        
        # Extract location information
        location_country = request_data.get('location_country', 'US')
        location_state = request_data.get('location_state', '').split(',')[0] if request_data.get('location_state') else ''
        location_city = request_data.get('location', '')
        
        # Create the candidate
        candidate_data = fadv_adapter.create_candidate(
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        
        candidate_id = candidate_data.get('candidate_id')
        if not candidate_id:
            return error_response(500, 'No candidate_id returned from candidate creation', app_sdk)
        
        # Send the invite
        invite_data = fadv_adapter.invite_candidate(
            email=email,
            application_id=application_id,
            candidate_id=candidate_id,
            package_id=str(test_id),
            profile_id=profile_id,
            pid=pid,
            location_country=location_country,
            location_state=location_state,
            location_city=location_city,
            action_user_email=request_data.get('action_user_email', ''),
            ats_job_id=ats_job_id
        )
        
        # Extract applicant_id from the response
        applicant_id = invite_data.get('applicant_id', '')
        
        return success_response({
            'assessment_id': applicant_id,
            'invite_already_sent': False,
            'email': email,
            'test_url': '',
            'vendor_candidate_id': ats_candidate_id
        })

    except Exception as e:
        if app_sdk:
            app_sdk.log(f"Error in invite_candidate: {str(e)}")
        return error_response(500, str(e), app_sdk)

def handle_webhook_event(request_data = {}, app_settings = {}, app_sdk = None):
    """
    Handles webhook notifications from First Advantage.
    
    Args:
        request_data (dict): The webhook data received.
        app_settings (dict): Application settings.
        app_sdk: Instance of EFAppSDK for logging.
        
    Returns:
        dict: Response with assessment status update information.
    """
    if not request_data or not app_settings:
        return error_response(400, 'request_data or app_settings cannot be empty', app_sdk)

    try:
        # Get the webhook payload
        webhook_payload = request_data.get('request_payload', {})
        if app_sdk:
            app_sdk.log(f'Webhook payload: {webhook_payload}')
        
        # Initialize the adapter
        fadv_adapter = FirstAdvantageAdapter(app_settings, app_sdk)
        
        # Process the webhook using the adapter
        response_data = fadv_adapter.process_webhook(webhook_payload)
        
        return success_response(response_data)
    except Exception as e:
        if app_sdk:
            app_sdk.log(f"Error processing webhook: {str(e)}")
        return error_response(500, f"Error processing webhook: {str(e)}", app_sdk)

def str2bool(value):
    """
    Convert a string value to boolean.

    Args:
        value: The value to convert.

    Returns:
        bool: The converted boolean value.
    """
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', 't', 'yes', 'y', '1')


def check_webhook_support(app_sdk=None):
    """
    Checks if webhook is supported by this application.
    
    Returns:
        dict: Success response indicating webhook support.
    """
    return success_response({'is_webhook_supported': 'true'})

def app_handler(event, context):
    """
    Main handler function for the Lambda function.
    
    Args:
        event (dict): The event data.
        context: The Lambda context.
        
    Returns:
        dict: The response data.
    """
    # Read the event's body into a python dict
    app_sdk = EFAppSDK(context)
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    app_sdk.log(f'Trigger name is {trigger_name}')
    
    try:
        # Route the request to the appropriate handler based on the trigger name
        if trigger_name == 'assessment_get_logo_url':
            return get_logo_url(app_sdk)
        if trigger_name == 'assessment_list_tests':
            return list_tests(request_data, app_settings, app_sdk)
        if trigger_name == 'assessment_invite_candidate':
            return invite_candidate(request_data, app_settings, app_sdk)
        if trigger_name == 'webhook_receive_event':
            return handle_webhook_event(request_data, app_settings, app_sdk)
        if trigger_name == 'assessment_is_webhook_supported':
            return check_webhook_support(app_sdk)
            
        # Return default response if no specific handler matched
        data = {
            'title': 'Welcome!',
        }

        return {
            'statusCode': 200,
            'body': json.dumps({'data': data})
        }
    except Exception as e:
        return error_response(500, f"An error occurred: {str(e)}", app_sdk)
