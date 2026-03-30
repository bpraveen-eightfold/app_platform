import time
import uuid
import json

import hmac
import hashlib
import base64

secret_key = '29d4dc63b8694c81d9ce230b54216000472a6c84f7a709ac0f8fa8bcbadedcbcf046f29e9f53f8db9048610282899e25'
iss = '9aa7716d8890f1f0159c824e775f8d33a74d1d25'
aud = '1158638238264268256'

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



def generate_authtoken():
    header = {'alg': 'HS256', 'typ': 'JWT'}
    iat = time_msec() / 1000 + 10
    #iat = 1651785601.612
    exp = time_msec() / 1000 + 1000
    #exp = 1651786591.612
    payload = { 'exp' : exp, 'iss': iss, 'aud': aud, 'iat': iat, 'jti': generate_guid()}
    #payload = { 'exp' : exp, 'iss': iss, 'aud': aud, 'iat': iat, 'jti': '654a9934-08a5-fcad-3208-b5a872d19553'}

    unsigned_token = base64_object(header) + "." + base64_object(payload)
    print('unsigned_token: {}'.format(unsigned_token))
    #import pdb
    #pdb.set_trace()
    #signed_hmac_sha256 = hmac.new(secret_key.encode('utf-8'), unsigned_token.encode('utf-8'), hashlib.sha256)
    signed_hmac_sha256 = hmac.new(secret_key.encode(), unsigned_token.encode(), hashlib.sha256)
    signature_hash = signed_hmac_sha256.digest()
    signature = base64.b64encode(signature_hash).decode()
    print('signature: {}'.format(signature))
    token = unsigned_token + '.' + signature;
    print('token: {}'.format(token))
    final_token = remove_illegal_chars(token)
    print('final_token: {}'.format(final_token))
    print('iat: {}, exp: {}, guid: {}'.format(iat, exp, payload['jti']))
    return final_token

import pdb
pdb.set_trace()
token = generate_authtoken()
#token2 = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2NTE3ODY1OTEuNjEyLCJpc3MiOiI5YWE3NzE2ZDg4OTBmMWYwMTU5YzgyNGU3NzVmOGQzM2E3NGQxZDI1IiwiYXVkIjoiMTE1ODYzODIzODI2NDI2ODI1NiIsImlhdCI6MTY1MTc4NTYwMS42MTIsImp0aSI6IjY1NGE5OTM0LTA4YTUtZmNhZC0zMjA4LWI1YTg3MmQxOTU1MyJ9.iQoMTIRUJ-UGz0igcaG2oWCHUahTaWSbTL5v8IUmWWQ'
url = 'https://api.mindtickle.com/api/v2/series/list'
headers = {}
headers['Authorization'] = 'Bearer {}'.format(token)
import requests
#import pdb
#pdb.set_trace()
resp = requests.get(url, headers=headers)
print(resp.content)

#header = {'alg': 'HS256', 'typ': 'JWT'}
#import pdb
#pdb.set_trace()
#input_str = json.dumps(header, separators=(',', ':'))
#print(input_str)
