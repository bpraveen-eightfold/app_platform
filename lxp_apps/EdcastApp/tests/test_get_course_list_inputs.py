import unittest
from parameterized import parameterized
import requests_mock
from fake_data import inputs, search_courses, token_string
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa

# user inputs
inputData = inputs.app()
# request data
request_data = inputData.get("request_data", {})
# app setting
app_settings = inputData.get("app_settings", {})

# degree baseurl
edcast_base_url = app_settings.get("edcast_base_url")
# baseurl
baseurl = edcast_base_url
# email
email = app_settings.get("edcast_test_email")
# language
language = "en"
# get token
token = token_string.get_token_string()
# api key
api_key = app_settings.get("edcast_api_key")
# headers
headers = {
    "X-API-KEY": api_key,
    "X-ACCESS-TOKEN": token,
    "Content-Type": "application/json",
}
# access token return json data
access_token_return_json_data = {
    "jwt_token": "nkdnlkikjf4753408yhlsdkbfhb43rgcdjbvjkh8fyu"
}

fq_skills = {
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
}

"""
to check two dict is equal or not
"""


def equal(a, b):
    if isinstance(a, dict):
        if len(a) != len(b):
            return False
        for key in a:
            if key not in b:
                return False
        return True


class CourseListInputsTest(unittest.TestCase):
    @parameterized.expand(
        [
            ["Microsoft Office", "", search_courses.get_data(), 1, 200],
            ["", fq_skills, search_courses.get_data(), 1, 200],
            ["", "", search_courses.get_data(), 1, 200],
            ["Accounting", fq_skills, [], 0, 404],
            ["", fq_skills, [], 0, 500],
            ["", "", [], 0, 500],
        ]
    )
    def test_get_combined_courses(
        self, term, fq, search_courses_data, course_len, status_code
    ):
        request_data = {
            "limit": 10,
            "current_user_email": "payal.sonawane@redcrackle.com",
            "offset": 0,
            "term": term,
            "fq": fq,
        }
        # The Mocker object working as a context manager.
        with requests_mock.Mocker() as mock:
            # mock access token api
            access_token_return_json = access_token_return_json_data
            mock.get(baseurl + "/auth", json=access_token_return_json, status_code=200)

            filter_search_term = lambda_function.get_search_string(
                request_data, lambda_function.concate_skills, ""
            )

            # get course api call with filter query
            url_params = (
                baseurl
                + "/cards/search?q="
                + filter_search_term
                + "&offset="
                + str(request_data.get("offset"))
                + "&limit="
                + str(request_data.get("limit"))
            )
            if filter_search_term == "":
                url_params = lambda_function.course_url_format(url_params)

            mock.get(
                url_params,
                headers=headers,
                status_code=status_code,
                json={"cards": search_courses_data},
            )

            expected = {
                "course_list": search_courses_data,
                "course_len": course_len,
                "limit": 10,
                "offset": 0,
            }
            response = lambda_function.get_course_list_inputs(
                request_data, app_settings, email
            )
            # to check expected course schema should be equal to response course schema
            check_dict_keys = equal(expected, response)
            # assert statement to check expected and response
            self.assertTrue(check_dict_keys)
            self.assertEqual(expected, response)
            self.assertEqual(expected.get("course_len"), response.get("course_len"))
