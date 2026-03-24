from __future__ import absolute_import

import json
import traceback
import sys

import transformation_router
import boto3
import time_utils
import uuid

BASE_S3_DIRECTORY = 'custom_transform'
MAX_RESPONSE_BYTES = 5000000

def _get_response_s3_key(request_info):
    event_type = request_info['event_type']
    transform_op = request_info['transform_op']
    group_id = request_info['group_id']
    system_id = request_info['system_id']
    unique_key = str(uuid.uuid4().hex)
    return f'{BASE_S3_DIRECTORY}/{group_id}/{system_id}/{event_type}/{transform_op}_resp/{unique_key}'

def app_handler(event, context):
    # Extract request_data -> this is the dynamic, per-invocation data for your app.
    req_data = event.get('request_data', {})
    # Extract app_settings -> this are the static params for your app configured for each unique installation.
    # E.g. API keys, allow/deny lists, etc.
    s3_bucket = req_data.get('s3_bucket')
    region = req_data.get('region', 'us-west-2')
    group_id = req_data.get('group_id')
    system_id = req_data.get('system_id')
    
    s3 = boto3.client('s3', region_name=region)
    
    if s3_bucket and req_data.get('s3_key'):
        try:
            response = s3.get_object(Bucket=s3_bucket, Key=req_data['s3_key'])
            content = response['Body'].read().decode('utf-8')
            req_data = json.loads(content)
        except Exception as ex:
            print('Error fetching S3 content:', str(ex))
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': repr(ex),
                    'stacktrace': traceback.format_exc(),
                })
            }

    trigger_name = event.get('trigger_name')
    input_dict = req_data.get('input_dict')
    output_dict = req_data.get('output_dict')
    entity_type = req_data.get('entity_type')
    event_type = req_data.get('event_type')
    transform_op = req_data.get('transform_op') or entity_type
    
    print(f'Call received for trigger_name: {trigger_name} entity_type: {entity_type} event_type: {event_type}')
    try:
        if event_type == 'write_back':
            transformation_router.apply_pre_write_back_transformation(input_dict, output_dict, transform_op)
        else:
            transformation_router.apply_post_fetch_transformation(input_dict, output_dict, transform_op)

        content = json.dumps({'data': output_dict}).encode('utf-8')
        response_size = sys.getsizeof(content)

        if response_size > MAX_RESPONSE_BYTES:
            s3_key = _get_response_s3_key({
                'event_type': event_type,
                'transform_op': transform_op,
                'group_id': group_id,
                'system_id': system_id
            })
            s3.put_object(Bucket=s3_bucket, Key=s3_key, Body=content)
            content = json.dumps({
                's3_bucket': s3_bucket,
                's3_key': s3_key,
                'response_size': response_size
            })

        return {
            'statusCode': 200,
            'body': content
        }
    except Exception as ex:
        err_str = 'Handler for trigger_name: {} entity_type: {} event_type: {} transform_op: {} failed with error: {}, traceback: {}'.format(
            trigger_name, entity_type, event_type, transform_op, str(ex), traceback.format_exc())
        print(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }
