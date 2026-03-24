import unittest
import requests_mock
import json
from fake_data import (
    recommended_course,
    search_courses,
    expected_homepage_recommended_course,
    inputs, token_string
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
# candidate id
candidate_id = "zk3jPZ"
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


class CareerhubHomepageRecommendedCoursesList(unittest.TestCase):
    """
    Given valid term
    test that a response returning by this trigger function is correctly as expected
    """
    def test_careerhub_homepage_recommended_courses_valid_term(self):
        # update request data with valid term and also update app setting
        event = {}
        request_data = {
            "limit": 10,
            "current_user_email": "payal.sonawane@redcrackle.com",
            "start": 0,
            "term": "Microsoft Office",
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

            filter_search_term = request_data.get("term")
            # get course api call with filter query
            url_without_nextBatch = (
                baseurl + "api/v2/content?filter%5Bterm%5D=" + filter_search_term
            )
            mock.get(
                url_without_nextBatch,
                headers=headers,
                status_code=200,
                json={"data": search_courses.get_data()},
            )
            # set expected response dict
            expected = expected_homepage_recommended_course.get_data_on_valid_term()
            # set extected course schema
            expected_course_schema = expected[0]
            # calling the function should return recommended course list
            response = lambda_function.careerhub_homepage_recommended_courses_handler(
                event, context=""
            )
            response_body = json.loads(response.get("body"))
            response_data = response_body.get("data")
            response_course_schema = response_data[0]
            # to check expected course schema should be equal to response course schema
            check_dict_keys = equal(expected_course_schema, response_course_schema)
            # assert statement to check expected and response
            self.assertTrue(check_dict_keys)
            self.assertEqual(len(response_data), len(expected))

    """
    Given valid fq
    test that a response returning by this trigger function is correctly as expected
    """
    def test_careerhub_homepage_recommended_courses_valid_fq(self):
        # update request data with valid fq and also update app setting
        event = {}
        request_data = {
            "limit": 10,
            "current_user_email": "payal.sonawane@redcrackle.com",
            "start": 0,
            "fq": {
                "position_skills": [
                    {"name": "Business Strategy"},
                    {"name": "Management"},
                    {"name": "Software Development"},
                    {"name": "Project Management"},
                    {"name": "Project Manager"},
                    {"name": "AWS"},
                    {"name": "Proofing"},
                ],
                "profile_skills": [{"name": "Management"}],
            },
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

            # mock recommended courses api
            candidate_id = "zk3jPZ"
            mock.get(
                baseurl + "/api/v2/users/" + candidate_id + "/required-learning",
                headers=headers,
                json={"data": recommended_course.get_data()},
            )
            # fake recommended courses
            recommended_courses = recommended_course.get_data()
            # traverse fake recommended courses
            for course in recommended_courses:
                # parse course id from course
                course_id = course["included"][0]["id"]
                # fake skills json
                skills = {"data": [{"type": "skills", "id": "Project Manager"}]}
                # mock course skills api
                mock.get(
                    baseurl + "/api/v2/content/" + course_id + "/skills",
                    json=skills,
                    headers=headers,
                )
                # fake course details json
                course_details = {
                    "data": {
                        "attributes": {
                            "employee-id": None,
                            "language": "en",
                            "assignment-type": "Assigned",
                        }
                    }
                }
                # mock course detail api
                mock.get(
                    baseurl + "/api/v2/content/" + str(course_id),
                    json=course_details,
                    headers=headers,
                )

            # filter_search_term = 'Proofing,Business Strategy,Project Management,Project Manager,Software Development,AWS'
            filter_search_term = lambda_function.get_search_string(
                request_data, lambda_function.concate_skills, ""
            )

            # get course api call with filter query
            url_without_nextBatch = (
                baseurl + "api/v2/content?filter%5Bterm%5D=" + filter_search_term
            )
            mock.get(
                url_without_nextBatch,
                headers=headers,
                status_code=200,
                json={"data": search_courses.get_data()},
            )

            # Mock completions api for filtering out completed courses
            mock.get(
                baseurl + "/api/v2/users/" + candidate_id + "/completions",
                json={"data": []},
                headers=headers,
            )

            # set expected response dict
            expected = expected_homepage_recommended_course.get_data_on_valid_fq()
            # set expected course schema
            expected_course_schema = expected[0]
            # calling the function should return recommended course list
            response = lambda_function.careerhub_homepage_recommended_courses_handler(
                event, context=""
            )
            response_body = json.loads(response.get("body"))
            response_data = response_body.get("data")
            response_course_schema = response_data[0]
            # to check expected course schema should be equal to entity schema
            check_dict_keys = equal(expected_course_schema, response_course_schema)
            # assert statement to check expected and response
            self.assertTrue(check_dict_keys)
            self.assertEqual(len(response_data), len(expected))
