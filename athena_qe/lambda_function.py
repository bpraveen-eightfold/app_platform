#!/usr/bin/env python

import glog as log
import json
import traceback

import os
import shutil
import tempfile


from constants import Constants
from constants import ConfiguredFrequecy
from constants import field_separators
from constants import MetaExtension
from constants import RESULT_FIELD_DEFAULT_DELIMITER
from constants import SupportedExporters
from constants import FieldSeps
from query import QueryExecutor
from transform import ResultXfrm
from transport import Email
from transport import Sftp

##### IMPORTANT #####
# Please do not modify naming conventions as they are
# consistent within the App and Eightfold environment
# Please treat normalize_group_id, the workgroup name
# and get_database_name as purely read-only functions
# Contact: kbajaj@eightfold.ai, bbhushan@eightfold.ai

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
    app_settings = event.get('app_settings', {})
    trigger = event.get('trigger_name')
    log.info('Event: {}'.format(str(event)))
    log.info('Context: {}'.format(str(context)))
    group_id = event.get('group_id')
    Constants(group_id, app_settings['aws_access_key_id'], app_settings['aws_secret_access_key'], os.getenv('AWS_REGION', 'us-west-2'))
    query_executor = QueryExecutor(Constants.athena_client)
    result_fields_separator = field_separators[app_settings.get('result_fields_separator', FieldSeps.COMMA.value)]
    result_xfrm = ResultXfrm(group_id)
    unconfigured_triggers = []
    for config in app_settings['exporter_config']:
        configured_frequency = config['exporter_frequency']
        if configured_frequency == ConfiguredFrequecy.HOURLY.value and trigger != 'scheduled_hourly' or\
            configured_frequency == ConfiguredFrequecy.DAILY.value and trigger != 'scheduled_daily' or\
            configured_frequency == ConfiguredFrequecy.WEEKLY.value and trigger != 'scheduled_weekly':
            unconfigured_triggers.append({'configured_frequency': configured_frequency, 'triggered_frequency': trigger})
            continue
        query = config['query']
        for exporter in config['exporter']:
            if exporter not in [e.value for e in SupportedExporters]:
                return _errordict(status_code=500, message='unknown exporter_type'.format(exporter))
        result_s3_location = query_executor(query)
        if not result_s3_location:
            log.error('Error Excuting Query {}'.format(query))
            continue
        for transport in config['exporter']:
            if transport == SupportedExporters.SFTP.value:
                bucket, obj = result_s3_location[len('s3://'):].split('/', 1)
                s3filename = os.path.basename(obj)
                workdir = tempfile.mkdtemp()
                zip_filepath = ''
                metafilepath = None
                skip_header = config.get('skip_header')
                # Transform
                localfile = result_xfrm.result_prefix(
                    config.get('result_filename_prefix', '%G.%D.%S'), 
                    config.get('result_files_seq_start', '0'),
                    config.get('timestamp_format', '%Y%m%d-%H%M%S'),
                    config.get('suffix', s3filename),
                    config.get('extension', 'csv')
                    )
                filepath = os.path.join(workdir, localfile)
                _ = Constants.s3_client.download_file(bucket, obj, filepath)
                if config.get('metaextension'):
                    metafilepath = result_xfrm.generate_metafile(filepath, config.get('encrypt') == 'true')
                    if config['metaextension'] != MetaExtension.META.value:
                        metafilepath = result_xfrm.rename_extension_and_move(metafilepath, config['metaextension'])
                result_files = [filepath, metafilepath] if metafilepath else [filepath]
                if result_fields_separator != RESULT_FIELD_DEFAULT_DELIMITER:
                    result_xfrm.change_sep(result_files, result_fields_separator)
                if config.get('zip'):
                    zip_prefix = config.get('result_zip_file_prefix')
                    zip_filename = os.path.splitext(zip_prefix + localfile)[0]
                    indir = os.path.dirname(filepath)
                    zip_filepath = result_xfrm.zipper(zip_filename, indir)
                    result_files.append(zip_filepath)
                    result_files.remove(filepath)
                    result_files.remove(metafilepath)
                if skip_header and skip_header.lower() == 'true':
                    result_xfrm.remove_header(result_files, result_fields_separator)
                if config.get('encrypt') == 'true':
                    encryption_public_key = config.get('encryption_public_key')
                    recipients = config.get('recipients')
                    result_files = result_xfrm.encrypt_files(result_files, encryption_public_key, recipients)

                Sftp(config['hostname'], config['username'], config['sftp_path'], config['id_rsa.pub'], config['id_rsa']).put(*result_files)     
            if transport == SupportedExporters.EMAIL.value:
                url = result_xfrm.sign_url(result_s3_location)
                body = 'Query {}\nResult {}'.format(query, url)
                Email(config['email_from'], config['email_to'], 'eightfold, query execution result', body)
            if zip_filepath:
                shutil.rmtree(os.path.dirname(zip_filepath))
            shutil.rmtree(os.path.dirname(filepath))

    if len(unconfigured_triggers) == len(app_settings['exporter_config']):
        return _successdict(status_code=200, message='Received unconfigured triggers (skipping): {}'.format(unconfigured_triggers))
    return _successdict(status_code=200, message='App invocation successful with {} trigger'.format(trigger))

def main():
    import pprint
    from pprint import pprint
    payload = {}
    # with open(os.path.join(os.path.dirname(__file__), 'payload_email.json')) as f:
    #     payload = json.load(f)
    # pprint(app_handler(payload, None))

    with open(os.path.join(os.path.dirname(__file__), 'payload_sftp.json')) as f:
       payload = json.load(f)
    result = app_handler(payload, None)
    print(80*'~')
    pprint(result)

if __name__ == '__main__':
    main()
