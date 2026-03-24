# pylint: disable=ef-restricted-imports, unused-variable, unused-import
"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import
import random
import json
import traceback

import response_objects
from base_adapter import BaseAdapter

NUM_COURSES = 10000 # Arbitrary number of dummy courses
NUM_CAREER_PLANNER_COURSES = 12

class TestAdapter(BaseAdapter):
    def __init__(self, app_settings):
        self.app_settings = app_settings

    def get_current_courses(self, req_data, app_settings):
        if app_settings.get('error_cases', {}).get('course_attendance_user_not_found'):
            raise ValueError('User not found')
        courses=[]
        for i in range(5): # Arbitrary number of current courses
            course_obj = response_objects.ProfileCourseAttendanceResponseType()
            course_obj.title = 'Title {}'.format(i)
            course_obj.course_url = 'https://app.eightfold.ai'
            course_obj.provider = 'Test Provider'
            course_obj.duration = i + 1
            courses.append(course_obj.to_dict())
        return courses

    def _get_test_html_description(self):
        return '''<p><b>bold</b></p> <p><i>italics</i></p> <p><u>underline</u></p> <ul><li>Bullet 1</li><li>Bullet 2</li></ul>'''

    def _get_test_custom_sections(self):
        return [
            {'header': 'test header', 'body': 'test body'},
            {'header': 'test header 2', 'body': '<ul><li>Test</li><li>Bullets</li></ul>'},
        ]

    def _setup_course_obj(self, course_obj, i):
        course_obj.entity_id = i
        course_obj.title = 'Title {}'.format(i)
        course_obj.description = 'Description {}'.format(i) + self._get_test_html_description()
        course_obj.source_name = 'Test Provider'
        course_obj.image_url = 'https://static.vscdn.net/images/logos/eightfold_logo_no_text.svg'
        # Test that having no CtaUrl at entity 0 makes no button show up
        course_obj.cta_url = 'https://app.eightfold.ai' if i != 0 else ''
        course_obj.cta_label = 'View Course'
        course_obj.card_label = 'Test'
        fields = []
        course_type = 'test type'
        fields.append({'name': 'Type', 'value': course_type})
        language = 'test language'
        fields.append({'name': 'Language', 'value': language})
        duration_hours = i + 1
        fields.append({'name': 'Duration Hours', 'value': duration_hours})
        category = 'test category'
        fields.append({'name': 'Category', 'value': category})
        course_obj.fields = fields
        course_obj.custom_sections = self._get_test_custom_sections()

    def _get_start_idx_using_term(self, term):
        if not term:
            return 0
        # generate start_idx randomly
        random.seed(term)
        # using minus 10 in endrange to make sure to return at least 10 courses
        return random.randint(0, NUM_COURSES - 10)

    def get_courses_search_results(self, req_data, app_settings):
        if app_settings.get('error_cases', {}).get('search_results_user_not_found'):
            raise ValueError('User not found')
        if app_settings.get('error_cases', {}).get('search_results_no_entites'):
            courses = response_objects.CareerhubEntitySearchResultsResponseType()
            courses.entities = []
            courses.num_results = 0
            return courses.to_dict()
        if app_settings.get('use_cursor_based_pagination'):
            if req_data.get('cursor'):
                start = int(req_data['cursor'])
            else:
                start = self._get_start_idx_using_term(req_data.get('term'))
        else:
            if req_data.get('start') == 0:
                start = self._get_start_idx_using_term(req_data.get('term'))
            else:
                start = req_data.get('start')
        limit = req_data.get('limit')
        courses = response_objects.CareerhubEntitySearchResultsResponseType()
        courses.entities = []
        if app_settings.get('error_cases', {}).get('no_search_results'):
            return courses.to_dict()
        # Dummy search behavior: parse search term as an int, then get all "courses"
        # with id less than that int
        try:
            search_id = int(req_data.get('term'))
        except:
            search_id = NUM_COURSES
        # Should return total number of search results in num_results, not just how many returned (up to limit)
        courses.num_results = min(search_id, NUM_COURSES)
        end = min(start + limit, search_id, NUM_COURSES)
        for i in range(start, end):
            course_obj = response_objects.CareerhubEntityDetailsResponseType()
            self._setup_course_obj(course_obj, i)
            courses.entities.append(course_obj.to_dict())
        # set cursor before returning the results
        if app_settings.get('use_cursor_based_pagination'):
            courses.cursor = str(end)
        return courses.to_dict()

    def get_course_details(self, req_data, app_settings):
        try:
            course_id = int(req_data.get('entity_id'))
        except:
            course_id = 0
        if app_settings.get('error_cases', {}).get('entity_details_entity_not_found'):
            raise ValueError("Couldn't find course with entity_id: {}".format(course_id))
        course_obj = response_objects.CareerhubEntityDetailsResponseType()
        self._setup_course_obj(course_obj, course_id)
        return course_obj.to_dict()

    def _setup_career_planner_course_obj(self, course_obj, i):
        course_obj.lms_course_id = i
        course_obj.title = 'Title {}'.format(i)
        course_obj.description = 'Description {}'.format(i)
        course_obj.course_type = 'course'
        course_obj.language = 'en'
        #supposing the course_duration is returned in seconds-> converting to hours
        course_obj.duration_hours = i + 1
        #course_obj.published_date = course['createdAt'] # of format 2020-10-22T11:06:53.000Z
        course_obj.course_url = 'https://app.eightfold.ai'
        course_obj.image_url = 'https://static.vscdn.net/images/logos/eightfold_logo_no_text.svg'
        course_obj.provider = 'Eightfold Test'
        #course_obj.skills = course['provider']
        course_obj.lms_data = {}

    def get_courses_for_career_planner(self, req_data, app_settings):
        if app_settings.get('error_cases', {}).get('career_planner_user_not_found'):
            raise ValueError('User not found')
        courses=[]
        courses = []
        for i in range(NUM_CAREER_PLANNER_COURSES):
            course_obj = response_objects.CareerPlannerCourseResponseType()
            self._setup_career_planner_course_obj(course_obj, i)
            courses.append(course_obj.to_dict())
        return courses

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
        ta = TestAdapter(app_settings)
        if trigger_name == 'careerhub_profile_course_attendance':
            data = ta.get_current_courses(req_data, app_settings)
        elif trigger_name == 'careerhub_entity_search_results':
            print('req_data: {}'.format(req_data))
            data = ta.get_courses_search_results(req_data, app_settings)
        elif trigger_name == 'careerhub_get_entity_details':
            data = ta.get_course_details(req_data, app_settings)
        elif trigger_name == 'career_planner_recommended_courses':
            data = ta.get_courses_for_career_planner(req_data, app_settings)
    except Exception as ex:
        err_str = 'Handler for trigger_name: {} failed with error: {}, traceback: {}'.format(
            trigger_name, str(ex), traceback.format_exc())
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
        'body': json.dumps({'data': data, 'cache_ttl_seconds': 60})
    }
