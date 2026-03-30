# pylint: disable=ef-restricted-imports, unused-variable, unused-import
"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import
import os
import json
import requests
import random
import traceback2

import response_objects
from base_adapter import BaseAdapter

EDCAST_LOGO_URL="https://res-4.cloudinary.com/crunchbase-production/image/upload/c_lpad,f_auto,q_auto:eco/v1486773223/b1npsiu4phvi0hfobrue.png"
CURRENT_COURSE_ENDPOINT_FORMAT = '/api/developer/v5/cards/search?email={email}'
COURSE_SEARCH_ENDPOINT_FORMAT = '/api/developer/v5/cards/search?email={email}&q={skills}'
COURSE_ENDPOINT_FORMAT = '/api/developer/v5/cards/{course_id}'

def call(http_method, **kwargs):
    if http_method == 'GET':
        return requests.get(**kwargs)
    elif http_method == 'POST':
        return requests.post(**kwargs)
    elif http_method == 'DELETE':
        return requests.delete(**kwargs)
    else:
        raise RuntimeError('Invalid http_method: {}'.format(http_method))

def get_resp(http_method, **kwargs):
    resp = call(http_method, **kwargs)
    try:
        resp.raise_for_status()
    except:
        raise Exception('Error: status_code: {}, resp_content: {}'.format(resp.status_code, resp.content))
    return resp

class EdcastAdapter(BaseAdapter):
    def __init__(self, app_settings):
        self.base_url = app_settings.get('base_url')
        if not self.base_url:
            raise ValueError('Base url cannot be emptyi!')
        if self.base_url.endswith('/'):
            self.base_url = self.base_url.strip('/')
        self.api_key = app_settings.get('api_key')
        self.access_token = app_settings.get('access_token')
        if not self.api_key or not self.access_token:
            raise ValueError('API key and access token cannot be empty')

        self.email_swap_map = app_settings.get('email_swap_map') or {}
        self.max_courses = app_settings.get('max_courses', 5)

    def _get_email(self, req_data):
        email = req_data.get('employee_email') or req_data.get('email')
        return self.email_swap_map.get(email) or email

    def get_current_courses(self, req_data):
        headers = {
            'X-API-KEY': self.api_key,
            'X-ACCESS-TOKEN': self.access_token,
            'Content-Type': 'application/json',
        }
        email = self._get_email(req_data)
        url = self.base_url + CURRENT_COURSE_ENDPOINT_FORMAT.format(email=email)
        resp = get_resp('GET', url=url, headers=headers)
        json_resp = json.loads(json.dumps(resp.json()))
        json_resp=dict(json_resp)['cards']
        courses=[]
        titles = set()
        for course in json_resp:
            if not course.get('resource', 0):
                continue

            if not course['duration']:
                continue

            course_resource = course.get('resource')
            #print("course_resource {}".format(course_resource))

            course_obj = response_objects.ProfileCourseAttendanceResponseType()
            title = course_resource['title']
            if title in titles:
                continue

            titles.add(title)
            #if course['provider'] == "User Generated Content":
            #    continue

            course_obj.title = course['resource']['title']
            course_obj.course_url = course['resource']['url']
            course_obj.provider = course['provider']
            #course_obj.provider_image = course['providerImage']
            #course_obj.duration = course['duration']/3600.0 if course['duration'] else 0

            #print("course duration {}".format(course['duration']))
            courses.append(course_obj.to_dict())

        return courses

    def _setup_course_obj(self, course_obj, course_dict):
        course_obj.lms_course_id = course_dict['id']
        course_obj.title = course_dict['resource']['title']
        course_obj.description = course_dict['resource']['description']
        course_obj.course_type = course_dict['resource']['type']
        course_obj.language = course_dict['language']
        #supposing the course_duration is returned in seconds-> converting to hours
        course_obj.duration_hours = course_dict['duration']/3600.0 if course_dict['duration'] else 0
        #course_obj.published_date = course['createdAt'] # of format 2020-10-22T11:06:53.000Z
        course_obj.course_url = course_dict['resource']['url']
        course_obj.category = course_dict['cardType']
        course_obj.image_url = course_dict['resource']['imageUrl']
        course_obj.provider = course_dict['provider']
        #course_obj.skills = course['provider']
        course_obj.lms_data = course_dict
        print("course duration {}".format(course_dict['duration']))

    def get_recommended_courses(self, req_data):
        headers = {
            'X-API-KEY': self.api_key,
            'X-ACCESS-TOKEN': self.access_token,
            'Content-Type': 'application/json',
        }

        email = self._get_email(req_data)
        url = self.base_url + COURSE_SEARCH_ENDPOINT_FORMAT.format(email='admin@edcast.com', skills="python")
        resp = get_resp('GET', url=url, headers=headers)
        json_resp = json.loads(json.dumps(resp.json()))
        json_resp=dict(json_resp)['cards']
        courses=[]
        for course in json_resp[:self.max_courses]:
            if not course['duration']:
                continue

            course_obj = response_objects.RecommendedCourseResponseType()
            self._setup_course_obj(course_obj, course)
            courses.append(course_obj.to_dict())
        return courses

    def get_course_details(self, req_data):
        headers = {
            'X-API-KEY': self.api_key,
            'X-ACCESS-TOKEN': self.access_token,
            'Content-Type': 'application/json',
        }

        email = self._get_email(req_data)
        url = self.base_url + COURSE_ENDPOINT_FORMAT.format(course_id=req_data.get('course_id'))
        resp = get_resp('GET', url=url, headers=headers)
        json_resp = json.loads(json.dumps(resp.json()))
        json_resp = dict(json_resp)['card']
        course_obj = response_objects.CourseDetailsResponseType()
        self._setup_course_obj(course_obj, json_resp)
        return course_obj.to_dict()
"""
    - Provide an entry point function for your app.
    - Your function name must be the form <trigger_point>_handler
    - Your function must accept two args -> event and context
    - The context arg can be ignored completely
    - The event arg will contain all needed params to properly invoke your app
"""
def app_handler(event, context):
    # Extract request_data -> this is the dynamic, per-invocation data for your app. E.g. profile info, message to be sent, etc.
    req_data = event.get('request_data', {})
    # Extract app_settings -> this are the static params for your app configured for each unique installation. E.g. API keys, allow/deny lists, etc.
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    print('Call recived for trigger_name: {}'.format(trigger_name))
    data = None

    try:
        ea = EdcastAdapter(app_settings)
        if trigger_name == 'careerhub_profile_course_attendance':
            data = ea.get_current_courses(req_data)
        elif trigger_name in ['careerhub_homepage_recommended_courses', 'career_planner_recommended_courses',
                              'careerhub_jobs_recommended_courses', 'careerhub_projects_recommended_courses',
                              'careerhub_recommended_courses']:
            data = ea.get_recommended_courses(req_data)
        elif trigger_name == 'careerhub_get_course_details':
            data = ea.get_course_details(req_data)
    except Exception as ex:
        err_str = 'Handler for trigger_name: {} failed with error: {}, traceback: {}'.format(
            trigger_name, str(ex), traceback2.format_exc())
        print(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback2.format_exc(),
            }),
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data, 'cache_ttl_seconds': 60})
    }
