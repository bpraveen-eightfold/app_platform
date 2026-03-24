import glog as log
import json
import ntpath
import os
import shutil
import tempfile
import traceback

from api_connector import ApiConnector
from constants import ConfiguredFrequecy
from constants import SupportedExporters
from constants import URLS, ACCESS_TOKEN_URLS, ACCESS_BASIC_TOKEN
from transport import Sftp
from xml_util import *


##### IMPORTANT #####
# Please do not modify naming conventions as they are
# consistent within the App and Eightfold environment
# Please treat normalize_group_id, the workgroup name

class InputValidator:
    def __init__(self):
        return


def _errordict(**kwargs):
    return {
        'statusCode': kwargs['status_code'],
        'body': json.dumps({
            'error': kwargs['message'],
            'stacktrace': traceback.format_exc()
        })
    }


def _successdict(**kwargs):
    return {
        'statusCode': kwargs['status_code'],
        'body': json.dumps({
            'message': kwargs['message']
        })
    }


def app_handler(event, context):
    config = event.get('app_settings', {}).get('config')
    log.info('Event: {}'.format(str(event)))
    log.info('Context: {}'.format(str(context)))
    oauth_username = config.get('oauth_username')
    oauth_password = config.get('oauth_password')
    region = config.get('region')
    extract_type = config.get('extract_type')
    fields = config.get('fields').split(',')
    result_filename_prefix = config.get('filename_prefix')
    timestamp_format = config.get('filename_timestamp_format')
    start_ts = config.get("start_timestamp")
    encryption_key = config.get('encryption_key')
    if not len(encryption_key):
        log.info("Provide encryption_key")
        return

    ef = ApiConnector(region, oauth_username, oauth_password)
    for field in fields:
        entity_data = ef.get_data(field, region, start_ts, extract_type)
        log.info("writing to file.")
        if field == "experiences":
            result_location = write_to_file_exp(entity_data, result_filename_prefix, encryption_key, timestamp_format)
        else:
            result_location = ef.write_to_file(field, entity_data, result_filename_prefix, encryption_key, timestamp_format)

        workdir = tempfile.mkdtemp()
        localfile = ntpath.basename(result_location)
        log.info(f"local file name: {localfile}")
        filepath = os.path.join(workdir, localfile)
        shutil.copyfile(result_location, filepath)
        sftp_path = config['sftp_path']
        Sftp(config['sftp_hostname'], config['sftp_username'], sftp_path, config['sftp_id_rsa.pub'],
                config['sftp_id_rsa']).put(*[filepath])
        shutil.rmtree(os.path.dirname(filepath))
    return _successdict(status_code=200, message='App invocation successful')

def main():
    with open(os.path.join(os.path.dirname(__file__), 'payload.json')) as f:
        payload = json.load(f)

    result = app_handler(payload, None)
    log.info(80 * '~')
    log.info(result)


if __name__ == '__main__':
    main()
