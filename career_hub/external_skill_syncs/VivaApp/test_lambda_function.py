import mock
import unittest
import pytest
import json

from lambda_function import VivaClient
from ef_app_sdk import EFAppSDK

class TestLambdaFunction(unittest.TestCase):
    def setUp(self) -> None:
        context = mock.MagicMock()
        self.app_sdk = EFAppSDK(context)

    # TODO: remove this test once we fully migrate to oauth gate
    def test_get_cert_path(self):
        # no cert_path or key_path
        app_settings = {}
        viva_client = VivaClient(app_settings, {}, self.app_sdk)
        self.assertEqual(viva_client.cert_path, ('eightfold_viva_skills_auth.crt', 'eightfold_viva_skills_auth.key'))

        # with cert_path and key_path
        app_settings = {
            'crt_path': 'test.crt',
            'key_path': 'test.key'
        }
        viva_client = VivaClient(app_settings, {}, self.app_sdk)
        self.assertEqual(viva_client.cert_path, ('test.crt', 'test.key'))

    # TODO: remove this test once we fully migrate to oauth gate
    def test_get_employee_id(self):
        # request_data with empty app_settings
        request_data = {
            'employee_id': 12345
        }
        app_settings = {}
        viva_client = VivaClient(app_settings, request_data, self.app_sdk)
        self.assertEqual(viva_client.employee_id, 12345)

        # request_data with app_settings having test_employee_id
        app_settings = {
            'test_employee_id': 123
        }
        viva_client = VivaClient(app_settings, request_data, self.app_sdk)
        self.assertEqual(viva_client.employee_id, 123)

    @mock.patch('requests.get')
    def test_handle_sync_skills_trigger(self, mock_get):
        base_url = 'http://mock-api.test'
        app_settings = {
            'base_url_oauth': base_url,
            'base_url_certs': base_url,
            'endpoint_oauth': 'skills-dev/v2',
            'endpoint_certs': 'skills-dev/v2',
            'subscription_key': '12345'
        }

        # TEST OAUTH FLOW (EXTERNAL_SKILLS_OAUTH_GATE_ENABLED=TRUE)
        # Test missing OAuth token
        request_data = {}
        app_settings_oauth = app_settings.copy()
        app_settings_oauth['external_skills_oauth_gate_enabled'] = True
        viva_client = VivaClient(app_settings_oauth, request_data, self.app_sdk)
        with pytest.raises(Exception) as exc_info:
            viva_client.handle_sync_skills_trigger(request_data)
        assert str(exc_info.value) == 'OAuth token is missing.'

        # Test non 200 response
        mock_get.return_value = mock_get_resp = mock.MagicMock()
        mock_get_resp.status_code = 500
        mock_get_resp.reason = 'idk'
        request_data = {
            'oauth_token': 'test-token'
        }
        viva_client = VivaClient(app_settings_oauth, request_data, self.app_sdk)
        with pytest.raises(Exception) as exc_info:
            viva_client.handle_sync_skills_trigger(request_data)
        assert str(exc_info.value) == 'Failed to get skills. Status code: 500. Reason: idk.'
        
        expected_headers = {
            'Ocp-Apim-Subscription-Key': '12345',
            'Authorization': 'Bearer test-token'
        }
        mock_get.assert_called_with(
            f'{base_url}/skills-dev/v2',
            headers=expected_headers,
            timeout=4
        )
        mock_get.reset_mock()

        # Test successful response
        mock_get.return_value = mock_get_resp = mock.MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            'skills': []
        }
        result = viva_client.handle_sync_skills_trigger(request_data)
        mock_get.assert_called_once_with(
            f'{base_url}/skills-dev/v2',
            headers=expected_headers,
            timeout=4
        )
        self.assertEqual(result, {'skills': []})
        mock_get.reset_mock()

        # Test Certificate flow (external_skills_oauth_gate_enabled=False)
        # Test missing employee_id
        app_settings_cert = app_settings.copy()
        app_settings_cert['external_skills_oauth_gate_enabled'] = False
        empty_request_data = {}
        viva_client = VivaClient(app_settings_cert, empty_request_data, self.app_sdk)
        with pytest.raises(Exception) as exc_info:
            viva_client.handle_sync_skills_trigger(empty_request_data)
        assert str(exc_info.value) == 'Employee id is missing.'

        # Test non 200 response for Certificate flow
        mock_get.return_value = mock_get_resp = mock.MagicMock()
        mock_get_resp.status_code = 500
        mock_get_resp.reason = 'idk'
        request_data_with_id = {
            'employee_id': 12345
        }
        viva_client = VivaClient(app_settings_cert, request_data_with_id, self.app_sdk)
        with pytest.raises(Exception) as exc_info:
            viva_client.handle_sync_skills_trigger(request_data_with_id)
        assert str(exc_info.value) == 'Failed to get skills. Status code: 500. Reason: idk.'
        
        expected_headers_cert = {
            'Ocp-Apim-Subscription-Key': '12345'
        }
        mock_get.assert_called_with(
            f'{base_url}/skills-dev/v2/12345',
            headers=expected_headers_cert,
            cert=('eightfold_viva_skills_auth.crt', 'eightfold_viva_skills_auth.key'),
            timeout=4
        )
        mock_get.reset_mock()

        # Test successful response for Certificate flow
        mock_get.return_value = mock_get_resp = mock.MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            'data': [{'skill': 'Python'}]
        }
        result = viva_client.handle_sync_skills_trigger(request_data_with_id)
        mock_get.assert_called_once_with(
            f'{base_url}/skills-dev/v2/12345',
            headers=expected_headers_cert,
            cert=('eightfold_viva_skills_auth.crt', 'eightfold_viva_skills_auth.key'),
            timeout=4
        )
        self.assertEqual(result, [{'skill': 'Python'}])

    @mock.patch('requests.put')
    def test_handle_writeback_skills_trigger(self, mock_put):
        base_url = 'http://mock-api.test'
        app_settings = {
            'base_url_oauth': base_url,
            'base_url_certs': base_url,
            'endpoint_oauth': 'skills-dev/v2',
            'endpoint_certs': 'skills-dev/v2',
            'subscription_key': '12345'
        }
        skills_data = [{'skillName': 'Python', 'skillTags': ['UserConfirmed']}]
        
        # TEST OAUTH FLOW (EXTERNAL_SKILLS_OAUTH_GATE_ENABLED=TRUE)
        # Test missing OAuth token
        request_data = {'skills_data': skills_data}
        app_settings_oauth = app_settings.copy()
        app_settings_oauth['external_skills_oauth_gate_enabled'] = True
        viva_client = VivaClient(app_settings_oauth, request_data, self.app_sdk)
        with pytest.raises(Exception) as exc_info:
            viva_client.handle_writeback_skills_trigger(request_data)
        assert str(exc_info.value) == 'OAuth token is missing.'

        # Test non 200 response for OAuth flow
        mock_put.return_value = mock_put_resp = mock.MagicMock()
        mock_put_resp.status_code = 500
        mock_put_resp.reason = "idk"
        request_data = {
            'oauth_token': 'test-token',
            'skills_data': skills_data
        }
        viva_client = VivaClient(app_settings_oauth, request_data, self.app_sdk)
        with pytest.raises(Exception) as exc_info:
            viva_client.handle_writeback_skills_trigger(request_data)
        assert str(exc_info.value) == 'Failed to write skills. Status code: 500. Reason: idk.'
        
        expected_headers = {
            'Ocp-Apim-Subscription-Key': '12345',
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
        }
        expected_payload = json.dumps({'data': skills_data})
        mock_put.assert_called_with(
            f'{base_url}/skills-dev/v2',
            headers=expected_headers,
            data=expected_payload
        )
        mock_put.reset_mock()

        # Test successful response for OAuth flow
        mock_put.return_value = mock_put_resp = mock.MagicMock()
        mock_put_resp.status_code = 200
        result = viva_client.handle_writeback_skills_trigger(request_data)
        mock_put.assert_called_once_with(
            f'{base_url}/skills-dev/v2',
            headers=expected_headers,
            data=expected_payload
        )
        self.assertEqual(result, 200)
        mock_put.reset_mock()

        # Test Certificate flow (external_skills_oauth_gate_enabled=False)
        # Test missing employee_id
        app_settings_cert = app_settings.copy()
        app_settings_cert['external_skills_oauth_gate_enabled'] = False
        empty_request_data = {'skills_data': skills_data}
        viva_client = VivaClient(app_settings_cert, empty_request_data, self.app_sdk)
        with pytest.raises(Exception) as exc_info:
            viva_client.handle_writeback_skills_trigger(empty_request_data)
        assert str(exc_info.value) == 'Employee id is missing.'

        # Test non 200 response for Certificate flow
        mock_put.return_value = mock_put_resp = mock.MagicMock()
        mock_put_resp.status_code = 500
        mock_put_resp.reason = "idk"
        request_data_with_id = {
            'employee_id': 12345,
            'skills_data': skills_data
        }
        viva_client = VivaClient(app_settings_cert, request_data_with_id, self.app_sdk)
        with pytest.raises(Exception) as exc_info:
            viva_client.handle_writeback_skills_trigger(request_data_with_id)
        assert str(exc_info.value) == 'Failed to write skills. Status code: 500. Reason: idk.'
        
        expected_headers_cert = {
            'Ocp-Apim-Subscription-Key': '12345'
        }
        mock_put.assert_called_with(
            f'{base_url}/skills-dev/v2/12345',
            headers=expected_headers_cert,
            data=expected_payload,
            cert=('eightfold_viva_skills_auth.crt', 'eightfold_viva_skills_auth.key')
        )
        mock_put.reset_mock()

        # Test successful response for Certificate flow
        mock_put.return_value = mock_put_resp = mock.MagicMock()
        mock_put_resp.status_code = 200
        result = viva_client.handle_writeback_skills_trigger(request_data_with_id)
        mock_put.assert_called_once_with(
            f'{base_url}/skills-dev/v2/12345',
            headers=expected_headers_cert,
            data=expected_payload,
            cert=('eightfold_viva_skills_auth.crt', 'eightfold_viva_skills_auth.key')
        )
        self.assertEqual(result, 200)
        
        # Test test_writeback_code override
        app_settings_with_test_code = app_settings.copy()
        app_settings_with_test_code['test_writeback_code'] = 204
        viva_client = VivaClient(app_settings_with_test_code, {}, self.app_sdk)
        result = viva_client.handle_writeback_skills_trigger({})
        self.assertEqual(result, 204)
