import unittest
from parameterized import parameterized
import requests_mock
import json
from fake_data import search_courses, inputs, token_string
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa

# user inputs
inputData = inputs.app()
# request data
request_data = inputData.get("request_data", {})
# app setting
app_settings = inputData.get("app_settings", {})
# baseurl
baseurl = app_settings.get("edcast_base_url")
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
to check twp dict is equal or not
"""


def equal(a, b):
    if isinstance(a, dict):
        if len(a) != len(b):
            return False
        for key in a:
            if key not in b:
                return False
        return True


class CareerhubEntitySearchResultsTest(unittest.TestCase):
    """
    Given valid term
    test that a response returning by this trigger function is correctly as expected
    """

    @parameterized.expand(
        [
            ["Microsoft Office", "", search_courses.get_data(), 1, 200],
            ["", fq_skills, search_courses.get_data(), 1, 200],
            ["", "", search_courses.get_data(), 1, 200],
            ["Microsoft Office", "", [], 0, 500],
            ["Accounting", fq_skills, [], 0, 500],
        ]
    )
    def test_careerhub_entity_search_results_valid_term(
        self, term, fq, search_courses_data, search_courses_len, status_code
    ):
        # update request data with valid term and also update app setting
        event = {}
        request_data = {
            "limit": 10,
            "current_user_email": "payal.sonawane@redcrackle.com",
            "offset": 0,
            "term": term,
            "fq": fq,
        }
        event.update({"request_data": request_data, "app_settings": app_settings})

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

            # set expected response dict
            expected = {
                "entities": search_courses.entity_resp_data(),
                "num_results": search_courses_len,
                "limit": 10,
                "offset": 0,
                "cursor": "",
            }
            # set expected entity schema
            expected_entity_schema = expected.get("entities")[0]
            # calling the function should return filtered course list
            response = lambda_function.careerhub_entity_search_results_handler(
                event, context=""
            )
            response_body = json.loads(response.get("body"))
            response_data = response_body.get("data")
            response_entity_schema = expected.get("entities")[0]
            # to check expected course schema should be equal to entity schema
            check_dict_keys = equal(expected_entity_schema, response_entity_schema)
            # assert statement to check expected and response
            self.assertTrue(check_dict_keys)
            self.assertEqual(
                expected.get("num_results"), response_data.get("num_results")
            )
            self.assertEqual(
                expected.get("limit"),
                response_data.get("limit"),
            )
            self.assertEqual(expected.get("offset"), response_data.get("offset"))
            self.assertEqual(expected.get("cursor"), response_data.get("cursor"))
