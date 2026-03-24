from __future__ import absolute_import

import concurrent.futures
import csv
import datetime
import os
import json
import traceback
import urllib.parse

import requests

from transfer import Sftp


TOKEN_URL = 'https://auth.go1.com/oauth/token'
BASE_URL = 'https://api.go1.com'
FIELD_NAMES = [
    'id', 'title', 'description', 'summary', 'language',
    'image_url', 'content_type', 'duration', 'enrolments', 'portal', 
    'created', 'sourceId', 'mobile_optimised', 'wcag', 'assessable',
    'internal_qa_rating'
]
MAX_ENTRIES = 50


def get_access_token(client_id, client_secret):
    """
    Make POST request to oauth/token/ endpoint to retrieve the
    access token using client ID and client secret.

    If the call returns a failure status code, an HTTPError will be raised
    """
    resp = requests.post(
        url=TOKEN_URL,
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
        }
    )
    resp.raise_for_status()
    body = resp.json()
    return body.get('token_type'), body.get('access_token')


def get_learning_objects(token_type, access_token):
    """
    Make async API calls to fetch all learning objects from Go1
    """
    url = urllib.parse.urljoin(BASE_URL, 'v2/learning-objects')
    headers = {
        'Authorization': f'{token_type} {access_token}'
    }

    learning_objects = []

    # Make an initial call to grab the scrollId
    params = {'limit': MAX_ENTRIES, 'scroll': True}
    resp = requests.get(url=url, headers=headers, params=params)
    resp.raise_for_status()

    scroll_id = resp.json().get('_scroll_id')
    params['scrollId'] = scroll_id
    total = resp.json().get('total')
    learning_objects.extend(resp.json().get('hits'))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = []
        for _ in range(len(learning_objects), total, MAX_ENTRIES):
            results.append(executor.submit(requests.get, url=url, headers=headers, params=params))
        for result in concurrent.futures.as_completed(results):
            learning_objects.extend(result.result().json().get('hits'))
    return learning_objects


def convert_field_names(learning_object):
    """
    Reformat data from API response to CSV-writable format
        Fields from the maunal CSV file that is missing in API response data
        enrollments
        sourceId
        mobile_optimised
        wcag
        internal_qa_rating
    """
    new_learning_object = {}
    for field in FIELD_NAMES:
        new_learning_object[field] = learning_object.get(field)
    new_learning_object['image_url'] = learning_object.get('image')
    new_learning_object['content_type'] = learning_object.get('type')
    new_learning_object['duration'] = learning_object.get('delivery', {}).get('duration')
    new_learning_object['portal'] = learning_object.get('provider', {}).get('name')
    new_learning_object['created'] = learning_object.get('created_time')
    return new_learning_object


def pack_learning_objects_into_csv(learning_objects, csv_filename):
    """
    Write all learning objects into a CSV file
    """
    with open(csv_filename, 'w', newline='') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES)
        csv_writer.writeheader()

        for lo in map(convert_field_names, learning_objects):
            csv_writer.writerow(lo)


def get_csv_filename(filename_prefix, timestamp_format):
    """
    Construct CSV filename based on given prefix and suffix format
    """
    timestamp = datetime.datetime.strftime(datetime.datetime.today(), timestamp_format)
    return f'/tmp/{filename_prefix}_{timestamp}.csv'


def upload_file_to_sftp(credentials, filename):
    """
    Upload a file to target SFTP server
    """
    hostname = credentials.get('host')
    username = credentials.get('username')
    destination = 'inbound/'
    private_key = credentials.get('private_key')
    sftp_conn = Sftp(
        hostname=hostname,
        username=username,
        destination=destination,
        private=private_key.get('value', '')
    )
    sftp_conn(filename)


def get_inconsistent_fields(request_data):
    app_settings = request_data.get('app_settings', {})
    ef_settings = request_data.get('ef_settings', {})

    inconsistent_fields = []
    for label in ['host', 'username', 'filename_prefix', 'timestamp_format']:
        app_settings_val = app_settings[label].strip()
        ef_settings_val = ef_settings[label].strip()
        if app_settings_val != ef_settings_val:
            inconsistent_fields.append(label)
    return inconsistent_fields


def app_handler(event, context):
    trigger_name = event.get('trigger_name')

    if trigger_name == 'post_install':
        inconsistent_fields = get_inconsistent_fields(event.get('request_data', {}))
        if not inconsistent_fields:
            data = {'is_success': True}
        else:
            data = {
                'is_success': False,
                'error': f'Following app and system settings fields are inconsistent: {inconsistent_fields}',
            }
        return {
            'statusCode': 200,
            'body': json.dumps({'data': data})
        }

    if not trigger_name.startswith('scheduled_'):
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'unknownTrigger'})
        }

    app_settings = event.get('app_settings', {})
    ef_integration_settings = event.get('ef_integration_settings', {})

    client_id = ef_integration_settings.get('client_id')
    client_secret = ef_integration_settings.get('client_secret')

    try:
        # Get access token
        token_type, access_token = get_access_token(client_id, client_secret)

        # Make request to list-learning-objects API endpoint
        learning_objects = get_learning_objects(token_type, access_token)

        # Pack data into csv
        filename_prefix = app_settings.get('filename_prefix')
        timestamp_format = app_settings.get('timestamp_format')
        csv_filename = get_csv_filename(filename_prefix, timestamp_format)
        pack_learning_objects_into_csv(learning_objects, csv_filename)

        # Upload to sftp server
        upload_file_to_sftp(credentials=app_settings, filename=csv_filename)
        
    except requests.HTTPError as e:
        return {
            'statusCode': e.response.status_code,
            'body': json.dumps(
                {
                    'error': repr(e),
                    'stacktrace': traceback.format_exc(),
                }
            ),
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(
                {
                    'error': repr(e),
                    'stacktrace': traceback.format_exc(),
                }
            ),
        }

    data = {'message': 'Successfully invoked Go1 app!'}
    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
