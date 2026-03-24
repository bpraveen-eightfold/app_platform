""" HackerRank Adapter Implements the methods to interact with HackerRank assessment system.  """

import json
from datetime import datetime
from datetime import timedelta
import requests

import utils
from base_adapter import BaseAdapter
from response_objects import AssessmentReportResponse
from response_objects import AssessmentTest
from response_objects import AssessmentInviteCandidateResponseType
from response_objects import AssessmentGetLogoUrlResponseType
from response_objects import AssessmentIsWebhookSupportedResponseType

ENDPOINT_TESTS = 'tests'
LIST_TESTS_URL_FORMAT = '{base_url}/{endpoint}?offset={offset}&limit={limit}'
INVITE_CANDIDATE_URL_FORMAT = '{base_url}/{endpoint}/{test_id}/candidates'
FETCH_CANDIDATE_REPORT_URL_FORMAT = '{base_url}/{endpoint}/{test_id}/candidates/{candidate_id}'
TEST_CANDIDATES_URL_FORMAT = '{base_url}/{endpoint}/{test_id}/candidates?limit={limit}&offset={offset}'
# pylint: disable=line-too-long
INVITE_ALREADY_SENT_ERROR_MSG = 'Candidate has already been invited to take the same test. If you want to reinvite, cancel the invite in your HackerRank for Work account first.'
TEST_ALREADY_TAKEN_ERROR_MSG = 'Candidate has already taken the test.'

class HackerRankAssessmentAdapter(BaseAdapter):
    """ Adapter for HackerRank. """

    @staticmethod
    def get_logo_url():
        resp_obj = AssessmentGetLogoUrlResponseType()
        resp_obj.logo_url = 'https://static.vscdn.net/app_platform_app_icons/HR_Logo_Dark.png'
        return resp_obj.to_dict()

    @staticmethod
    def is_webhook_supported():
        resp_obj = AssessmentIsWebhookSupportedResponseType()
        resp_obj.is_webhook_supported = True
        return resp_obj.to_dict()

    @staticmethod
    def list_tests(credentials, action_user_email=None):
        url = _get_list_tests_url(credentials.get('api_url'))
        json_payload = get_url_content(
            credentials=credentials,
            http_method='GET',
            url=url,
            action_user_email=action_user_email)
        if not json_payload:
            return []
        tests_list = _get_test_list_helper(json_payload)
        while json_payload.get('next'):
            json_payload = get_url_content(
                credentials=credentials,
                http_method='GET',
                url=json_payload.get('next'),
                action_user_email=action_user_email)
            if not json_payload:
                return tests_list
            tests_list.extend(_get_test_list_helper(json_payload))
        return tests_list

    @staticmethod
    def invite_candidate(credentials, test_id, subject, invite_metadata, action_user_email=None, notification_url=None, **kwargs):
        if not invite_metadata.get('email') or not test_id:
            raise ValueError('Candidate email or test_id can not be None.')
        force_send = False
        if kwargs.get('force') is not None:
            force_send = kwargs.get('force')
        send_email = True
        if kwargs.get('send_email') is not None:
            send_email = kwargs.get('send_email')
        assessment_config = kwargs.get('assessment_config') or {}
        invite_valid_duration_days = kwargs.get('invite_valid_duration_days') or assessment_config.get('invite_valid_duration_days', None)
        url = _get_invite_candidate_url(credentials.get('api_url'), test_id)
        payload = _get_payload_for_invite_candidate(
            invite_metadata=invite_metadata,
            force_send=force_send,
            send_email=send_email,
            invite_candidate_duration_days=invite_valid_duration_days,
            subject=subject,
            notification_url=notification_url)
        json_resp = get_url_content(
            credentials=credentials,
            http_method='POST',
            url=url,
            action_user_email=action_user_email,
            json_payload=payload)
        if not json_resp:
            raise RuntimeError('Invite candidate response is empty')
        return _process_invite_candidate_response(json_resp, invite_metadata.get('email'))

    @staticmethod
    def fetch_candidate_report(credentials, test_id, vendor_candidate_id, action_user_email=None):
        if not test_id or not vendor_candidate_id:
            raise ValueError('test_id and vendor_candidate_id can not be None!')
        url = _get_fetch_candidate_report_url(credentials.get('api_url'), test_id, vendor_candidate_id)
        json_resp = get_url_content(
            credentials=credentials,
            http_method='GET',
            url=url,
            action_user_email=action_user_email)
        if not json_resp:
            raise RuntimeError('Fetch candidate report response is empty')
        return _process_candidate_report_dict(json_resp)

    @staticmethod
    def verify_webhook_authentication(credentials, headers, request, **kwargs):
        if not kwargs.get('auth_key'):
            raise ValueError('Auth key cannot be empty!')
        if kwargs['auth_key'] != credentials.get('secret_key'):
            raise ValueError('Invalid authorization key!')

    @staticmethod
    def validate_webhook_request(headers, request_payload):
        if not request_payload:
            raise ValueError('request_payload cannot be empty!')
        if not request_payload.get('invite_metadata'):
            raise ValueError('invite_metadata cannot be empty!')
        im = json.loads(request_payload['invite_metadata'])
        if not im.get('profile_id') or not im.get('pid') or not im.get('test_id'):
            raise ValueError('profile_id: {}, pid: {}, test_id: {} cannot be None!'.format(
                im.get('profile_id'), im.get('pid'), im.get('test_id')))

    @staticmethod
    def process_webhook_request(headers, request_payload):
        return {'invite_metadata': json.loads(request_payload.get('invite_metadata')),
                'assessment_report': _process_candidate_report_dict(request_payload)}

    @staticmethod
    def fetch_reports(credentials, test_id, action_user_email=None):
        if not test_id:
            raise ValueError('test_id: {} cannot be None'.format(test_id))
        next_url = _get_test_candidates_url(credentials.get('api_url'), test_id)
        while next_url:
            json_payload = get_url_content(
                credentials=credentials,
                http_method='GET',
                url=next_url,
                action_user_email=action_user_email)
            if not json_payload or not json_payload.get('data'):
                break
            for record in json_payload.get('data'):
                invite_metadata = json.loads(record.get('invite_metadata')) if record.get('invite_metadata') else None
                aad = _process_candidate_report_dict(record)
                yield {'invite_metadata': invite_metadata,
                       'assessment_report':  aad}
            next_url = json_payload.get('next')

def get_url_content(credentials, http_method, url, action_user_email=None, json_payload=None):
    headers = {}
    if credentials.get('auth_key'):
        headers = {'Authorization': 'Bearer {}'.format(credentials.get('auth_key'))}
    if action_user_email:
        headers.update({'HRW-User-Email': '{}'.format(action_user_email)})

    headers.update({'X-HRW-Partner-Authorization': 'RWlnaHRmb2xkLmFpOjkxMmRjOGM3ZWIxYjA1ZTYwMjI2MTM3MTcwNjUzZWVlZjQ3M2NkNTY3YmZjZWU3ZDI0MDg4MTVkMTljMTU0MWU='})

    print(f"sending {http_method} request to url {url}, with json payload: {json_payload}")
    if http_method == 'GET':
        resp = requests.get(url=url, headers=headers, json=json_payload)
    elif http_method == 'POST':
        resp = requests.post(url=url, headers=headers, json=json_payload)
    else:
        raise RuntimeError('Invalid http_method: {}'.format(http_method))
    print(f"received response: {resp}, content: {resp.content}")
    try:
        return json.loads(resp.content) if resp.content else {}
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        raise

def _get_test_list_helper(json_payload):
    if not json_payload:
        return []
    if json_payload.get('errors'):
        if isinstance(json_payload['errors'], list):
            raise RuntimeError(json_payload['errors'][0])
        else:
            raise RuntimeError('Failed with unknown error')
    tests_list = []
    for record in json_payload.get('data'):
        test = AssessmentTest()
        test.id = record['id']
        test.name = record['name']
        test.duration_minutes = record.get('duration')
        test.published = not record['draft']
        tests_list.append(test.to_dict())
    return tests_list

def _get_list_tests_url(base_url, offset=0, limit=100):
    return LIST_TESTS_URL_FORMAT.format(base_url=base_url, endpoint=ENDPOINT_TESTS,
                                        limit=limit, offset=offset)

def _get_invite_candidate_url(base_url, test_id):
    return INVITE_CANDIDATE_URL_FORMAT.format(base_url=base_url, endpoint=ENDPOINT_TESTS,
                                              test_id=test_id)

def _get_fetch_candidate_report_url(base_url, test_id, vendor_candidate_id):
    return FETCH_CANDIDATE_REPORT_URL_FORMAT.format(base_url=base_url, endpoint=ENDPOINT_TESTS,
                                                    test_id=test_id, candidate_id=vendor_candidate_id)
def _get_test_candidates_url(base_url, test_id, offset=0, limit=10):
    return TEST_CANDIDATES_URL_FORMAT.format(base_url=base_url, endpoint=ENDPOINT_TESTS,
                                             test_id=test_id, limit=limit, offset=offset)

def _get_payload_for_invite_candidate(invite_metadata, force_send, send_email, invite_candidate_duration_days,
                                      subject, notification_url):
    invite_valid_from = None
    invite_valid_to = None
    # If invite_candidate_duration_days is provided then honor that and if not then The desired behavior is for
    # HackerRank’s API to default to the user/company-level default within HackerRank.
    # To achieve this, we need to leave invite_valid_from and invite_valid_to blank instead of setting it to a value.
    if invite_candidate_duration_days is not None:
        invite_valid_from = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        invite_valid_to = (datetime.now() + timedelta(days=invite_candidate_duration_days)).strftime('%Y-%m-%dT%H:%M:%S')
    payload = {'email': invite_metadata.get('email'),
               'invite_valid_from': invite_valid_from,
               'invite_valid_to': invite_valid_to,
               'subject': subject,      # If subject is None, HackerRank’s API defaults to the user/company-level default within HackerRank
               'send_email': send_email,
               'force_send': force_send,
               'invite_metadata': invite_metadata,
               'test_result_url': notification_url}
    return payload

def _process_invite_candidate_response(payload, email):
    if payload.get('message'):
        raise RuntimeError(payload.get('message'))
    if payload.get('errors'):
        if INVITE_ALREADY_SENT_ERROR_MSG in payload['errors'] or TEST_ALREADY_TAKEN_ERROR_MSG in payload['errors']:
            invite_resp = AssessmentInviteCandidateResponseType(email)
            invite_resp.invite_already_sent = True
            return invite_resp.to_dict()
        else:
            if isinstance(payload['errors'], list):
                raise RuntimeError(payload['errors'][0])
            else:
                raise RuntimeError('Failed with unknown error')
    invite_resp = AssessmentInviteCandidateResponseType(payload.get('email'))
    invite_resp.vendor_candidate_id = payload.get('id')
    invite_resp.test_url = payload.get('test_link')
    return invite_resp.to_dict()

def _process_candidate_report_dict(payload):
    aad = AssessmentReportResponse()
    if isinstance(payload.get('test'), dict):
        aad.test_id = payload.get('test', {}).get('id')
    aad.email = payload.get('email')
    aad.status = _get_assessment_status(payload.get('status'))
    aad.assigned_ts = utils.to_timestamp(payload.get('invited_on')) if payload.get('invited_on') else None
    aad.start_ts = utils.to_timestamp(payload.get('attempt_starttime')) if payload.get('attempt_starttime') else None
    aad.completed_ts = utils.to_timestamp(payload.get('attempt_endtime')) if payload.get('attempt_endtime') else None
    aad.score = payload.get('percentage_score')
    aad.score_unit = 'percentage'
    #aad.report_url = payload.get('pdf_url') # url for pdf file
    aad.report_url = payload.get('report_url') # report url of the candidate
    aad.plagiarism_status = payload.get('plagiarism_status')
    aad.comments = utils.listify(payload.get('comments')) if payload.get('comments') else None
    aad.response_json = payload
    return aad.to_dict()

def _get_assessment_status(status):
    if status is None:
        return None
    elif status == -1:
        return 'invited'
    elif status == 7:
        return 'completed'
    return None
