# pylint: disable=ef-restricted-imports, unused-variable, unused-import
"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import json
import time
import traceback

import response_objects
import udemy_utils


UDEMY_BASE_URL = 'https://www.udemy.com'
COURSE_LIST_URL = '{base_url}/api-2.0/courses/?fields[course]=@all'
COURSE_DETAILS_URL = '{base_url}/api-2.0/courses/{entity_id}/?fields[course]=@all'


def _get_entity_from_course_details(data_dict, entity_id):
    entity_obj = response_objects.CareerhubEntityDetailsResponseType()
    entity_obj.entity_id = entity_id
    entity_obj.title = data_dict.get('title')
    entity_obj.image_url = data_dict.get('image_480x270')
    entity_obj.last_modified_ts = data_dict.get('last_update_date')
    entity_obj.tags = [label['label']['title'] for label in data_dict.get('course_has_labels', {}) if label.get('label')]
    course_url = UDEMY_BASE_URL + data_dict.get('url')
    entity_obj.cta_url = course_url
    cta_url_str = None
    if course_url:
        cta_url_str = (
            """<div style="text-align:center;padding:20px 10px;"><a target="_blank"
            style="background-color:#1571ac;padding:10px
            20px;display:inline-block;border-radius:4px;color:#fff;text-decoration:none;" href='"""
            + course_url
            + """'>View Course</a></div> """
        )
    description = data_dict.get('description') or ""
    entity_obj.description = description + " " + cta_url_str if cta_url_str else description
    entity_obj.source_name = 'Udemy'
    entity_obj.cta_label = 'Course'
    entity_obj.fields = []
    return entity_obj


class UdemyAdapter:
    def __init__(self, app_settings):
        self.app_settings = app_settings
        self.auth_token = udemy_utils.generate_authtoken(
            client_id=app_settings.get('client_id'),
            client_secret=app_settings.get('client_secret')
        )
        self.headers = {
            "Authorization": f"Basic {self.auth_token}"
        }

    def _process_assigned_courses_resp_content(self, courses_data_dict, req_data):
        search_results = response_objects.CareerhubEntitySearchResultsResponseType()
        search_results.entities = []

        for course_data in courses_data_dict:
            entity_id = course_data.get('id')
            search_results.entities.append(_get_entity_from_course_details(course_data, entity_id))

        search_results.num_results = len(search_results.entities)
        search_results.offset = 0
        search_results.limit = search_results.num_results
        return search_results.to_dict()

    def get_assigned_courses(self, req_data):
        url = COURSE_LIST_URL.format(base_url=UDEMY_BASE_URL)
        search_key = req_data.get('term', None)
        params = {}
        params['page_size'] = req_data.get('limit', 10)

        if search_key:
            params['search'] = search_key

        start_time = time.perf_counter()
        resp = udemy_utils.get_resp('GET', url=url, headers=self.headers, params=params)

        if resp.status_code != 200:
            raise ValueError(resp.content or 'Failure to fetch assigned courses')

        end_time = time.perf_counter()
        print(f'assigned courses fetch time: {end_time - start_time:0.4f} seconds')
        data = json.loads(resp.content.decode('utf-8'))
        return self._process_assigned_courses_resp_content(data['results'], req_data)

    def get_course_search_results(self, req_data):
        return self.get_assigned_courses(req_data)

    def get_course_details_int(self, entity_id):
        url = COURSE_DETAILS_URL.format(base_url=UDEMY_BASE_URL, entity_id=entity_id)
        resp = udemy_utils.get_resp('GET', url=url, headers=self.headers)

        if resp.status_code != 200:
            raise ValueError(resp.content or 'Failure to fetch course details')

        data_dict = json.loads(resp.content.decode('utf-8'))
        return _get_entity_from_course_details(data_dict, entity_id)

    def get_course_details(self, req_data):
        entity_id = req_data['entity_id']
        entity_obj = self.get_course_details_int(entity_id)
        return entity_obj.to_dict()

"""
    - The entry point function for the app.
    - The context arg can be ignored completely
    - The event arg will contain all needed params to properly invoke your app
"""
def app_handler(event, context):
    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    print(f'Call recived for trigger_name: {trigger_name}')
    data = None

    try:
        ua = UdemyAdapter(app_settings)
        print(f'req_data: {req_data}')

        if trigger_name == 'careerhub_entity_search_results':
            data = ua.get_course_search_results(req_data)
        elif trigger_name == 'careerhub_get_entity_details':
            data = ua.get_course_details(req_data)

    except Exception as ex:
        err_str = f'Handler for trigger_name: {trigger_name} failed with error: {str(ex)}, traceback: {traceback.format_exc()}'
        print(err_str)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
