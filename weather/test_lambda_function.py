import mock
import unittest
import json
import lambda_function
from unittest.mock import MagicMock

class TestAppHandler(unittest.TestCase):
    def _return_value_generator(self, status_code, body_dict):
        return {
            'statusCode': status_code,
            'body': json.dumps({'data': body_dict})
        }

    @mock.patch('requests.get')
    def test_success(self, mock_request_get):
        weather_url_return = {
            'main':{
                'temp':25.55
            },
            'weather':[{
                'icon':'13d',
                'description': 'snow',
            }]
        }
        mm = MagicMock()
        mm.json.return_value = weather_url_return
        mock_request_get.return_value = mm

        event = {
            'trigger_name': 'career_hub_profile_view',
            'request_data':{
                'location': 'San Jose'
            }
        }
        context = {}
        ret = lambda_function.app_handler(event, context)
        body_dict = {
            'title': '25.6°F - Snow', 
            'subtitle': 'San Jose', 
            'logo_url': 'https://bmcdn.nl/assets/weather-icons/all/snow.svg'
        }
        self.assertEqual(ret, self._return_value_generator(200, body_dict))

    @mock.patch('requests.get')
    def test_no_location(self, mock_request_get):
        weather_url_return = {
            'main':{
                'temp':25.55
            },
            'weather':[{
                'icon':'13d',
                'description': 'snow',
            }]
        }
        mm = MagicMock()
        mm.json.return_value = weather_url_return
        mock_request_get.return_value = mm

        event = {
            'trigger_name': 'career_hub_profile_view',
            'request_data':{}
        }
        context = {}
        ret = lambda_function.app_handler(event, context)
        body_dict = {
            'title': 'Weather', 
            'error': 'Unable to find city for weather information.', 
            'logo_url': 'https://bmcdn.nl/assets/weather-icons/all/clear-day.svg'
        }
        self.assertEqual(ret, self._return_value_generator(200, body_dict))

    @mock.patch('requests.get')
    def test_request_get_error(self, mock_request_get):
        mock_request_get.side_effect = Exception('Too Many Attempts')

        event = {
            'trigger_name': 'career_hub_profile_view',
            'request_data':{'location': 'San Jose'}
        }
        context = {}
        ret = lambda_function.app_handler(event, context)
        body_dict = {
            'title': 'Weather',
            'error': 'Problem accessing weather information, please retry shortly.',
            'logo_url': 'https://bmcdn.nl/assets/weather-icons/all/clear-day.svg'
        }
        self.assertEqual(ret, self._return_value_generator(200, body_dict))

