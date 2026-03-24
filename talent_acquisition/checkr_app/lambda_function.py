from __future__ import absolute_import

import json
import traceback
import requests
from datetime import datetime
from datetime import timezone
from ef_app_sdk import EFAppSDK

TEST_EMAIL = 'pcs-eng@eightfold.ai'

class SUPPORTED_WEBHOOK_EVENT:
    ACCOUNT_CREDENTIALED = 'account.credentialed'
    TOKEN_DEAUTHORIZED = 'token.deauthorized'

class Logger:
    def log(self, *args):
        print(*args)

app_sdk = Logger()

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

def error_response(error_code, error_str):
    """
    Generates an error response with the given error code and error string.

    Parameters:
    error_code (int): The error code to be included in the response.
    error_str (str): The error string to be included in the response.

    Returns:
    dict: A dictionary containing the error code and error string.

    """
    data = {'error': error_str, 'error_code': error_code}
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

def convert_to_timestamp(time_str):
    """
    Converts a string representation of time in ISO 8601 format to a Unix timestamp.

    Args:
        time_str (str): The string representation of time in ISO 8601 format.

    Returns:
        int: The Unix timestamp corresponding to the given time string, or None if the time string is empty.

    """
    if time_str:
        date_time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
        return int(date_time.replace(tzinfo=timezone.utc).timestamp())
    return None

def str2bool(v):
    """
    Converts a string representation of a boolean value to its corresponding boolean value.

    Args:
        v (str): The string representation of the boolean value.

    Returns:
        bool: The corresponding boolean value.

    Examples:
        >>> str2bool('yes')
        True
        >>> str2bool('no')
        False
        >>> str2bool('true')
        True
        >>> str2bool('false')
        False
        >>> str2bool('t')
        True
        >>> str2bool('f')
        False
        >>> str2bool('1')
        True
        >>> str2bool('0')
        False
    """
    return str(v).lower() in ('yes', 'true', 't', '1')

def get_logo_url():
    """
    Retrieves the logo URL for the talent acquisition app.

    Returns:
        dict: A dictionary containing the logo URL.
    """
    logo_url = 'https://assets.checkr.com/logo-blue.svg'
    data = {'logo_url': logo_url}
    app_sdk.log(f'Checkr Logo URL is: {data}')
    return success_response(data)

def list_tests(request_data={}, app_settings={}):
    """
    Retrieves a list of assessments/tests.
    Args:
        request_data (dict, optional): The request data. Defaults to {}.
        app_settings (dict, optional): The application settings. Defaults to {}.
    Returns:
        dict: The list of assessments/tests.
    Raises:
        ValueError: If request_data or app_settings is empty.
        ValueError: If the response status code is not 200.
        ValueError: If the nodes response status code is not 200.
    """
    if not request_data or not app_settings:
        return error_response(400, 'request_data or app_settings cannot be empty')

    oauth_token = request_data.get('oauth_token','')
    base_url = app_settings.get('checkr_base_url','')

    response = requests.get(f'{base_url}/packages', auth=(oauth_token, ''))

    if response.status_code != 200:
        return error_response(response.status_code, 'Could not get assessment list')
    
    nodes_response = requests.get(f'{base_url}/nodes?include=packages', auth=(oauth_token, ''))
    if nodes_response.status_code != 200:
        app_sdk.log(f'Could not get nodes list {nodes_response.json()}')

    # Get the nodes list and the package associated with it.
    # If the node has a package, then append the package name to the node name.
    # If the node does not have a package, then append the node name to the list.
    # Remove duplicates based on name.
    nodes = nodes_response.json().get('data', [])

    data = []
    assessment_list = response.json().get('data', [])

    if not nodes:
        for assessment in assessment_list:
            item = {
                'duration_minutes': '',
                'id': assessment.get('slug',0),
                'name': assessment.get('name',''),
                'published': ''
            }
            data.append(item)
    else:
        # Loop through all the nodes and generate the assessment list based out of package and node combination
        # Example NOde is Global HQ and package is Basic Plus. The value will be `Global HQ - Basic Plus`
        for node in nodes:
            packages = node.get('packages', [])
            if not packages:
                packages = [x.get('slug') for x in assessment_list]
            for package_id in packages:
                package = next((assessment for assessment in assessment_list if assessment.get('slug') == package_id), None)
                if not package:
                    app_sdk.log(f'Package not found for node {node.get("name")} and package_id {package_id}')
                    continue
                item = {
                    'duration_minutes': '',
                    'id': package.get('slug', 0),
                    'name': f"{node.get('name', '')} - {package.get('name', '')}",
                    'published': ''
                }
                data.append(item)

    # Remove duplicates based on name
    unique_data = {}
    for item in data:
        unique_data[item['name']] = item

    # Convert dictionary back to list
    data = list(unique_data.values())

    app_sdk.log(f'Assessment List: {data}, Nodes List: {nodes}')
    return success_response(data)

def invite_candidate(request_data={}, app_settings={}):
    """
    Invites a candidate to the talent acquisition system.

    Args:
        request_data (dict, optional): The request data containing information about the candidate and the invitation. Defaults to {}.
        app_settings (dict, optional): The application settings. Defaults to {}.

    Returns:
        dict: The response containing the assessment ID, email, test URL, and vendor candidate ID.
    """

    if not request_data or not app_settings:
        return error_response(400, 'request_data or app_settings cannot be empty')

    use_test_email = str2bool(app_settings.get('use_test_email', False))
    invite_metadata = request_data.get('invite_metadata')
    email = TEST_EMAIL if use_test_email else invite_metadata.get('email')

    oauth_token = request_data.get('oauth_token')
    base_url = app_settings.get('checkr_base_url')

    first_name = request_data.get('first_name')
    last_name = request_data.get('last_name')
    work_location = request_data.get('location_state')
    location_country = request_data.get('location_country')

    work_state = validate_work_location(work_location)
    if not work_state:
        app_sdk.log('Invite Candidate: Candidate location not found or not in the United States')
        return error_response(400, 'Candidate location not found or not in the United States')

    candidate_data = get_candidate(base_url, oauth_token, first_name, last_name, email)
    if candidate_data:
        invitation = invite_existing_candidate(base_url, oauth_token, candidate_data, invite_metadata, work_state, work_country=location_country)
    else:
        candidate_data = create_new_candidate(base_url, oauth_token, first_name, last_name, email, invite_metadata, location_country=location_country, location_state=work_state)
        invitation = invite_existing_candidate(base_url, oauth_token, candidate_data, invite_metadata, work_state, work_country=location_country)

    response = success_response({
        'assessment_id': invitation.get('id'),
        'invite_already_sent': '',
        'email': candidate_data.get('email'),
        'test_url': invitation.get('invitation_url'),
        'vendor_candidate_id': invitation.get('candidate_id')
    })
    app_sdk.log(f'Invite Candidate Response: {response}')
    return response

def validate_work_location(work_location):
    """
    Validates the work location.

    Args:
        work_location (str): The work location to be validated.

    Returns:
        str or None: The validated work location if it is a valid US location, otherwise None.
    """
    if not work_location:
        return None
    location_split = work_location.split(',')
    if location_split[-1] == 'US':
        return 'CA' if location_split[0] == '' or location_split[0] == 'US' else location_split[0]
    return None

def get_candidate(base_url, oauth_token, first_name, last_name, email, location_country='US', location_state='CA'):
    """
    Retrieves a candidate from the specified base URL using the provided OAuth token.

    Parameters:
    - base_url (str): The base URL of the API.
    - oauth_token (str): The OAuth token for authentication.
    - first_name (str): The first name of the candidate.
    - last_name (str): The last name of the candidate.
    - email (str): The email address of the candidate.
    - location_country (str, optional): The country of the candidate's location. Defaults to 'US'.
    - location_state (str, optional): The state of the candidate's location. Defaults to 'CA'.

    Returns:
    - dict: The candidate data if found, otherwise None.
    """
    candidate_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
    }
    response = requests.get(f'{base_url}/candidates', params=candidate_data, auth=(oauth_token, ''))
    if response.status_code != 200:
        return None
    candidates = response.json().get('data', [])
    return candidates[-1] if candidates else None

def create_new_candidate(base_url, oauth_token, first_name, last_name, email, invite_metadata, location_country='US', location_state='CA'):
    """
    Create a new candidate in the talent acquisition system.

    Args:
        base_url (str): The base URL of the talent acquisition system.
        oauth_token (str): The OAuth token for authentication.
        first_name (str): The first name of the candidate.
        last_name (str): The last name of the candidate.
        email (str): The email address of the candidate.
        invite_metadata (dict): A dictionary containing the invite metadata.
        location_country (str, optional): The country of the candidate's work location. Defaults to 'US'.
        location_state (str, optional): The state of the candidate's work location. Defaults to 'CA'.

    Returns:
        dict: The JSON response containing the details of the created candidate.
    """
    candidate_data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'metadata[pid]': invite_metadata.get('pid'),
        'metadata[profile_id]': invite_metadata.get('profile_id'),
        'metadata[ats_candidate_id]': invite_metadata.get('ats_candidate_id'),
        'metadata[test_id]': invite_metadata.get('test_id'),
        'metadata[email]': email,
        'work_locations[][state]': location_state,
        'work_locations[][country]': location_country,
    }
    response = requests.post(f'{base_url}/candidates', data=candidate_data, auth=(oauth_token, ''))
    return response.json()

def invite_existing_candidate(base_url, oauth_token, candidate_data, invite_metadata, work_state, work_country='US'):
    """
    Invites an existing candidate to a job application.

    Parameters:
    - base_url (str): The base URL of the API.
    - oauth_token (str): The OAuth token for authentication.
    - candidate_data (dict): The data of the candidate to be invited.
    - invite_metadata (dict): The metadata for the invitation.
    - work_state (str): The state of the candidate's work location.
    - work_country (str, optional): The country of the candidate's work location. Defaults to 'US'.

    Returns:
    - dict: The JSON response from the API.
    """
    invite_data = {
        'package': invite_metadata.get('test_id', ''),
        'candidate_id': candidate_data.get('id'),
        'work_locations[][state]': work_state,
        'work_locations[][country]': work_country,
    }
    response = requests.post(f'{base_url}/invitations', data=invite_data, auth=(oauth_token, ''))
    return response.json()

def is_webhook_supported():
    """
    Checks if webhook is supported.

    Returns:
        dict: A dictionary containing the result of the check.
    """
    data = {'is_webhook_supported': 'true'}
    return success_response(data)

def handle_webhook_event(request_data={}, app_settings={}):
    """
    Handle webhook events.

    Args:
        request_data (dict): The request data containing the webhook payload.
        app_settings (dict): The application settings.

    Returns:
        dict: The response generated based on the webhook type.

    Raises:
        KeyError: If a key error occurs.
        requests.RequestException: If a request error occurs.
        Exception: If an unexpected error occurs.
    """
    if not request_data or not app_settings:
        return error_response(400, 'request_data or app_settings cannot be empty')
    try:
        candidate_report_json = request_data.get('request_payload')
        app_sdk.log(f'Webhook Request Payload: {candidate_report_json}')
        if 'type' not in candidate_report_json:
            return error_response(400, 'Webhook type not found')
        
        # Check if the webhook type is account.credentialed
        if candidate_report_json['type'] == SUPPORTED_WEBHOOK_EVENT.ACCOUNT_CREDENTIALED:
            response_data = {
                'stacktrace': '',
                'actions': [
                    {
                        'action_name': 'save_account_credentialed_data',
                        'request_data': candidate_report_json
                    }
                ],
                'is_success': True,
                'error': False
            }
            response = success_response(response_data)
            app_sdk.log(f'Auth credentialed webhook customised response: {response}' )

        # Check if the webhook type is token.deauthorized
        elif candidate_report_json['type'] == SUPPORTED_WEBHOOK_EVENT.TOKEN_DEAUTHORIZED:
            response_data = {
                'stacktrace': '',
                'actions': [
                    {
                        'action_name': 'token_deauthorized',
                        'request_data': candidate_report_json
                    }
                ],
                'is_success': True,
                'error': False
            }
            response = success_response(response_data)
            app_sdk.log(f'Token deauthorized webhook customised response: {response}')
        
        # Else this is a report webhook
        else:
            report_base_url = app_settings.get('checkr_report_base_url')
            candidate_report_data = candidate_report_json.get('data')
            candidate_report_obj = candidate_report_data.get('object')
            response = create_webhook_report_response(request_data, app_settings, candidate_report_json, report_base_url, candidate_report_data, candidate_report_obj)
            app_sdk.log(f'Report webhook customised response: {response}')
        return response
    except KeyError as e:
        app_sdk.log(f'Key error: {e}')
        return error_response(400, f'Key error: {e}')
    except requests.RequestException as e:
        app_sdk.log(f'Request error: {e}')
        return error_response(500, f'Request error: {e}')
    except Exception as e:
        app_sdk.log(f'Unexpected error: {e}')
        return error_response(500, f'Unexpected error: {e}')

def create_webhook_report_response(request_data, app_settings, candidate_report_json, report_base_url, candidate_report_data, candidate_report_obj):
    """
    Creates a webhook report response based on the given parameters.

    Args:
        request_data (dict): The request data containing the OAuth token.
        app_settings (dict): The application settings.
        candidate_report_json (dict): The JSON data of the candidate report.
        report_base_url (str): The base URL for the report.
        candidate_report_data (dict): The data of the candidate report.
        candidate_report_obj (dict): The object representing the candidate report.

    Returns:
        dict: The webhook report response.

    Raises:
        requests.exceptions.HTTPError: If there is an HTTP error while retrieving the candidate response.

    """
    report_data = {
            'candidate_report_url': None,
            'candidate_report_checkr_status': candidate_report_obj.get('status', ''),
            'candidate_report_completed': convert_to_timestamp(candidate_report_obj.get('completed_at')),
            'candidate_report_start': convert_to_timestamp(candidate_report_obj.get('created_at')),
            'candidate_report_custom_status': '',
            'candidate_report_comments': '',
            'report_json': candidate_report_json,
        }
    candidate_report_ef_status = 'completed'
    candidate_report_status = report_data.get('candidate_report_checkr_status')
    if candidate_report_status == 'clear' or candidate_report_status == 'consider' \
            or candidate_report_status == 'suspended' or candidate_report_status == 'dispute':
        candidate_report_ef_status = 'completed'
    elif candidate_report_status == 'pending':
        candidate_report_ef_status = 'invited'
    report_data['candidate_report_ef_status'] = candidate_report_ef_status
    if candidate_report_status != 'pending':
        report_data['candidate_report_url'] = f'{report_base_url}/{candidate_report_obj.get("id")}'
    candidate_report_custom_status, candidate_report_comments = map_to_custom_status(
        candidate_report_json.get('type', ''),
        candidate_report_status,
        candidate_report_obj.get('result', ''),
        candidate_report_obj.get('assessment', ''),
        candidate_report_obj.get('adjudication', '')
    )
    report_data['candidate_report_custom_status'] = candidate_report_custom_status
    report_data['candidate_report_comments'] = candidate_report_comments
    oauth_token = request_data.get('oauth_token')
    base_url = app_settings.get('checkr_base_url')
    candidate_response = requests.get(
        f'{base_url}/candidates/{candidate_report_obj.get("candidate_id")}',
        auth=(oauth_token, '')
    )
    candidate_response.raise_for_status()
    candidate_report_response = candidate_response.json()
    app_sdk.log(f'Webhook Checkr Response: {candidate_report_response}')
    candidate_report_invite_metadata = candidate_report_response.get('metadata', {})
    response = create_webhook_response(report_data, candidate_report_invite_metadata)
    return response

def create_webhook_response(report_data, invite_metadata):
    """
    Creates a webhook response.

    Args:
        report_data (dict): The report data.
        invite_metadata (dict): The invite metadata.

    Returns:
        dict: The webhook response.

    """
    return success_response({
        'stacktrace': '',
        'actions': [{
            'action_name': 'save_assessment_to_profile_data',
            'request_data': {
                'invite_metadata': {
                    'email': invite_metadata.get('email', None),
                    'profile_id': invite_metadata.get('profile_id', None),
                    'pid': invite_metadata.get('pid', None),
                    'ats_candidate_id': invite_metadata.get('ats_candidate_id', None),
                    'test_id': invite_metadata.get('test_id', None)
                },
                'assessment_report': {
                    'test_id': invite_metadata.get('test_id', None),
                    'email': invite_metadata.get('email', None),
                    'status': report_data.get('candidate_report_ef_status', None),
                    'vendor_report_status': report_data.get('candidate_report_checkr_status', None),
                    'rating': invite_metadata.get('result', None),
                    'assigned_ts': report_data.get('candidate_report_start', 0),
                    'start_ts': report_data.get('candidate_report_start', 0),
                    'completed_ts': report_data.get('candidate_report_completed', 0),
                    'comments': report_data.get('candidate_report_comments', None),
                    'report_url': report_data.get('candidate_report_url', None),
                    'response_json': report_data.get('report_json', {}),
                    'vendor_status': report_data.get('candidate_report_custom_status', None)
                }
            }
        }],
        'is_success': True,
        'error': False
    })

def map_to_custom_status(report_type, report_status, report_result, report_assessment, report_adjudication):
    """
    Maps the given report attributes to a custom status and comments.
    Args:
        report_type (str): The type of the report.
        report_status (str): The status of the report.
        report_result (str): The result of the report.
        report_assessment (str): The assessment of the report.
        report_adjudication (str): The adjudication of the report.
    Returns:
        tuple: A tuple containing the custom status and comments.
    """
    # Rest of the code...
    custom_status = 'Unknown'
    comments = 'No comments available.'

    if report_status == 'complete':
        if 'includes_canceled' in report_status and 'false' in report_status:
            custom_status = report_assessment or 'Clear'
            comments = 'The report was completed and no charges were found.'
        elif 'includes_canceled' in report_status and 'true' in report_status:
            if report_result == 'clear':
                custom_status = report_assessment or 'Complete with Canceled'
                comments = 'The report was partially completed with canceled screening(s) and no charges were found.'
            elif report_result is None:
                custom_status = 'Canceled'
                comments = 'The report was automatically completed and all screenings were canceled. An example of this is an SSN exception that resulted in a report suspension lasting 30 days.'
        elif report_result == 'consider':
            if report_adjudication is None:
                custom_status = report_assessment or 'Needs Review'
                comments = 'The report was completed and charges were found.'
            elif report_adjudication == 'pre_adverse_action':
                custom_status = 'Pre Adverse Action'
                comments = 'The report has been pre-adverse actioned.'
            elif report_adjudication == 'post_adverse_action':
                custom_status = 'Not Eligible'
                comments = 'The report has been automatically post-adverse actioned (normally 7 days after pre-adverse actioning).'
            elif report_adjudication == 'engaged':
                custom_status = 'Eligible'
                comments = 'The report has been engaged.'
    elif report_status == 'suspended':
        custom_status = 'Suspended'
        comments = 'The report has been suspended due to an exception not being resolved within 7 days or 2 attempts by the candidate.'
    elif report_status == 'pending':
        custom_status = 'Pending'
        comments = 'The suspended report has been un-suspended (i.e.: resumed).'
    elif report_status == 'dispute':
        custom_status = 'Disputed'
        comments = 'The report has been disputed by the candidate (only applicable to reports with a “consider” result).'
    elif report_status == 'canceled':
        custom_status = 'Canceled'
        comments = 'All of the screenings in the background check have been canceled (prior to any of them processing).'
    
    if report_type == 'invitation.created':
        custom_status = 'Invitation Sent'
        comments = 'The invite was sent.'
    elif report_type == 'invitation.completed':
        custom_status = 'Pending'
        comments = 'The invite was completed by the candidate and the report was created.'
    elif report_type == 'invitation.expired':
        custom_status = 'Invitation Expired'
        comments = 'The invite expired after 7 days.'
    elif report_type == 'invitation.deleted':
        custom_status = 'Invitation Canceled'
        comments = 'The invite was canceled via the Dashboard or the API.'

    return custom_status, comments

def app_handler(event, context):
    """
    Handle the application events based on the trigger name.

    Parameters:
    - event (dict): The event data passed to the lambda function.
    - context (object): The context object passed to the lambda function.

    Returns:
    - The result of the corresponding trigger function based on the trigger name.

    Raises:
    - Exception: If an error occurs while handling the event.

    """
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    app_sdk.log(f'Trigger name is {trigger_name}')

    try:
        if trigger_name == 'assessment_get_logo_url':
            return get_logo_url()
        elif trigger_name == 'assessment_list_tests':
            return list_tests(request_data, app_settings)
        elif trigger_name == 'assessment_invite_candidate':
            return invite_candidate(request_data, app_settings)
        elif trigger_name == 'assessment_is_webhook_supported':
            return is_webhook_supported()
        elif trigger_name == 'webhook_receive_event':
            return handle_webhook_event(request_data, app_settings)
        else:
            return error_response(400, 'Unknown trigger name')
    except Exception as e:
        error_str = 'Something went wrong, traceback: {}'.format(traceback.format_exc())
        app_sdk.log(json.dumps({'error_str': error_str}))
        app_sdk.log(f'Unable to handle checkr error: {e}')
        return error_response(500, error_str)
