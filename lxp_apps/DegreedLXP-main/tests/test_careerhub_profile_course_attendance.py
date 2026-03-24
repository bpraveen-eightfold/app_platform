import unittest
from parameterized import parameterized
import requests_mock
import json
from fake_data import (
    course_attendance_api_response,
    expected_course_attendance_response,
    inputs,
    token_string,
)
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa

# user inputs
inputData = inputs.app()
# request data
request_data = inputData.get("request_data", {})
# app setting
app_settings = inputData.get("app_settings", {})
# degree baseurl
degreed_base_url = app_settings.get("degreed_base_url")
# baseurl
baseurl = "https://api." + degreed_base_url + "/"
# token_url
token_url = "https://" + degreed_base_url
# language
language = "en"
# get token
token = token_string.get_token_string()
# headers
headers = {"Authorization": "Bearer " + str(token)}
email = lambda_function.get_email(request_data, app_settings)

"""
to check twp dict is equal or not
"""


def equal(a, b):
    type_a = type(a)
    type_b = type(b)

    if type_a != type_b:
        return False

    if isinstance(a, dict):
        if len(a) != len(b):
            return False
        for key in a:
            if key not in b:
                return False
        return True


class CareerhubProfileCourseAttendanceTest(unittest.TestCase):
    def test_get_sorted_attendance(self):
        attendance = [
            {
                'lms_course_id': 'aaa',
                'completion_date': None,
                'start_date': None,
            },
            {
                'lms_course_id': 'bbb',
                'completion_date': 12,
                'start_date': 12,
            },
            {
                'lms_course_id': 'ccc',
                'completion_date': 123,
                'start_date': 23,
            },
            {
                'lms_course_id': 'ddd',
                'completion_date': 234,
                'start_date': 34,
            },
            {
                'lms_course_id': 'eee',
                'completion_date': None,
                'start_date': None,
            },
            {
                'lms_course_id': 'fff',
                'completion_date': 99,
                'start_date': 99,
            },
        ]
        sorted_attendance = lambda_function._get_sorted_attendance(attendance)
        self.assertEqual(sorted_attendance, [
            {
                'lms_course_id': 'ddd',
                'completion_date': 234,
                'start_date': 34,
            },
            {
                'lms_course_id': 'ccc',
                'completion_date': 123,
                'start_date': 23,
            },
            {
                'lms_course_id': 'fff',
                'completion_date': 99,
                'start_date': 99,
            },
            {
                'lms_course_id': 'bbb',
                'completion_date': 12,
                'start_date': 12,
            },
            {
                'lms_course_id': 'aaa',
                'completion_date': None,
                'start_date': None,
            },
            {
                'lms_course_id': 'eee',
                'completion_date': None,
                'start_date': None,
            },
        ])

    """
    Given valid email
    test that a response returning by this trigger function is correctly as expected
    """
    @parameterized.expand([
        ["payal.sonawane@redcrackle.com", 200, 3],
        ["payal.sonaw@redcrackle.com", 500, {"statusCode": 500, "body": 
                '{"error": "Could not find course attendance list. Status code: 500. Reason: None."}'}]
    ])
    def test_careerhub_profile_course_attendance_valid_email(self, candidate_email, user_id_status_code,
                                                             expected):
        # update request data with valid email
        event = {}
        request_data = {
            "trigger_name": "careerhub_profile_course_attendance",
            "email": candidate_email,
        }
        event.update({"request_data": request_data, "app_settings": app_settings})
        # The Mocker object working as a context manager.
        with requests_mock.Mocker() as mock:
            # mock access token api
            access_token_return_json = {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 5183999,
                "refresh_token": "4cfc971e671a4cc5afbda32527f6e9c472bdfc6c77c64ee7a6fdc8a2f6e5a54b",
            }
            mock.post(
                token_url + "/oauth/token", json=access_token_return_json, status_code=200
            )

            # mock get use id api
            get_userid_return_json = {"data": {"type": "users", "id": "zk3jPZ"}}
            mock.get(
                baseurl + "api/v2/users/" + email + "?identifier=email",
                json=get_userid_return_json,
                status_code=200,
            )
            if user_id_status_code == 200:
                # candidate id
                candidate_id = "zk3jPZ"
                # mock api to get profile attendance details
                mock.get(
                    baseurl + "/api/v2/users/" + candidate_id + "/completions",
                    json={"data": course_attendance_api_response.get_data()},
                    headers=headers,
                )
                # set expected course attendance list
                expected_profile_schema = expected_course_attendance_response.get_data()[0]
                # calling the function should return course attendance list
                response = lambda_function.careerhub_profile_course_attendance_handler(
                    event, context=""
                )
                response_body = json.loads(response.get("body"))
                response_data = response_body.get("data")
                response_profile_schema = response_data[0]
                # to check expected course schema should be equal to response course schema
                check_dict_keys = equal(expected_profile_schema, response_profile_schema)
                # check asert statement
                self.assertTrue(check_dict_keys)
                self.assertEqual(expected, len(response_data))
            else:
                # candidate id
                candidate_id = "zk3jPZ"
                mock.get(
                    baseurl + "/api/v2/users/" + candidate_id + "/completions",
                    status_code=user_id_status_code,
                    json={"error": "Could not get attendance course detail."},
                    headers=headers,
                )
                # calling the function should return 500 status code
                response = lambda_function.careerhub_profile_course_attendance_handler(
                    event, context=""
                )

                self.assertEqual(expected.get("statusCode"), response.get("statusCode"))
                self.assertEqual(expected.get("body"), response.get("body"))
