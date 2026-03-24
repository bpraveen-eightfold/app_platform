import unittest
from parameterized import parameterized
import requests_mock
import json
from fake_data import entity_details, inputs, token_string
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa

# user inputs
inputData = inputs.app()
# request data
request_data = inputData.get("request_data", {})
# app setting
app_settings = inputData.get("app_settings", {})
# edcast baseurl
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


class CareerhubGetEntityDetailsTest(unittest.TestCase):
    """
    Given valid entity id
    test that a response returning by this trigger function is as expected
    """

    @parameterized.expand(
        [
            [
                "ECL-05b7ab0f-b0ec-4345",
                200,
                entity_details.get_data_sample1(),
                entity_details.entity_resp_data_sample1(),
            ],
            [
                "ECL-05b7ab0f-b0ec-4322",
                200,
                entity_details.get_data_sample2(),
                entity_details.entity_resp_data_sample2(),
            ],
            ["xyz", 500, "fake data", 500],
        ]
    )
    def test_careerhub_get_entity_details_valid_entity_id(
        self, entity_id, status_code, samples, expected
    ):
        # update given request data with valid entity id
        event = {}
        request_data = {
            "current_user_email": "payal.sonawane@redcrackle.com",
            "entity_id": entity_id,
        }
        event.update({"request_data": request_data, "app_settings": app_settings})
        entity_id = request_data.get("entity_id", 0)

        # The Mocker object working as a context manager.
        with requests_mock.Mocker() as mock:
            # mock access token api
            access_token_return_json = access_token_return_json_data
            mock.get(baseurl + "/auth", json=access_token_return_json, status_code=200)

            # get course api call with filter query
            url_params = baseurl + "/cards/" + str(entity_id)

            # mock api to get entity details
            mock.get(
                url_params,
                headers=headers,
                status_code=status_code,
                json=samples,
            )
            # # calling the function which will return entity details
            response = lambda_function.careerhub_get_entity_details_handler(
                event, context=""
            )
            print(response)
            if status_code == 200:
                response_body = json.loads(response.get("body"))
                response_data = response_body.get("data")
                # to check expected entity schema and response entity schema is equal or not
                check_dict_keys = equal(expected, response_data)
                self.assertTrue(check_dict_keys)
                self.assertEqual(expected, response_data)
            else:
                self.assertEqual(response.get("statusCode"), expected)
