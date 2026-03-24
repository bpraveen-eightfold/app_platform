import json
import requests

from base import AvailabilityOAuthCredentials, AvailabilityCredentials
from constants import MeraRequestAttributes, EFResponseAttributes
from exceptions import AvailabilityAppException


class MeraAvailabilityAdapter:
    """ Adapter for Mera """

    @staticmethod
    def _get_credentials(app_settings):
        credentials = AvailabilityCredentials()
        credentials.api_url = app_settings['api_url']
        credentials.oauth = MeraAvailabilityAdapter._get_oauth_credentials(app_settings['oauth_settings'])
        return credentials

    @staticmethod
    def _get_oauth_credentials(oauth_settings):
        oauth_credentials = AvailabilityOAuthCredentials()
        oauth_credentials.url = oauth_settings.get('url')
        oauth_credentials.grant_type = oauth_settings.get('grant_type')
        oauth_credentials.client_id = oauth_settings.get('client_id')
        oauth_credentials.client_secret = oauth_settings.get('client_secret')
        oauth_credentials.resource = oauth_settings.get('resource')
        return oauth_credentials

    @staticmethod
    def call(url, http_method='GET', headers=None, data=None):
        """ Utility method to make the remote API call """
        if http_method == 'GET':
            resp = requests.get(url=url, headers=headers, data=data)
        elif http_method == 'POST':
            resp = requests.post(url=url, headers=headers, data=data)
        else:
            raise RuntimeError(f'Invalid HTTP method {http_method}')
        return resp

    @staticmethod
    def _get_resp_json(url, http_method, headers=None, data=None):
        resp = MeraAvailabilityAdapter.call(
            url=url,
            headers=headers,
            http_method=http_method,
            data=data
        )

        if resp.status_code != 200:
            raise AvailabilityAppException(message=resp.reason, status_code=resp.status_code)

        return json.loads(resp.content) if resp.content else {}

    @staticmethod
    def _get_oauth_token(credentials):
        """ Returns the oauth token """
        data = {
            'grant_type': credentials.oauth.grant_type,
            'client_id': credentials.oauth.client_id,
            'client_secret': credentials.oauth.client_secret,
            'resource': credentials.oauth.resource
        }

        resp_json = MeraAvailabilityAdapter._get_resp_json(
            url=credentials.oauth.url,
            http_method='GET',
            data=data
        )
        return f"{resp_json.get('token_type')} {resp_json.get('access_token')}"

    @staticmethod
    def _get_url_content(url, credentials, http_method='GET', data=None):
        headers = {
            'Authorization': MeraAvailabilityAdapter._get_oauth_token(credentials),
            'Content-Type': 'application/json',
            'User-Agent': ''
        }
        return MeraAvailabilityAdapter._get_resp_json(
            url=url,
            http_method=http_method,
            data=json.dumps(data) if data else None,
            headers=headers)

    @staticmethod
    def prepare_request(request_data):
        employee_ids, start_date, end_date = request_data['employee_ids'], request_data['start_date'], request_data['end_date']
        return {
            MeraRequestAttributes.GPNIDS: list(map(lambda x: {'gpn': x, 'order': 1}, employee_ids)),
            MeraRequestAttributes.START_DATE: start_date,
            MeraRequestAttributes.END_DATE: end_date
        }

    @staticmethod
    def process_response(response):
        ef_to_mera_response_map = EFResponseAttributes.get_ef_to_mera_response_map()

        processed_resp = []
        for empl_availability_data in response:
            processed_resp.append({ef_resp_attr: empl_availability_data[mera_resp_attr]
                for ef_resp_attr, mera_resp_attr in ef_to_mera_response_map.items()})

        return processed_resp

    @staticmethod
    def fetch_availability(app_settings, request_data):
        """ Fetch availability """
        data = MeraAvailabilityAdapter.prepare_request(request_data)
        credentials = MeraAvailabilityAdapter._get_credentials(app_settings)

        resp = MeraAvailabilityAdapter._get_url_content(
            url=credentials.api_url,
            credentials=credentials,
            http_method='POST',
            data=data
        )
        return MeraAvailabilityAdapter.process_response(resp)
