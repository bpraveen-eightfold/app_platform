# pylint: disable=ef-restricted-imports, unused-variable, unused-import
#Include all dependencies such as Python Standard Modules and open source libraries
from __future__ import absolute_import

import json
import time
import traceback
import response_objects

# Set up your LXP details such as base URL and URLs for API endpoints to fetch list of courses as well as individual course details. An arbitrary example is shown below.
LXP_BASE_URL = 'https://www.xyz.com'
COURSE_LIST_URL = ''
COURSE_DETAILS_URL = ''
USER_ENROLLED_COURSES_URL = ''

# Set up an Adapter

class LXPAdapter(BaseAdapter):
    # Modify the init function to set up app settings for the integration such as auth information
    def __init__(self, app_settings):
        self.app_settings = app_settings
        self.headers = {
            "Authorization": f"Basic {self.auth_token}"
        }
        
    def get_attended_courses(self, req_data):
        headers = {
            #set up headers with auth information 
        }
        #Email address of user
        email = self._get_email(req_data)
        #URL to fetch details of courses that are attended by the user
        url = self.base_url + USER_ENROLLED_COURSES.format(email=email)
        resp = get_resp('GET', url=url, headers=headers)
        data = json.loads(resp.content.decode('utf-8'))
        courses=[]
        titles = set()
        for course in data:
            if not course['duration']:
                continue
            course_resource = course.get('resource')
            course_obj = response_objects.ProfileCourseAttendanceResponseType()
            title = course_resource['title']
            if title in titles:
                continue
            titles.add(title)
            course_obj.title = course['resource']['title']
            course_obj.course_url = course['resource']['url']
            course_obj.provider = course['provider']
            courses.append(course_obj.to_dict())
        return courses
    
    # Modify this function to map course details values for CareerhubEntityDetailsResponseType 
    def _setup_course_obj(self, data_dict, entity_id):
        course_obj = response_objects.CareerhubEntityDetailsResponseType()
        course_obj.entity_id = entity_id
        course_obj.title = data_dict.get('title')
        course_obj.image_url = data_dict.get('image_480x270')
        course_obj.last_modified_ts = data_dict.get('last_update_date')
        course_obj.tags = [label['label']['title'] for label in data_dict.get('course_has_labels', {}) if label.get('label')]
        course_url = LXP_BASE_URL + data_dict.get('url')
        course_obj.cta_url = course_url
        description = data_dict.get('description') or ""
        course_obj.description = description + " "
        course_obj.source_name = 'XYZ'
        course_obj.cta_label = 'View Course'
        course_obj.card_label = 'Course'
        fields = []
        course_type = 'test type'
        fields.append({'name': 'Type', 'value': course_type})
        language = 'test language'
        fields.append({'name': 'Language', 'value': language})
        duration_hours = '' 
        fields.append({'name': 'Duration Hours', 'value': duration_hours})
        category = 'test category'
        fields.append({'name': 'Category', 'value': category})
        course_obj.fields = fields
        course_obj.fields = []
        return course_obj
    
    # Modify this function to create your own logic for fetching results for courses that are searched on Eightfold 
    def get_searched_courses(self, req_data):
        url = COURSE_LIST_URL.format(base_url=LXP_BASE_URL)
        search_key = req_data.get('term', None)
        params = {}
        params['page_size'] = req_data.get('limit', 10)

        if search_key:
            params['search'] = search_key

        start_time = time.perf_counter()
        resp = get_resp('GET', url=url, headers=self.headers, params=params)

        if resp.status_code != 200:
            raise ValueError(resp.content or 'Failure to fetch assigned courses')

        end_time = time.perf_counter()
        print(f'assigned courses fetch time: {end_time - start_time:0.4f} seconds')
        data = json.loads(resp.content.decode('utf-8'))
        return self._process_search_courses_resp_content(data['results'], req_data)

    # Modify this function to create your own logic for processing and returning the search results  
    def _process_search_courses_resp_content(self, courses_data_dict, req_data):
        courses = response_objects.CareerhubEntitySearchResultsResponseType()
        courses.entities = []

        for course_data in courses_data_dict:
            entity_id = course_data.get('id')
            search_results.entities.append(_setup_course_obj(course_data, entity_id))
            
        search_results.num_results = len(search_results.entities)
        search_results.offset = 0
        search_results.limit = search_results.num_results
        return search_results.to_dict()
    
    def get_course_search_results(self, req_data):
        return self.get_searched_courses(req_data)
    
    # Modify the code below to fetch course details from your LXP and to set up course object to display in the Eightfold UI   
    def get_course_details(self, req_data):
        headers = {
            # set up header information such as auth data
        }
        email = '' # User email 
        url =  '' # URL to get details of a course Example: self.base_url + COURSE_LIST_URL(course_id=req_data.get('course_id'))
        resp = get_resp('GET', url=url, headers=headers)
        json_resp = json.loads(json.dumps(resp.json()))
        json_resp = dict(json_resp)['courses']
        course_obj = response_objects.CareerhubEntityDetailsResponseType()
        self._setup_course_obj(course_obj, course_id)
        return course_obj.to_dict()

   # Modify this function to map course details values for CareerhubRecommendedCourseResponseType 
    def _setup_career_planner_course_obj(self, course_obj, course):
        course_obj.lms_course_id = i
        course_obj.title = 'Title {}'.format(i)
        course_obj.description = 'Description {}'.format(i)
        course_obj.course_type = 'course'
        course_obj.language = 'en'
        course_obj.duration_hours = ''
        course_obj.course_url = ''
        course_obj.image_url = ''
        course_obj.provider = ''

    # Modify the code here to set up the logic for fetching and displaying recommended courses to users based on skills 
    def get_recommended_courses(self, req_data):
        headers = {
           # setup headers
        }
        email = '' # Set up a way to fetch user email so you can recommend course for individual user
        url =  '' # URL to call to get recommended courses. Example: LXP_BASE_URL + COURSE_DETAILS_URL.format(email=email skills="")
        resp = get_resp('GET', url=url, headers=headers)
        json_resp = json.loads(json.dumps(resp.json()))
        json_resp=dict(json_resp)['cards']
        courses=[]
        for course in json_resp:
            if not course['duration']:
                continue
            course_obj = response_objects.CareerhubRecommendedCourseResponseType()
            self.__setup_career_planner_course_obj(course_obj, course)
            courses.append(course_obj.to_dict())
        return courses

"""
    - Create a handler function that responds appropriately to various triggers that you have subscribed to within Eightfold 
    - The event arg will contain all needed params to properly invoke your app
"""
def app_handler(event, context):
    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    print(f'Call recived for trigger_name: {trigger_name}')
    data = None

    try:
        lxp_adapter = LXPAdapter(app_settings)
        print(f'req_data: {req_data}')

      if trigger_name == 'careerhub_profile_course_attendance':
            data = lxp_adapter.get_attended_courses(req_data)
        elif trigger_name == 'careerhub_entity_search_results':
            data = lxp_adapter.get_course_search_results(req_data)
        elif trigger_name == 'careerhub_get_entity_details':
            data = lxp_adapter.get_course_details(req_data)
        elif trigger_name == 'career_planner_recommended_courses':
            data = lxp_adapter.get_recommended_coursesr(req_data)

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
