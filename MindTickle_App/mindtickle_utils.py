from __future__ import absolute_import

import time
import uuid
import json
import hmac
import hashlib
import base64
import time
import datetime

import requests

def call(http_method, **kwargs):
    if http_method == 'GET':
        return requests.get(**kwargs)
    elif http_method == 'POST':
        return requests.post(**kwargs)
    elif http_method == 'DELETE':
        return requests.delete(**kwargs)
    else:
        raise RuntimeError(f'Invalid http_method: {http_method}')

def get_resp(http_method, **kwargs):
    resp = call(http_method, **kwargs)
    try:
        resp.raise_for_status()
    except:
        raise Exception(f'Error: status_code: {resp.status_code}, resp_content: {resp.content}')
    return resp

def time_msec():
    return (time.time() * 1000)

def generate_guid():
    return str(uuid.uuid4())

def remove_illegal_chars(input_str):
    return input_str.replace('=', '').replace('+', '-').replace('/', '_')

def base64_str(input_str):
    return base64.b64encode(bytes(input_str, 'utf-8')).decode()

def base64_object(input_obj):
    input_str = json.dumps(input_obj, separators=(',', ':'))
    b64_str = base64_str(input_str)
    return remove_illegal_chars(b64_str)

# This method is written based on Content API documentation of MindTickle uploaded
# at https://drive.google.com/file/d/1ZvZBkTsVmXDJkMUpy-vx-nUHnablSePb/view?usp=sharing
def generate_authtoken(secret_key, api_key, company_id):
    header = {'alg': 'HS256', 'typ': 'JWT'}
    iat = time_msec() / 1000 + 10
    exp = time_msec() / 1000 + 1000
    payload = { 'exp' : exp, 'iss': api_key, 'aud': company_id, 'iat': iat, 'jti': generate_guid()}

    unsigned_token = base64_object(header) + "." + base64_object(payload)
    signed_hmac_sha256 = hmac.new(secret_key.encode(), unsigned_token.encode(), hashlib.sha256)
    signature_hash = signed_hmac_sha256.digest()
    signature = base64.b64encode(signature_hash).decode()
    token = unsigned_token + '.' + signature;
    final_token = remove_illegal_chars(token)
    return final_token

def to_timestamp(datetime_str, dt_fmt):
    try:
        return time.mktime(datetime.datetime.strptime(datetime_str, dt_fmt).timetuple())
    except ValueError:
        pass
    return 0

def get_series_id_module_id_from_entity_id(entity_id):
    parts = entity_id.split(':')
    if len(parts) != 2:
        raise ValueError(f'entity_id: {entity_id} is not valid!')
    return parts[0], parts[1]
