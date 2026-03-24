# pylint: disable=ef-restricted-imports, unused-variable, unused-import
"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import
import json
import requests
import traceback2
from collections import OrderedDict

import response_objects
from base_adapter import BaseAdapter

class SFDCAdapter(BaseAdapter):
    AUTH_DATA_TEMPLATE = 'grant_type=password&client_id={client_id}&client_secret={client_secret}&username={username}&password={password}'
    API_VERSION = "/services/data/v51.0/query/?q="
    SFDC_QUERY = {
        'ALL_WON_OPPORTUNITIES': "SELECT Id, AccountId, Name, StageName, CloseDate, Amount, Product_of_Interest__c, Account_Manager__c FROM opportunity WHERE isWon = true ORDER BY Amount DESC LIMIT 50",
        'WON_OPPORTUNITY_FROM_ID': "SELECT Id, AccountId, Name, StageName, CloseDate, Amount, Product_of_Interest__c, Account_Manager__c FROM opportunity WHERE isWon = true AND Id = '{entity_id}' LIMIT 50",
        'ACCOUNTS_FROM_ACCOUNT_IDS': "SELECT Id, ATS__c, CRM__c, HRIS__c, Name, Industry, Segment__c, NF_LSCompanySizeExact__c, BillingCity, BillingState, BillingCountry FROM account WHERE Id in {account_ids}",
    }

    def __init__(self, instance_url, access_token):
        self.instance_url = instance_url
        self.access_token = access_token

    @classmethod
    def get_adapter(cls, app_settings):
        token_url = app_settings.get('token_url')
        client_id = app_settings.get('client_id')
        client_secret = app_settings.get('client_secret')
        username = app_settings.get('username')
        password = app_settings.get('password')

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth_data = SFDCAdapter.AUTH_DATA_TEMPLATE.format(
            username=username,
            password=password,
            client_id=client_id,
            client_secret=client_secret,
        )
        response = requests.post(token_url, headers=headers, data=auth_data, timeout=60).json()
        adapter = cls(response.get('instance_url'), response.get('access_token'))
        return adapter

    @staticmethod
    def _groupby(iterable, key, to_dict=False):
        ret = OrderedDict()
        for i in iterable:
            k = key(i)
            if k not in ret:
                ret[k] = []
            ret[k].append(i)
        return ret if to_dict else list(ret.items())

    def _get_details_response_obj(self, data):
        resp_obj = response_objects.CareerhubEntityDetailsResponseType()
        resp_obj.entity_id = data.get('id')
        resp_obj.title = data.get('name')
        resp_obj.cta_url = '{}/{}'.format(self.instance_url, data.get('id'))
        resp_obj.cta_label = 'Opportunity'
        resp_obj.source_name = data.get('description')
        resp_obj.description = data.get('description')
        resp_obj.fields = data.get('fields')
        resp_obj.image_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/220px-Salesforce.com_logo.svg.png'

        return resp_obj

    def get_response_for_query(self, query):
        url = self.instance_url + SFDCAdapter.API_VERSION + query
        headers = {'Authorization': 'Bearer ' + self.access_token}
        response = requests.get(url, headers=headers, timeout=60)
        response_json = response.json()
        return response_json

    def get_entity_search_results(self, req_data):
        start = req_data.get('start')
        end = start + req_data.get('limit')
        opportunities = self.get_opportunities()
        resp_obj = response_objects.CareerhubEntitySearchResultsResponseType()
        resp_obj.num_results = len(opportunities)
        resp_obj.entities = [self._get_details_response_obj(o).to_dict() for o in opportunities[start:end]]
        return resp_obj.to_dict()

    def get_entity_details(self, req_data):
        entity_id = req_data.get('entity_id')
        opportunities = self.get_opportunities(entity_id)
        opportunity = next((o for o in opportunities if o.get('id') == entity_id), {})
        return self._get_details_response_obj(opportunity).to_dict()

    def get_opportunities(self, entity_id=None):
        response = None
        if entity_id:
            response = self.get_response_for_query(SFDCAdapter.SFDC_QUERY.get('WON_OPPORTUNITY_FROM_ID').format(entity_id=entity_id))
        else:
            response = self.get_response_for_query(SFDCAdapter.SFDC_QUERY.get('ALL_WON_OPPORTUNITIES'))

        account_id_to_opportunities = SFDCAdapter._groupby(response.get('records', []), key=lambda x: x.get('AccountId'), to_dict=True)
        account_ids = list(account_id_to_opportunities.keys())

        account_ids_tuple_string = "('{}')".format("','".join(account_ids))
        response = self.get_response_for_query(SFDCAdapter.SFDC_QUERY.get('ACCOUNTS_FROM_ACCOUNT_IDS').format(account_ids=account_ids_tuple_string))
        account_id_to_account = SFDCAdapter._groupby(response.get('records', []), key=lambda x: x.get('Id'), to_dict=True)

        all_opportunities = []
        for a_id in account_ids:
            account = account_id_to_account.get(a_id)[0]
            account_opportunities = account_id_to_opportunities.get(a_id)

            account_info = {
                'ats': account.get('ATS__c'),
                'crm': account.get('CRM__c'),
                'hris': account.get('HRIS__c'),
                'customerName': account.get('Name'),
                'industry': account.get('Industry'),
                'segment': account.get('Segment__c'),
                'companySize': account.get('NF_LSCompanySizeExact__c'),
                'location': '{}, {}, {}'.format(account.get('BillingCity'), account.get('BillingState'), account.get('BillingCountry')),
            }

            if not account_info.get('ats'):
                continue

            for opportunity in account_opportunities:
                amount = '${:,.2f}'.format(opportunity.get('Amount'))
                fields = [
                    ('Customer', account_info.get('customerName')),
                    ('Date Closed', opportunity.get('CloseDate')),
                    ('TCV', amount),
                    ('Location', account_info.get('location')),
                    ('Industry', account_info.get('industry')),
                    ('Company Size', account_info.get('companySize')),
                    ('Customer Segment', account_info.get('segment')),
                    ('Products', ', '.join((opportunity.get('Product_of_Interest__c', '') or '').split(';'))),
                    ('ATS', account_info.get('ats')),
                    ('HRIS', account_info.get('hris')),
                    ('CRM', account_info.get('crm')),
                ]

                fields = [{'name': name, 'value': value} for name, value in fields if value]

                all_opportunities.append({
                    **account_info,
                    'tcv': amount,
                    'fields': fields,
                    'id': opportunity.get('Id'),
                    'name': opportunity.get('Name'),
                    'stage': opportunity.get('StageName'),
                    'closeDate': opportunity.get('CloseDate'),
                    'products': opportunity.get('Product_of_Interest__c'),
                    'accountManger': opportunity.get('Account_Manager__c'),
                    'description': '{} (TCV: {} · {})'.format(account_info.get('customerName'), amount, opportunity.get('CloseDate'))
                })

        return all_opportunities

def app_handler(event, context):
    trigger_name = event.get('trigger_name')
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})

    data = None
    try:
        adapter = SFDCAdapter.get_adapter(app_settings)
        if trigger_name == 'careerhub_entity_search_results':
            data = adapter.get_entity_search_results(request_data)
        elif trigger_name == 'careerhub_get_entity_details':
            data = adapter.get_entity_details(request_data)
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

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data, 'cache_ttl_seconds': 60})
    }
