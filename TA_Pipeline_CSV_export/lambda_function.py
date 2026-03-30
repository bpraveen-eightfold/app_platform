import json
import time
import logging
import time
import traceback
from jsonpath_ng.ext import parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

S3_FILEPATH_FORMAT = 'app_data/{group_id}/{app_name}/{user_email}/pipeline_export_csv_{timestamp}.csv'

def current_micro_time():
    return int(round(time.time() * 1000000))

def lookup_jsonpath(data, parsed_expr, default=None):
    return (lookup_jsonpath_all(data, parsed_expr) or [default])[0]

def lookup_jsonpath_all(data, parsed_expr):
    return [match.value for match in parsed_expr.find(data)] if parsed_expr else []

def jsonpath_parsed_expr(expr):
    start_us = current_micro_time()
    ret = parse(expr)
    logging.debug('Time taken in jsonpath_parsed_expr: {}, exp: {}, ret: {}'.format(current_micro_time() - start_us, expr, ret))
    return ret

def _get_group_id(user_email):
    return user_email.split('@')[-1].strip()

def _extract_notes(notes_str, num_notes):
    if num_notes <= 0:
        return ''
    notes = notes_str.split(',"')
    notes = [n.strip('"') for n in notes]
    notes = notes[:num_notes]
    return ','.join('"{}"'.format(n) for n in notes)

def get_row_data(pr_json, parsed_expr_list, app_settings):
    if not parsed_expr_list or not pr_json:
        return []
    row = []
    fields_to_extract = app_settings['profile_fields']
    num_notes = app_settings.get('num_notes', 1)
    start_time = current_micro_time()
    for idx, parsed_expr in enumerate(parsed_expr_list):
        start_us = current_micro_time()
        val = lookup_jsonpath(pr_json, parsed_expr) or ''
        if fields_to_extract[idx] == 'notes' and val:
            val = _extract_notes(val, num_notes)
        row.append(val)
        logging.debug('Time spent in lookup_jsonpath: {} us'.format(
            current_micro_time() - start_us))
    logging.debug('Time spent in get_row_data: {} us'.format(current_micro_time() - start_time))
    return row

def app_handler(event, context):
    if event.get('trigger_name') == 'pipeline_app_action':
        app_settings = event.get('app_settings', {})

        req_data = event.get('request_data', {})

        if not app_settings.get('profile_fields') or not app_settings.get('app_name'):
            return {
                'statusCode': 200,
                'body': json.dumps({'error': 'Please provide app_name and profile_fields in app_settings'})
            }
        columns = app_settings.get('columns')
        if not columns:
            columns = []
            for field in app_settings.get('profile_fields'):
                columns.append(field.split('.')[-1])

        if not req_data.get('profile_json_list') or not req_data.get('user_email'):
            return {
                'statusCode': 200,
                'body': json.dumps({'error': 'Please provide profile_json_list, user_email in request_data'})
            }
        try:
            group_id = _get_group_id(req_data['user_email'])
            data = {'actions': []}
            rows = []
            parsed_expr_list = []
            for field in app_settings['profile_fields']:
                parsed_expr_list.append(jsonpath_parsed_expr(field))
            for pr_json in req_data.get('profile_json_list'):
                row = get_row_data(pr_json, parsed_expr_list, app_settings)
                rows.append(row)
            action = {'action_name': 'convert_data_to_csv',
                      'request_data': {'headers': columns,
                                       'row_list': rows,
                                       'msg_format': app_settings.get('msg_format') or 'Data has been exported to {url}.'
                                      }
                     }
            data['actions'].append(action)
        except Exception as ex:
            logging.info(traceback.format_exc())

            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': repr(ex),
                    'stacktrace': traceback.format_exc(),
                }),
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'data': data})
        }
