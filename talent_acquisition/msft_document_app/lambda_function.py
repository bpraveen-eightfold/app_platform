import json
import requests
import traceback
import base64
from typing import Dict, Any, Optional, Union
from requests.exceptions import Timeout
from ef_app_sdk import EFAppSDK

CRT_PATH = 'certificate.crt'
KEY_PATH = 'private.key'

def error_response(error_str: str) -> Dict[str, Any]:
    """Error Response message"""
    error = {'error': error_str}
    print(json.dumps(error))
    return {
        'statusCode': 500,
        'body': json.dumps(error)
    }

class DocumentClient:
    def __init__(self, app_settings: Dict[str, Any], request_data: Dict[str, Any], app_sdk: EFAppSDK):
        """Initialize the Document Client.
        
        Args:
            app_settings: Application settings containing configuration
            request_data: Request data containing parameters
            app_sdk: EFAppSDK instance for logging
        """
        self.app_settings = app_settings
        self.request_data = request_data    
        self.base_url = app_settings.get('base_url', '')
        self.headers = self.get_headers()
        self.cert_path = self.get_cert_path()
        self.request_timeout = app_settings.get('request_timeout') or 4
        self.app_sdk = app_sdk

    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            'Ocp-Apim-Subscription-Key': self.app_settings.get('subscription_key', '')
        }
    
    def get_cert_path(self) -> tuple[str, str]:
        """Get certificate path tuple."""
        return (self.app_settings.get('crt_path') or CRT_PATH, self.app_settings.get('key_path') or KEY_PATH)

    def get_published_document(self) -> bytes:
        """Get published read-only document.
        
        Returns:
            bytes: Document content
            
        Raises:
            Exception: If request fails or required parameters are missing
        """
        url = self.request_data.get('url')
        url = self.base_url + url

        self.app_sdk.log(f'Invoking Document GET API for URL: {url}')
        
        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                cert=self.cert_path,
                timeout=self.request_timeout
            )
        except Timeout:
            raise Exception('Request timed out for GET document API.')

        if response.status_code != 200:
            raise Exception(f'Failed to get document. Status code: {response.status_code}. Reason: {response.reason}.')
        
        return response.content

    def get_signature_status(self) -> Dict[str, Any]:
        """Get document signature status.
        
        Returns:
            Dict[str, Any]: Signature status details
            
        Raises:
            Exception: If request fails or required parameters are missing
        """
        url = self.request_data.get('url')
        url = self.base_url + url
        self.app_sdk.log(f'Invoking Signature Status GET API for URL: {url}')
        
        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                cert=self.cert_path,
                timeout=self.request_timeout
            )
        except Timeout:
            raise Exception('Request timed out for GET signature status API.')

        if response.status_code != 200:
            raise Exception(f'Failed to get signature status. Status code: {response.status_code}. Reason: {response.reason}.')
        
        return response.json()

def app_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main handler function for the lambda.
    
    Args:
        event: Lambda event containing request data
        context: Lambda context
        
    Returns:
        Dict[str, Any]: Response with status code and body
    """
    app_sdk = EFAppSDK(context)
    app_sdk.log('Starting Document App Invocation')
    
    request_data = event.get('request_data', {})
    trigger_name = event.get('trigger_name')
    app_settings = event.get('app_settings', {})
    
    document_client = DocumentClient(app_settings, request_data, app_sdk)

    try:
        data = None
        if trigger_name == 'get_published_document':
            app_sdk.log('Handling get published document trigger')
            data = document_client.get_published_document()
            # Base64 encode binary data
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'data': base64.b64encode(data).decode('ascii')
                })
            }
        elif trigger_name == 'get_signature_status':
            app_sdk.log('Handling get signature status trigger')
            data = document_client.get_signature_status()
            return {
                'statusCode': 200,
                'body': json.dumps({'data': data})
            }

        if data is None:
            return error_response('Unknown trigger.')
        
    except Exception as ex:
        print('Something went wrong, traceback: {}'.format(traceback.format_exc()))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        } 
