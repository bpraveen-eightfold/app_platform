import base64
import requests
import glog as log
import json

from sterling_constants import SterlingConstants

AUTH_URL_FORMAT = '{base_url}/oauth'


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
    url = kwargs.get('url')
    log.info(
        f'[PreOnboard BG Check] Made Sterling BG Check API call, with the following parameters: url={url}, method={http_method}, {kwargs}')
    resp = call(http_method, **kwargs)
    log.info(f'[PreOnboard BG Check] Response for url={url}, method={http_method}: {resp.__dict__}')
    try:
        resp.raise_for_status()
    except:
        raise Exception(f'Error: status_code: {resp.status_code}, resp_content: {resp.content}')
    return resp


def base64_str(input_str):
    return base64.b64encode(bytes(input_str, 'utf-8')).decode()


def generate_auth_credentials(client_id, client_secret):
    auth_string = client_id + ':' + client_secret
    auth_bytes = auth_string.encode('utf-8')
    auth_token_bytes = base64.b64encode(auth_bytes)
    auth_token = auth_token_bytes.decode('utf-8')
    return auth_token


def generate_auth_token(auth_key):
    resp = get_resp(
        'POST',
        url=AUTH_URL_FORMAT.format(base_url=SterlingConstants.BASE_URL),
        headers={
            'Authorization': f'Basic {auth_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        data={
            'grant_type': 'client_credentials'
        }
    )
    resp_content = resp.content.decode('utf-8')
    try:
        data = json.loads(resp_content) if resp_content else {}
        token = data.get('access_token')
        return token
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        raise


