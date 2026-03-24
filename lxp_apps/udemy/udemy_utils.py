import base64
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

def generate_authtoken(client_id, client_secret):
    auth_string = client_id + ':' + client_secret
    auth_bytes = auth_string.encode('utf-8')

    auth_token_bytes = base64.b64encode(auth_bytes)
    auth_token = auth_token_bytes.decode('utf-8')
    print(auth_token)

    return auth_token
