import unittest

from lambda_function import app_handler


def get_actions_from_response(response):
    body = response.get('body')
    return body.get('data').get('actions')


class TestAppHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.app_settings = {
            "ef_api_key": "Basic gmqiqirrrulqbkewolymdcxowxylxqft",
            "request_fields": ["positionId", "name"],
            "reference_name_suffix": "Reference",
            "should_confirm_calibration": True,
            "position_title_field": "name",
            "copy_from_role_calibration_template": False
        }

        self.calibration_template_app_settings = {
            "ef_api_key": "Basic gmqiqirrrulqbkewolymdcxowxylxqft",
            "request_fields": ["positionId", "name", "role.templates"],
            "reference_name_suffix": "Reference",
            "should_confirm_calibration": True,
            "copy_from_role_calibration_template": True
        }

        self.request_data = {
            'positionId': '7549978',
            'name': 'Senior Analyst',
            "role": {
                "templates": [
                    {
                        "name": "Analyst",
                        "id": 1
                    },
                    {
                        "name": "Business Analyst",
                        "id": 2
                    },
                    {
                        "name": "Dummy Position China",
                        "id": 3
                    }
                ]
            }
        }

    def test_successful_search(self):
        self.request_data['name'] = 'Software Engineer'
        response = app_handler({
            'request_data': self.request_data,
            'app_settings': self.app_settings
        }, None)
        assert response.get('statusCode') == 200
        action = get_actions_from_response(response)[0]
        assert action.get('action_name') == 'entity_update_action'
        assert action.get('request_data').get('confirm_calibration')
        assert action.get('request_data').get('update_payload').get('custom_info.calibration_template_id')

    def test_successful_match(self):
        response = app_handler({
            'request_data': self.request_data,
            'app_settings': self.calibration_template_app_settings
        }, None)
        assert response.get('statusCode') == 200
        action = get_actions_from_response(response)[0]
        assert action.get('action_name') == 'entity_update_action'
        assert action.get('request_data').get('confirm_calibration')
        assert action.get('request_data').get('update_payload').get('custom_info.calibration_template_id') == 1

    def test_successful_match_on_country(self):
        self.request_data['locations'] = ['China']
        response = app_handler({
            'request_data': self.request_data,
            'app_settings': self.calibration_template_app_settings
        }, None)
        assert response.get('statusCode') == 200
        action = get_actions_from_response(response)[0]
        assert action.get('action_name') == 'entity_update_action'
        assert action.get('request_data').get('confirm_calibration')
        assert action.get('request_data').get('update_payload').get('custom_info.calibration_template_id') == 3

    def test_successful_match_on_default_english(self):
        self.request_data['locations'] = ['United Kingdom']
        self.request_data['role']['templates'][0]['name'] = 'Analyst United states of America'
        response = app_handler({
            'request_data': self.request_data,
            'app_settings': self.calibration_template_app_settings
        }, None)
        assert response.get('statusCode') == 200
        action = get_actions_from_response(response)[0]
        assert action.get('action_name') == 'entity_update_action'
        assert action.get('request_data').get('confirm_calibration')
        assert action.get('request_data').get('update_payload').get('custom_info.calibration_template_id') == 2
