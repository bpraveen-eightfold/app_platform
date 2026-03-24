import json
#from zeep import Client, xsd

import response_objects
from base_adapter import BaseAdapter

import logging.config

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'zeep.transports': {
            'level': 'DEBUG',
            'propagate': True,
            'handlers': ['console'],
        },
    }
})

class AssessmentAdapter(BaseAdapter):
    def __init__(self, credentials):
        API_URL = 'https://www.pymetrics.com/integrations/webservice/v3/wsdl/'

        self.credentials = credentials
        
#       client = Client(wsdl=API_URL)
#       session_id = client.service.authenticate(credentials.get('client_id'), credentials.get('client_secret')).session_id
#       header_factory = xsd.Element(
#           "{pym.intg.ws.3.0.0}RequestHeader",
#           xsd.ComplexType([
#               xsd.Element("{https://www.pymetrics.com/integrations/webservice/v3/wsdl/}client_id", xsd.String()),
#               xsd.Element("{https://www.pymetrics.com/integrations/webservice/v3/wsdl/}session_id", xsd.String()),
#           ])
#       )
#       auth_header = header_factory(client_id=credentials.get('client_id'), session_id=session_id)
#       self.soap_client = client
#       self.auth_header = auth_header
#

    def get_logo_url(self):
        return 'https://res-5.cloudinary.com/crunchbase-production/image/upload/c_lpad,h_256,w_256,f_auto,q_auto:eco/v1505930291/hkrze217niqryaj2j9cc.png'

    def is_webhook_supported(self):
        return False

    def list_tests(self):
        #list_assessments_request = self.soap_client.get_type("{integrations.webservice.ws_models}WSListAssessmentRequest")()
        #list_assessments_request['organization_id'] = self.credentials.get('organization_id')
        
        # response = self.soap_client.service.list_assessments(
        #   list_assessments_request,
        #   _soapheaders=[self.auth_header],
        # )

        # tests = response.get('WSListAssessmentResponse', []) if response else []
        tests = [
            {
                'assessment_id': '8129',
                'assessment_name': 'Sample Test 1',
            }
        ]
        return [
            response_objects.EFListAssessmentsResponse(
                assessment_id=test.get('assessment_id'),
                name=test.get('assessment_name'),
                published=True,
            ).to_dict()
            for test in tests
        ]

    def invite_candidate(self, test_id, invite_metadata):
        #assessment_order_request = self.soap_client.get_type("{integrations.webservice.ws_models}AssessmentOrderRequest")()
        #assessment_order_request.assessment_id = test_id
        #assessment_order_request.email = invite_metadata.get('email')
        #assessment_order_request.external_id = invite_metadata.get('candidate_id')
        #assessment_order_request.first_name = invite_metadata.get('firstname')
        #assessment_order_request.last_name = invite_metadata.get('lastname')
        #assessment_order_request.application_locale = invite_metadata.get('application_locale', 'en')
        # print(self.auth_header)
        # print(type(assessment_order_request), assessment_order_request, assessment_order_request.__dict__)
        # response = self.soap_client.service.request_assessment_order(
        #   assessment_order_request,
        #   _soapheaders=[self.auth_header],
        # )

        # response = response if response and response.get('success') == True else {}
        return response_objects.EFAssessmentInviteResponse(
            email=invite_metadata.get('email'),
            invite_already_sent=True,
                        assessment_id='1234'
        ).to_dict()

    def fetch_reports(self, order_ids):
        return self.soap_client.service.get_bulk_results(order_ids=order_ids, _soapheaders=[self.auth_header])

    def fetch_candidate_report(self, order_id):
        # response = self.soap_client.service.get_report(order_id=order_id, _soapheaders=[self.auth_header])
        ret = response_objects.EFAssessmentReportResponse()
        # ret.report_url = response.get('report_url')
        ret.report_url = 'https://app.eightfold.ai'
        ret.status = 'completed'
        return ret.to_dict()

def app_handler(event, context):
    app_settings = event.get('app_settings', {})
    partner_key = app_settings.get('partner_key')
    CREDENTIALS = app_settings.get('credentials', {})
    CREDENTIALS['partner_key'] = partner_key

    PymetricsAdapter = AssessmentAdapter(CREDENTIALS)

    req_data = event.get('request_data', {})
    trigger_name = event.get('trigger_name')

    data = None
    if trigger_name == 'assessment_get_logo_url':
        data = PymetricsAdapter.get_logo_url()
    elif trigger_name == 'assessment_is_webhook_supported':
        data = PymetricsAdapter.is_webhook_supported()
    elif trigger_name == 'assessment_list_tests':
        data = PymetricsAdapter.list_tests()
    elif trigger_name == 'assessment_invite_candidate':
        test_id = req_data.get('test_id')
        invite_metadata = req_data.get('invite_metadata')
        data = PymetricsAdapter.invite_candidate(test_id, invite_metadata)
    elif trigger_name == 'assessment_fetch_reports':
        order_ids = req_data.get('order_ids')
        data = PymetricsAdapter.fetch_reports(order_ids)
    elif trigger_name == 'assessment_fetch_candidate_report':
        order_id = req_data.get('assessment_id')
        data = PymetricsAdapter.fetch_candidate_report(order_id)

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }

#credentials = {
#   'client_id': 'NkseV0nrcCaYjmiFs7gHuYXeRGy6NdMlHmEKfVNe',
#   'client_secret': 'JClWJ7hof2pu0Mb3jelZY1GmxjWckzSHQsCyNkjuBpVbGEdXhlrgG00uFDDir6b48VFYaf8VTRWM0OHWVSO5kwcZV1genyMxux9DI6QXQj7sib9Yu1beLoIEBxsfEBZJ',
#   'organization_id': 'XYZ123',
#}
#
#PymetricsAdapter = AssessmentAdapter(credentials)
#print(PymetricsAdapter)
#print(PymetricsAdapter.get_logo_url())
##print(PymetricsAdapter.soap_client.service.echo('hi team', _soapheaders=[PymetricsAdapter.auth_header]))
#print(json.dumps({'data': PymetricsAdapter.invite_candidate(
#       '7329caa9-3b12-486f-847d-42b0d71deac7', 
#       {'email': 'gauravg@eightfold.ai', 'firstname': 'Gaurav', 'lastname': 'Gupta', 'candidate_id': 12345, 'application_locale': 'en'},
#   )}))
#
#print(PymetricsAdapter.fetch_candidate_report(123))
#
