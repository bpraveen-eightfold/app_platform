#!/usr/bin/env python
import argparse
import logging
import os
import traceback
import time

import glog as log

import data_exporter_utils
import incremental_exporter

from db.table_registry import UnknownTableException
from utils import str_utils
from utils import json_utils
from utils.sftp_utils import SFTPException
from data_exporter_utils import APIConnectionException, DeliveryTimeException, IncorrectOutputFileFormatException
from incremental_exporter_constants import APP_KEY
from incremental_exporter_constants import EF_DEBUG_LOG_PREFIX

class IncompleteRunException(Exception):
    pass

class InvalidConfigException(Exception):
    pass

def _errordict(status_code, message):
    return {
        'statusCode': status_code,
        'body': json_utils.dumps({
            'is_success': False,
            'error': message,
            'stacktrace': traceback.format_exc()
        })
    }

def _validation_response(is_success, message=None):
    data = { 'is_success': is_success }
    if not is_success:
        data['error'] = message
    return {
        'statusCode': 200,
        'body': json_utils.dumps({'data': data})
    }

def _successdict(status_code, message, save_to_app_data_json=None):
    body = { 'message': message }
    if save_to_app_data_json:
        body['data'] = {
            'actions': [
                {
                    'action_name': 'save_app_data',
                    'request_data': save_to_app_data_json
                }
            ]
        }
    resp = {
        'statusCode': status_code,
        'body': json_utils.dumps(body)
    }
    print(f'{EF_DEBUG_LOG_PREFIX}returning resp for a complete run: {resp}')
    return resp


def _validate_app_setting(exporter_config, trigger_locally=False):
    try:
        data_exporter_utils.validate_app_settings(exporter_config, trigger_locally)
    except SFTPException as e:
        raise InvalidConfigException(f'Invalid SFTP setting. {str(e)}')
    except APIConnectionException as e:
        raise InvalidConfigException(f'Invalid API setting. Please check api_oauth_username or api_auth_token')
    except DeliveryTimeException as e:
        raise InvalidConfigException(f'Invalid API setting. Please check api_oauth_username or api_auth_token')
    except IncorrectOutputFileFormatException as e:
        raise InvalidConfigException(f'Invalid Output File Format {str(e)}')
    except UnknownTableException:
        raise InvalidConfigException(f'Invalid tablename in output_file_formats')
    except TimeoutError:
        raise InvalidConfigException(f'Invalid redshift connection string')

def _clean_ssh_key_double_escape(exporter_config):
    exporter_config['private_key'] = str_utils.safe_unicode_escape(exporter_config['private_key'])
    return

def app_handler(event, context):
    request_data = event.get('request_data', {})
    exporter_config = event.get('app_settings', {})
    app_data = request_data.get('app_data') or {} # default app_data is None { app_data: None }
    last_run_state = app_data.get('incremental_exporter_app', {})
    print(f'{EF_DEBUG_LOG_PREFIX}Starting Data Exporter with app_settings:{exporter_config} request_data: {request_data}')
    
    trigger_name = event.get('trigger_name')
    # Can override group_id using request_data for development invocation
    group_id = request_data.get('group_id') or event.get('group_id')

    if not trigger_name.startswith('scheduled_'):
        return _errordict(
            status_code=500,
            message='Not running exporter in from scheduled trigger'
        )
    try:
        msg = ''
        fail_msg = ''
        st = time.time()
        start_time, end_time = incremental_exporter.get_running_interval(request_data.get('start_date'), days=request_data.get('running_interval'))
        log.info(f'Start exporting data for tables: {exporter_config.get("to_export_tables")}')
        _clean_ssh_key_double_escape(exporter_config)
        exporter = incremental_exporter.IncrementalExporter(
            group_id=group_id,
            dry_run=request_data.get('dry_run', False),
            working_dir=request_data.get('working_dir'),
            start_time=start_time,
            end_time=end_time,
            exported_limit=str_utils.safe_get_int(request_data.get('limit'), default=-1),
            exporter_config=exporter_config,
            skip_recovery=request_data.get('skip_recovery', False),
            last_run_state=last_run_state
        )
        _validate_app_setting(exporter_config, trigger_locally=trigger_name == 'scheduled_locally') # Run a runtime config validation
        breakdown_run_time, breakdown_changelog_size = exporter.run_incremental_data_delivery()
        exporter.trim_state_for_state_dump()
        end = time.time()
        log.info(f'Total run time {end - st}s')
        log.info(f'breakdown_run_time {breakdown_run_time}')
        log.info(f'breakdown_changelog_size {breakdown_changelog_size}')
        msg += data_exporter_utils.generate_output_message(breakdown_run_time, group_id, breakdown_changelog_size)
        # If any table fails, raise Exception and return 500 to App Platform so that it appears as failed in Admin Console Monitoring Page
        non_passes_detail = exporter.get_non_passed_status_for_all_tables()
        
        if non_passes_detail:
            fail_msg = data_exporter_utils.generate_error_message_for_non_pass_tables(non_passes_detail)
            raise IncompleteRunException('Fail to export data for some tables')

    except IncompleteRunException as ex:
        # Not returning 500 because state will not be updated and next run we wil waste time running it all instead of just the failed one
        log.error(f'Fail to complete incremental_data_exporter run: {str(ex)}.\nFinal Status: {fail_msg}')
    except InvalidConfigException as ex:
        # This will result in delay alarm and app invoke failure alarm
        log.error(f'Invalid Config {str(ex)}')
        return _errordict(
            status_code=500,
            message=f'Invalid App Setting for incremental exporter. {str(ex)}'
        )  
    except Exception as ex:
        log.error(f'Fail to run incremental_data_exporter {str(ex)}. Traceback: {traceback.format_exc()}')
        msg += data_exporter_utils.generate_output_message(None, group_id, traceback=traceback.format_exc(), ex=ex)
        return _errordict(
            status_code=500,
            message='Fail to run incremental exporter.\n' + msg
        )

    return _successdict(
        status_code=200,
        message=msg,
        save_to_app_data_json={
            'namespace': trigger_name,
            'app_key': APP_KEY,
            'data_json': exporter.current_state
        }
    )

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group_id', type=str, default=[], help='group_id to be run incremental delivery')
    parser.add_argument('--running_interval', type=int, default=1, help='number of day internal to retrieve data')
    parser.add_argument('--start_date', type=str, default=None, help='specify the start date in a %Y-%m-%d format')
    parser.add_argument('--dry_run', help='dry run mode will only exported data locally and not uploading to destination', action='store_true')
    parser.add_argument('--skip_recovery', help='skip automatically recovery mode instead of full run', action='store_true')
    parser.add_argument('--working_dir', type=str, default=[], help='A path from which to read checkpoint file')
    parser.add_argument('--tables', nargs='+', type=str, default=[], help='tables to be exported. We will export all entites if not specified')
    parser.add_argument('--limit', type=int, default=-1, help='The number of items to be exported for each table')
    parser.add_argument('--config_file', type=str, default="", help='config file name (if any)')
    parser.add_argument('--api_host', type=str, default="", help='api_host')
    parser.add_argument('--redshift_host', type=str, default="", help='redshift_host')
    parser.add_argument('--trigger_name', type=str, default="", help='trigger_name such as scheduled_hourly')
    return parser.parse_args()

def main():
    args = parse_args()
    cfg_filename = args.config_file or 'exporter_config.json'
    with open(os.path.join(os.path.dirname(__file__), cfg_filename)) as f:
       # This is for local testing only
       exporter_config = json_utils.load(f)
       # This api_host will be used for testing with localhost / stage only
       exporter_config['api_host'] = args.api_host
       exporter_config['redshift_host'] = args.redshift_host
    
    event = {
        'trigger_name': args.trigger_name or 'scheduled_locally',
        'app_settings': exporter_config,
        'request_data': {
            'running_interval': args.running_interval,
            'start_date': args.start_date,
            'dry_run': args.dry_run,
            'skip_recovery': args.skip_recovery,
            'working_dir': args.working_dir,
            'tables': args.tables,
            'limit': args.limit,
            'group_id': args.group_id,
            'app_data': None
        }
    }
    result = app_handler(event=event, context=None)
    log.info(f'Run Result:\n {result}')

if __name__ == '__main__':
    log.setLevel(logging.INFO)
    main()
