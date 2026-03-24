import datetime
import time
from datetime import datetime as dt
from db import table_registry
from db.redshift_utils import RedshiftClient
from db.table_registry import UnknownTableException
from functools import wraps
from incremental_exporter_constants import ACCESS_TOKEN_URL
from incremental_exporter_constants import AUTHORIZATION_TOKEN_MAP
from incremental_exporter_constants import DATA_FILE
from incremental_exporter_constants import EF_DEBUG_LOG_PREFIX
from incremental_exporter_constants import META_FILE
from utils import sftp_utils
from utils import time_utils
from utils import url_utils

import glog as log
import requests


NUM_ROWS_TO_FLUSH = 2000 # Number of rows to flush data once to avoid OOM


class DownloadFailedExcpetion(Exception):
    pass

class APIConnectionException(Exception):
    pass


class DeliveryTimeException(Exception):
    pass

class IncorrectOutputFileFormatException(Exception):
    pass

class ApiConnector:

    def __init__(self, oauth_username, oauth_password, api_host=None, region='us-west-2'):
        self.oauth_username = oauth_username
        self.oauth_password = oauth_password
        self.region = region

        self.data = {
            "grantType": "password",
            "username": self.oauth_username,
            "password": self.oauth_password
        }

        self.oauth_headers = {
            'Authorization': AUTHORIZATION_TOKEN_MAP.get(self.region)
        }
        self.access_token = None
        self.api_host = api_host or get_api_host(region) # We can internally pass api_host. Otherwise, fall back to prod by region
        self.access_token_url = f'{self.api_host}{ACCESS_TOKEN_URL}'

    def _connect(self):
        self._fetch_access_token()

    def _fetch_access_token(self):
        try:
            res = requests.post(self.access_token_url, json=self.data, headers=self.oauth_headers)
            self.access_token = res.json().get('data', {}).get('access_token')
            if not self.access_token:
                raise APIConnectionException('Get Empty Access Token')
        except Exception as e:
            log.error(f'Error fetching access token: {str(e)}')
            raise APIConnectionException(e)

    def get_headers(self):
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }
        return headers

    def get_request(self, url, params, timeout=300):
        full_url = f'{self.api_host}/{url.strip("/")}'
        if not self.access_token:
            self._connect()
        print(EF_DEBUG_LOG_PREFIX + f'Get: {full_url} with param_dict {params}')
        return get_request_with_retries(full_url, headers=self.get_headers(), params=params, timeout=timeout)

    def post_request(self, url, json, timeout=300):
        full_url = f'{self.api_host}/{url.strip("/")}'
        if not self.access_token:
            self._connect()
        print(EF_DEBUG_LOG_PREFIX + f'Post: {full_url} with param_dict {json}')
        return post_request_with_retries(full_url, headers=self.get_headers(), json=json, timeout=timeout)


def generate_output_message(breakdown_runtime, group_id, breakdown_changelog_size=None, traceback=None, ex=None):
    msg = ''
    if ex or traceback:
        return f'Failed to export data for group_id: {group_id}. With Exception {str(ex)}. Traceback: {traceback}'

    msg += f'Successfully export data for group_id: {group_id}\n\nTime Taken:\n'
    for tablename, runtime in breakdown_runtime.items():
        msg += f'{tablename}: {round(runtime, 2)}s\n'
    if breakdown_changelog_size:
        msg += '\n\nNumber of Changelog Ids:\n'
        for tablename, changelog_size in breakdown_changelog_size.items():
            msg += f'{tablename}: {changelog_size}\n'
    msg += '-' * 20 + '\n'
    return msg

def generate_error_message_for_non_pass_tables(non_passes_detail):
    msg = 'The following tables were not completely exported:\n'
    for tablename, status in non_passes_detail.items():
        msg += f'{tablename}: {status}\n'
    return msg.strip()

def get_headers(exporter_config):
    auth_token = exporter_config.get('api_auth_token')
    headers = {
        'accept': 'application/json',
        'Authorization': auth_token
    }
    return headers

def get_api_host(region='us-west-2'):
    return f'https://apiv2.{url_utils.get_region_domain(region)}.ai'

def get_running_interval(start_date=None, days=1):
    # Assumption here is that endtime will be the current day 00:00 AM
    if not start_date:
        end_date = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - datetime.timedelta(days)
    else:
        start_date = time_utils.date_obj_from_str(start_date)
        end_date = start_date + datetime.timedelta(days)
    return int(time_utils.to_timestamp(start_date)), int(time_utils.to_timestamp(end_date))

def is_redshift_table(tablename):
    return tablename in ['www_server_log', 'user_analytics']

def retry_on_failure(n_attempts=3, initial_delay=1, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for i in range(n_attempts):
                try:
                    response = func(*args, **kwargs)
                    if response.status_code == 200:
                        return response
                    else:
                        log.info(f"Attempt {i+1} failed with status_code {response.status_code}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                        delay *= backoff_factor
                except Exception as e:
                    log.info(f"Attempt {i+1} failed due to: {str(e)}")
                    time.sleep(delay)
                    delay *= backoff_factor
            log.error(f'Exceed maximum retry after {n_attempts} attempts')
            return response # Return last reponse if not success
        return wrapper
    return decorator

@retry_on_failure(initial_delay=30)
def post_request_with_retries(url, headers, json, timeout):
    return requests.post(url=url, headers=headers, json=json, timeout=timeout)

@retry_on_failure(initial_delay=30)
def get_request_with_retries(url, headers, params, timeout):
    return requests.get(url=url, headers=headers, params=params, timeout=timeout)

def does_output_date_format_exist(output_file_formats):
    for _, formats in output_file_formats.items():
        for _, value in formats.items():
            # Check if {output_date_format} is present in the format strings
            if "{output_date_format}" in value:
                # Check if the data_filename_format is already in the set
                return True
    return False

def is_filename_duplicated(output_file_formats):
    for _, formats in output_file_formats.items():
        if formats[DATA_FILE] == formats[META_FILE]:
            # Since we respect the filename customer set, if we see duplicated filename for meta and data file, we will end up overwriting the data file or vice versa
            return True
    return False

def validate_json(app_setting):
    # If {output_date_format} is there in any compressed_filename_format, data_filename_format, meta_filename_format keys, then output_date_format is required
    # check if the provided table name is valid
    output_file_formats = app_setting.get('output_file_formats')
    if does_output_date_format_exist(output_file_formats) and not app_setting.get('output_date_format'):
        raise IncorrectOutputFileFormatException('output_date_format is required when output_file_formats contains {output_date_format}')
    if is_filename_duplicated(output_file_formats):
        raise IncorrectOutputFileFormatException('data_filename_format and meta_filename_format cannot be the same')
    table_list = set(output_file_formats.keys())
    all_tables_supported = table_registry.get_all_tablenames()
    if not set(table_list).issubset(set(all_tables_supported)):
        raise UnknownTableException(f'Table not supported. Supported tables are {all_tables_supported}')

def validate_delivery_time(app_setting):
    if app_setting.get('delivery_time') and not time_utils.parse_time_str_for_today(app_setting.get('delivery_time')):
        raise DeliveryTimeException(f'Invalid delivery time: {app_setting.get("delivery_time")}')

def validate_app_settings(app_setting, trigger_locally=False):
    # Validate SFTP Connection
    if app_setting.get('method') == 'sftp':
        sftp_utils.verify_sftp_connection(
            hostname=app_setting.get('hostname'),
            username=app_setting.get('username'),
            private_key =app_setting.get('private_key')
        )

    # Validate API Auth Token is valid
    api_connector = ApiConnector(app_setting.get('api_oauth_username'), app_setting.get('api_auth_token'))
    api_connector._connect()

    # Validate Redshift Connection
    all_redshift_table = set(table_registry.RedshiftTableRegistry.REDSHIFT_TABLE_CLASS_MAP.keys())
    if set(app_setting.get('to_export_tables', [])).intersection(all_redshift_table):
        redshift_client = RedshiftClient(app_setting.get('redshift_user'), app_setting.get('redshift_password'), app_setting.get('region'), app_setting.get('redshift_host'))
        if not trigger_locally:
            # The current setup cannot connect to Redshift via the same method as app because dev env VPC is not whitelisted in beska
            redshift_client._test_connection_query()

    # Validate delivery time
    validate_delivery_time(app_setting)

    # Validate output_file_formats
    validate_json(app_setting)
