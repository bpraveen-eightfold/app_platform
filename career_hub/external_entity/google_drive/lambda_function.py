from __future__ import absolute_import

import json
import requests

import response_objects

GOOGLE_LOGO_URL = 'https://images.fastcompany.net/image/upload/w_596,c_limit,q_auto:best,f_auto/fc/3050613-inline-i-2-googles-new-logo-copy.png'

class GDriveConnector():

    FILE_FIELDS = (
        'id,mimeType,description,webViewLink,iconLink,thumbnailLink,owners,'
        'labelInfo,name,kind,viewedByMeTime,modifiedTime,capabilities,trashed'
    )

    FILE_LIST_URL_BASE = 'https://www.googleapis.com/drive/v3/files?corpora=user'
    LIST_FILE_FIELDS_PARAM = '&fields=files(' + FILE_FIELDS + ')'

    FILE_GET_FIELDS_PARAM = 'fields=' + FILE_FIELDS
    FILE_GET_URL_BASE = 'https://www.googleapis.com/drive/v3/files/{entity_id}?' + FILE_GET_FIELDS_PARAM

    def __init__(self, oauth_token):
        self.oauth_token = oauth_token
        self.headers = {
            'Authorization': 'Bearer ' + self.oauth_token
        }

    def get_file_list(self, term=None, page_size=10, page_token=''):
        q_param = f"&q=name contains '{term}'" if term else ''
        page_size_param = f'&pageSize={page_size}'
        page_token_param = f'&pageToken={page_token}' if page_token else ''

        file_list_url = self.FILE_LIST_URL_BASE + page_size_param + page_token_param + self.LIST_FILE_FIELDS_PARAM + q_param

        print(file_list_url)

        resp = requests.get(file_list_url, headers=self.headers)
        return resp.json()

    def get_file(self, entity_id):
        if not entity_id:
            return {}

        file_get_url = self.FILE_GET_URL_BASE.format(entity_id=entity_id)

        resp = requests.get(file_get_url, headers=self.headers)
        return resp.json()


def to_file_capabilities_str(capabilities):
    if not capabilities:
        return ''
    allowed_capabilities = []
    for capability in ['canEdit', 'canComment', 'canShare']:
        if capabilities.get(capability, False):
            allowed_capabilities.append(capability)
    return ', '.join(allowed_capabilities)


def file_get_to_ext_entity_response(file):
    file_type = file.get('mimeType','').split('.')[-1]
    if file_type:
        file_type = file_type.capitalize()
    resp_obj = response_objects.CareerhubEntityDetailsResponseType()
    resp_obj.entity_id = file.get('id')
    resp_obj.title = file.get('name')
    resp_obj.cta_url = file.get('webViewLink')
    resp_obj.card_label = file_type
    resp_obj.cta_label = 'View ' + file_type if file_type else 'file'
    resp_obj.source_name = 'Google Drive'
    resp_obj.description = file.get('description')
    resp_obj.image_url = file.get('iconLink')
    # add a few interesting fields to the display
    file_owners = file.get('owners', [])
    resp_obj.fields = [
        {'name': 'Owner email', 'value': file_owners[0].get('emailAddress', 'Unknown') if len(file_owners) > 0 else 'Unknown'},
        {'name': 'Last viewed', 'value': file.get('viewedByMeTime', 'Not viewed')},
        {'name': 'Last modified', 'value': file.get('modifiedTime')},
        {'name': 'Capabilities', 'value': to_file_capabilities_str(file.get('capabilities'))},
        {'name': 'Is trashed?', 'value': 'Yes' if file.get('trashed', False) else 'No'}
    ]
    return resp_obj.to_dict()


def file_list_response_to_ext_entity_response(file_list_response):
    files = file_list_response.get('files', [])
    resp_obj = response_objects.CareerhubEntitySearchResultsResponseType()
    resp_obj.num_results = len(files)
    resp_obj.cursor = file_list_response.get('nextPageToken')
    resp_obj.entities = [file_get_to_ext_entity_response(file) for file in files]
    return resp_obj.to_dict()

def file_list_response_to_profile_view_response(file_list_response):
    rows = [
        [{'value': file.get('name'), 'link': file.get('webViewLink')}] for file in file_list_response.get('files', [])
    ]
    return {
        'title': 'Google Drive',
        'logo_url': GOOGLE_LOGO_URL,
        'table': {
            'headers': ['File'],
            'rows': rows
        }
    }


def app_handler(event, context):
    trigger_name = event.get('trigger_name')
    request_data = event.get('request_data', {})

    gdrive = GDriveConnector(oauth_token=request_data['oauth_token'])

    data = None
    if trigger_name == 'careerhub_entity_search_results':
        files = gdrive.get_file_list(
            term=request_data.get('term'),
            page_size=request_data.get('limit', 10),
            page_token=request_data.get('cursor', None)
        )
        data = file_list_response_to_ext_entity_response(files)
    elif trigger_name == 'careerhub_get_entity_details':
        file = gdrive.get_file(entity_id=request_data.get('entity_id'))
        data = file_get_to_ext_entity_response(file)
    elif trigger_name == 'career_hub_home_sidebar_view':
        files = gdrive.get_file_list(page_size=3)
        data = file_list_response_to_profile_view_response(files)

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data, 'cache_ttl_seconds': 60})
    }

def main():
    import os
    import pprint
    from pprint import pprint
    payload = {}

    payload_files = ['test_payload_search.json', 'test_payload_get.json', 'test_payload_sidebar.json']

    for payload_file in payload_files:
        payload = {}
        with open(os.path.join(os.path.dirname(__file__), payload_file)) as f:
            payload = json.load(f)
        result = app_handler(payload, None)
        print(40*'~' + payload_file + 40*'~')
        pprint(json.loads(result['body']))

if __name__ == '__main__':
    main()
