from lambda_function import app_handler
import json
import glog as log

event = {}
req_data = {}
req_payload = {}
req_data['trigger_name'] = 'webhook_receive_event'
req_payload['entity_type'] = ''

req_data['request_payload'] = req_payload
event['request_data'] = req_data

resp = app_handler(event, {})
body = json.loads(resp['body'])
log.info(f'statusCode: {resp["statusCode"]}, body: {body}')

req_payload['entity_type'] = 'candidate'
req_payload['entity_id'] = '1234'
req_payload['entity_payload'] = {'firstname': 'Test', 'lastname': 'User'}

req_data['request_payload'] = req_payload
event['request_data'] = req_data

resp = app_handler(event, {})
body = json.loads(resp['body'])
log.info(f'statusCode: {resp["statusCode"]}, body: {body}')
