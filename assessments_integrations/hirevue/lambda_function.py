import time
import json
import traceback2
import requests

from dateutil import parser as du

import response_objects
from response_objects import AssessmentTestStatus
from base_adapter import BaseAdapter

DEFAULT_API_VERSION = '1.2.0'
LOGIN_ENDPOINT = '/api/v1/login/'
DEFAULT_APPLICATION_TOKEN = 'test_public_token'
LOGOUT_ENDPOINT = '/api/v1/logout/'
DEFAULT_POSITIONS_COUNT = 20
MAX_POSITIONS_COUNT = 500
POSITIONS_ENDPOINT = '/api/v1/positions/?qf=!isArchived!isDraft'
POSITIONS_COUNT_ENDPOINT = '/api/v1/positions/?qf=!isArchived!isDraft&qr={count}'

def to_timestamp(date_str, default=0):
    try:
        dt = du.parse(date_str)
        # if date has a timezone not the same as utc, then convert to utc
        t = (time.mktime(dt.timetuple()) + (dt.microsecond/1000000. if getattr(dt, 'microsecond', None) else 0)) if dt else default
        return t
    except:
        print('Failed to convert to_timestamp %s, exception: %s', date_str, traceback2.format_exc())
    return default

def call(http_method, **kwargs):
    if http_method == 'GET':
        return requests.get(**kwargs)
    elif http_method == 'POST':
        return requests.post(**kwargs)
    elif http_method == 'DELETE':
        return requests.delete(**kwargs)
    else:
        raise RuntimeError('Invalid http_method: {}'.format(http_method))

def get_resp(http_method, **kwargs):
    resp = call(http_method, **kwargs)
    try:
        resp.raise_for_status()
    except:
        raise Exception('Error: status_code: {}, resp_content: {}'.format(resp.status_code, resp.content))
    return resp

class AssessmentAdapter(BaseAdapter):
    def __init__(self, app_settings):
        #super(AssessmentAdapter, self).__init__()
        self.base_url = app_settings.get('base_url')
        if not self.base_url:
            raise ValueError('Base url cannot be emptyi!')
        if self.base_url.endswith('/'):
            self.base_url = self.base_url.strip('/')
        self.default_user = app_settings.get('default_user')
        self.api_key = app_settings.get('api_key')
        self.api_version = app_settings.get('api_version') or DEFAULT_API_VERSION
        self.csrf_token = None
        self.cookies = None
        self.session_key = None

    def login(self):
        url = self.base_url + LOGIN_ENDPOINT
        body = {
            'impersonate': self.default_user,
            'apiKey': self.api_key,
            'applicationToken': DEFAULT_APPLICATION_TOKEN,
            'version': self.api_version
        }

        resp = get_resp('POST', url=url, json=body)
        headers = json.loads(resp.headers) if isinstance(resp.headers, str) else resp.headers
        # set csrf token
        self.csrf_token = headers['csrftoken']
        self.cookies = resp.cookies
        self.session_key = headers['X-HvApi-Session-Key']

    def logout(self):
        url = self.base_url + LOGOUT_ENDPOINT
        if not self.csrf_token:
            return
        headers = {'X-CSRFToken': self.csrf_token}
        get_resp('POST', url=url, cookies=self.cookies, headers=headers)


    def get_logo_url(self):
        resp_obj = response_objects.AssessmentGetLogoUrlResponseType()
        resp_obj.logo_url = 'https://static.vscdn.net/app_platform_app_icons/hirevue-logo.png'
        return resp_obj.to_dict()

    def is_webhook_supported(self):
        resp_obj = response_objects.AssessmentIsWebhookSupportedResponseType()
        resp_obj.is_webhook_supported = True
        return resp_obj.to_dict()

    def list_tests(self, req_data):
        url = self.base_url + POSITIONS_ENDPOINT
        headers = {'X-CSRFToken': self.csrf_token}
        resp = get_resp('GET', url=url, headers=headers, cookies=self.cookies)
        resp_headers = json.loads(resp.headers) if isinstance(resp.headers, str) else resp.headers
        num_tests = int(resp_headers['X-HvAPI-Count'])
        print('num_tests: {}'.format(num_tests))
        if num_tests > DEFAULT_POSITIONS_COUNT:
            url = self.base_url + POSITIONS_COUNT_ENDPOINT.format(count=min(num_tests, MAX_POSITIONS_COUNT))
            headers = {'X-CSRFToken': self.csrf_token}
            resp = get_resp('GET', url=url, headers=headers, cookies=self.cookies)
        tests_data = json.loads(resp.content)
        tests = []
        for test in tests_data:
            tests.append(response_objects.AssessmentTest(
                test_id=test['id'],
                name=test['title'],
                duration_minutes=test.get('interviewDurationMinutes'),
                published=not test.get('isArchived')).to_dict())
        return tests

    def invite_candidate(self, req_data, suppress_participants_email=False):
        invite_metadata = req_data.get('invite_metadata')
        test_id = invite_metadata.get('test_id')
        url = self.base_url + '/api/v1/positions/{pid}/interviews/'.format(pid=test_id)
        headers = {'X-CSRFToken': self.csrf_token}
        if suppress_participants_email:
            headers['X-Suppress-Participant-Emails'] = 'true'
        body = {
            'firstName': req_data.get('firstname'),
            'lastName': req_data.get('lastname'),
            'email': invite_metadata.get('email'),
            'language': 'en',
            'externalId': invite_metadata.get('profile_id'),
            'externalCandidateId': json.dumps(invite_metadata),
            'partnerType': 'Eightfold'
        }
        resp = get_resp('POST', url=url, headers=headers, cookies=self.cookies, json=body)
        headers = resp.headers
        return response_objects.AssessmentInviteCandidateResponseType(
            email=invite_metadata.get('email'),
            invite_already_sent=False,
            assessment_id=headers['X-HvApi-Id'],
            test_url=(self.base_url + headers['Location'])
        ).to_dict()

    def fetch_reports(self, req_data):
        #position_id = req_data.get('test_id')
        return [response_objects.AssessmentReportResponse().to_dict()]

    def _convert_hv_status_to_assessment_test_status(self, status):
        if status == 'complete':
            return AssessmentTestStatus.COMPLETED
        elif status == 'not-invited':
            return AssessmentTestStatus.NOT_INVITED
        return AssessmentTestStatus.INVITED

    def _fetch_interview_object(self, position_id, interview_id):
        url = self.base_url + '/api/v1/positions/{pid}/interviews/{iid}'.format(pid=position_id, iid=interview_id)
        headers = {'X-CSRFToken': self.csrf_token}
        resp = get_resp('GET', url=url, headers=headers, cookies=self.cookies)
        payload = json.loads(resp.content) if resp.content else None
        return payload

    def _process_assessment_report_dict(self, payload):
        print(json.dumps(payload))
        report = response_objects.AssessmentReportResponse()
        invite_metadata = json.loads(payload['externalCandidateId']) if payload.get('externalCandidateId') else {}
        report.status = self._convert_hv_status_to_assessment_test_status(payload.get('status'))
        report.assessment_id = payload.get('id')
        report.test_id = invite_metadata.get('test_id')
        if not report.test_id:
            raise ValueError('position_id cannot be none for interview_id: {}'.format(report.assessment_id))
        interview_obj = self._fetch_interview_object(report.test_id, report.assessment_id)
        if not interview_obj:
            raise ValueError('Interview object cannot be none for position_id: {}, interview_id: {}'.format(report.test_id, report.assessment_id))
        report.email = payload.get('email')
        report.assigned_ts = to_timestamp(payload['createDate']) if payload.get('createDate') else None
        if report.status == AssessmentTestStatus.COMPLETED:
            report.completed_ts = to_timestamp(payload['lastStatusChangeDate']) if payload.get('lastStatusChangeDate') else None
        summary = interview_obj.get('summary')
        if summary:
            payload['summary'] = summary
            report.num_tests_total = summary.get('questionCount')
            report.num_tests_completed = summary.get('answerCount')
            report.rating = summary.get('averageRating')
        report.response_json = payload
        return invite_metadata, report.to_dict()

    def _fetch_assessment_report(self, interview_id):
        url = self.base_url + '/api/v1/interviews/?qf=[id:exact:{iid}]'.format(iid=interview_id)
        headers = {'X-CSRFToken': self.csrf_token}
        resp = get_resp('GET', url=url, headers=headers, cookies=self.cookies)
        payload = json.loads(resp.content) if resp.content else None
        if not payload:
            raise ValueError('Assessment report cannot be empty for interview_id: {}'.format(interview_id))
        return self._process_assessment_report_dict(payload[0])

    def fetch_candidate_report(self, req_data):
        interview_id = req_data.get('assessment_id')
        _, report = self._fetch_assessment_report(interview_id)
        return report

    def _is_event_processing_needed(self, event_type):
        return event_type in ['interviewFinished', 'ratingSubmitted', 'ratingRemoved', 'decisionSubmitted', 'decisionRemoved',
                              'evaluationCompleted']

    def process_webhook_request(self, req_data):
        #headers = req_data.get('headers')
        request_payload = req_data.get('request_payload')
        event_type = request_payload.get('eventType')
        resp = response_objects.AssessmentProcessWebhookResponseType()
        if not self._is_event_processing_needed(event_type):
            return resp.to_dict()
        details = request_payload.get('details')
        print('processing webhook for interview_id: {}'.format(details.get('interview_id')))
        if not details or not details.get('interview_id'):
            print('request_data doesnot have details or interview_id for event_type: {}'.format(event_type))
            return resp.to_dict()
        interview_id = details['interview_id']
        invite_metadata, report = self._fetch_assessment_report(interview_id)
        resp.invite_metadata = invite_metadata
        resp.assessment_report = report
        print('invite_metadata: {}'.format(invite_metadata))
        print('assessment_report: {}'.format(report))
        return resp.to_dict()

    def _get_account_id(self):
        url = self.base_url + '/api/v1/accounts/self/'
        headers = {'X-CSRFToken': self.csrf_token}
        resp = get_resp('GET', url=url, headers=headers, cookies=self.cookies)
        resp_dict = json.loads(resp.content)
        return resp_dict['id']

    def setup(self, req_data):
        ef_settings = req_data.get('ef_settings', {})
        notification_url = ef_settings.get('webhook_settings', {}).get('endpoint_url')
        if not notification_url:
            raise ValueError('Endpoint url cannot be None')
        account_id = self._get_account_id()
        url = self.base_url + '/api/v1/accounts/{id}/notifications/'.format(id=account_id)
        registered_urls = self.get_notification_urls()
        for ru in registered_urls:
            if ru.get('url') == notification_url:
                print('url: {} is already registered with notification service'.format(notification_url))
                resp_obj = response_objects.PostInstallResponseType()
                resp_obj.is_success = True
                return resp_obj.to_dict()
        headers = {'X-CSRFToken': self.csrf_token}
        body = {'url': notification_url}
        get_resp('POST', url=url, headers=headers, cookies=self.cookies, json=body)
        resp_obj = response_objects.PostInstallResponseType()
        resp_obj.is_success = True
        return resp_obj.to_dict()

    def get_notification_urls(self):
        account_id = self._get_account_id()
        url = self.base_url + '/api/v1/accounts/{id}/notifications/'.format(id=account_id)
        headers = {'X-CSRFToken': self.csrf_token}
        resp = get_resp('GET', url=url, headers=headers, cookies=self.cookies)
        return json.loads(resp.content) if resp.content else []

    def delete_notification_url(self, notification_id):
        account_id = self._get_account_id()
        url = self.base_url + '/api/v1/accounts/{id}/notifications/{notification_id}'.format(id=account_id, notification_id=notification_id)
        headers = {'X-CSRFToken': self.csrf_token}
        resp = get_resp('DELETE', url=url, headers=headers, cookies=self.cookies)
        return resp.content

def app_handler(event, context):
    app_settings = event.get('app_settings', {})

    ha = AssessmentAdapter(app_settings)

    req_data = event.get('request_data', {})
    trigger_name = req_data.get('trigger_name')

    print('Call recived for trigger_name: {}'.format(trigger_name))
    data = None
    try:
        if trigger_name == 'assessment_get_logo_url':
            data = ha.get_logo_url()
        elif trigger_name == 'assessment_is_webhook_supported':
            data = ha.is_webhook_supported()
        elif trigger_name == 'assessment_list_tests':
            ha.login()
            data = ha.list_tests(req_data)
        elif trigger_name == 'assessment_invite_candidate':
            ha.login()
            suppress_participants_email = app_settings.get('suppress_participants_email')
            data = ha.invite_candidate(req_data, suppress_participants_email)
        elif trigger_name == 'assessment_fetch_reports':
            ha.login()
            data = ha.fetch_reports(req_data)
        elif trigger_name == 'assessment_fetch_candidate_report':
            ha.login()
            data = ha.fetch_candidate_report(req_data)
        elif trigger_name == 'assessment_process_webhook':
            ha.login()
            data = ha.process_webhook_request(req_data)
        elif trigger_name == 'post_install':
            ha.login()
            data = ha.setup(req_data)
    except Exception as ex:
        err_str = 'Handler for trigger_name: {} failed with error: {}, traceback: {}'.format(
            trigger_name, str(ex), traceback2.format_exc())
        print(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback2.format_exc(),
            }),
        }

    finally:
        ha.logout()

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
