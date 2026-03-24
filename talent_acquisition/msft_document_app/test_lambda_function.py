import json
import sys
import pytest
from unittest.mock import MagicMock, patch
from lambda_function import DocumentClient, app_handler

@pytest.fixture
def mock_app_sdk():
    """Fixture for mocked EFAppSDK."""
    mock = MagicMock()
    mock.log = MagicMock()
    return mock

@pytest.fixture
def mock_context():
    """Fixture for lambda context."""
    return MagicMock()

@pytest.fixture
def app_settings():
    """Fixture for app settings."""
    return {
        'base_url': 'https://api.example.com',
        'subscription_key': 'test-key',
        'request_timeout': 5,
        'crt_path': '/path/to/cert.crt',
        'key_path': '/path/to/key.pem'
    }

@pytest.fixture
def document_request_data():
    """Fixture for document request data."""
    return {
        'entity_id': '123',
        'document_type': 'OfferLetter',
        'doc_version': '2.0',
        'api_version': '1.0'
    }

@pytest.fixture
def signature_request_data():
    """Fixture for signature status request data."""
    return {
        'entity_id': '123',
        'document_type': 'OfferLetter',
        'workflow_id': '456',
        'candidate_email': 'test@example.com',
        'api_version': '1.0'
    }

def test_get_published_document_success(mock_app_sdk, app_settings, document_request_data):
    """Test successful retrieval of published document."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'test document content'
        mock_get.return_value = mock_response

        with patch('lambda_function.DocumentClient.get_cert') as mock_get_cert:
            mock_get_cert.return_value = ('cert.pem', 'key.pem')
            client = DocumentClient(app_settings, document_request_data, mock_app_sdk)
            result = client.get_published_document()

            assert result == b'test document content'
            mock_get.assert_called_once()
            assert mock_app_sdk.log.called

def test_get_published_document_missing_params(mock_app_sdk, app_settings):
    """Test document retrieval with missing parameters."""
    client = DocumentClient(app_settings, {}, mock_app_sdk)
    
    with pytest.raises(Exception) as exc_info:
        client.get_published_document()
    
    assert "Missing required parameters" in str(exc_info.value)

def test_get_signature_status_success(mock_app_sdk, app_settings, signature_request_data):
    """Test successful retrieval of signature status."""
    expected_response = {
        'memberEmail': 'test@example.com',
        'signStatus': 'COMPLETED',
        'statusDateTime': '2024-01-01T00:00:00Z'
    }

    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        client = DocumentClient(app_settings, signature_request_data, mock_app_sdk)
        result = client.get_signature_status()

        assert result == expected_response
        mock_get.assert_called_once()
        assert mock_app_sdk.log.called

def test_get_signature_status_missing_params(mock_app_sdk, app_settings):
    """Test signature status retrieval with missing parameters."""
    client = DocumentClient(app_settings, {}, mock_app_sdk)
    
    with pytest.raises(Exception) as exc_info:
        client.get_signature_status()
    
    assert "Missing required parameters" in str(exc_info.value)

def test_app_handler_get_published_document(mock_context, app_settings, document_request_data):
    """Test app handler with get_published_document trigger."""
    event = {
        'trigger_name': 'get_published_document',
        'app_settings': app_settings,
        'request_data': document_request_data
    }

    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'test document content'
        mock_get.return_value = mock_response

        with patch('lambda_function.DocumentClient.get_cert') as mock_get_cert:
            mock_get_cert.return_value = ('cert.pem', 'key.pem')
            result = app_handler(event, mock_context)

            assert result['statusCode'] == 200
            assert result['body'] == b'test document content'

def test_app_handler_get_signature_status(mock_context, app_settings, signature_request_data):
    """Test app handler with get_signature_status trigger."""
    event = {
        'trigger_name': 'get_signature_status',
        'app_settings': app_settings,
        'request_data': signature_request_data
    }

    expected_response = {
        'memberEmail': 'test@example.com',
        'signStatus': 'COMPLETED',
        'statusDateTime': '2024-01-01T00:00:00Z'
    }

    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = app_handler(event, mock_context)

        assert result['statusCode'] == 200
        assert json.loads(result['body'])['data'] == expected_response

def test_app_handler_unknown_trigger(mock_context, app_settings):
    """Test app handler with unknown trigger."""
    event = {
        'trigger_name': 'unknown_trigger',
        'app_settings': app_settings,
        'request_data': {}
    }

    result = app_handler(event, mock_context)

    assert result['statusCode'] == 500
    assert 'Unknown trigger' in json.loads(result['body'])['error']

def test_app_handler_error_handling(mock_context, app_settings, document_request_data):
    """Test app handler error handling."""
    event = {
        'trigger_name': 'get_published_document',
        'app_settings': app_settings,
        'request_data': document_request_data
    }

    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception('Test error')
        with patch('lambda_function.DocumentClient.get_cert') as mock_get_cert:
            mock_get_cert.return_value = ('cert.pem', 'key.pem')
            result = app_handler(event, mock_context)

            assert result['statusCode'] == 500
            assert 'Test error' in json.loads(result['body'])['error'] 