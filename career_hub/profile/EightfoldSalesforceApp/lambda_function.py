import json
import copy
from datetime import datetime
import requests
import traceback2
import locale
locale.setlocale(locale.LC_ALL, '')
from jinja2.nativetypes import NativeEnvironment


SALESFORCE_LOGO_URL = 'https://static.vscdn.net/images/career_hub/profile/salesforce.png'
REQUIRED_FIELDS = ['instance_url', 'business_unit_to_query_info']
NUM_RECORDS = 3

def get_native_env_from_string(template_str):
    env = NativeEnvironment()
    filter_template = env.from_string(template_str)
    return filter_template

def substitute_template(template_str, entity_dict):
    filter_template = get_native_env_from_string(template_str)
    subst_string = filter_template.render(**entity_dict)
    return subst_string

class SalesforceConnector():

    def __init__(self, request_data, app_settings):
        self.app_settings = app_settings
        self.instance_url = self.app_settings.get('instance_url')
        self.access_token = request_data.get('oauth_token')
        # change keys in business_unit_to_query_info to lower case
        tmp_dict = {}
        for key in self.app_settings.get('business_unit_to_query_info').keys():
            tmp_dict[key.lower()] = self.app_settings['business_unit_to_query_info'][key]
        self.app_settings['business_unit_to_query_info'] = copy.deepcopy(tmp_dict)

    def get_resp(self, url):
        headers = {
            "Authorization": "Bearer " + self.access_token
        }
        resp = requests.get(url, headers=headers, timeout=60)
        if resp.status_code != 200:
            raise ValueError(resp.content)
        resp_json = resp.json()
        if isinstance(resp_json, list) and resp_json and resp_json[0].get('errorCode'):
            error_msg = 'get failed for url: {} with resp: {}'.format(url, resp_json)
            print(error_msg)
            raise ValueError(error_msg)
        return resp_json

    def get_query_data(self, email, business_unit, query_type):
        query_info = self.app_settings.get('business_unit_to_query_info').get(business_unit)
        variable_name = query_info.get('variable_name')
        query = substitute_template(query_info[query_type], {variable_name: email})
        url = self.instance_url + "/services/data/v49.0/query/?q=" + query
        return self.get_resp(url)

    def _process_sales_data(self, sales_data):
        owner_set = set()
        won_amount = 0
        for record in sales_data['records']:
            won_amount += record.get('Amount', 0) if record.get('Amount') else 0
            owner_set.add(record.get('Owner')['Name'])
        return won_amount, len(owner_set) > 1

    def _process_last_quarter_data_1(self, current_quarter_data, is_manager):
        if is_manager:
            return True
        owner_set = set()
        for record in current_quarter_data['records']:
            owner_set.add(record.get('Owner')['Name'])
        return len(owner_set) > 1

    def _process_current_quarter_data(self, current_quarter_data, is_manager):
        table_data = []
        if not is_manager:
            # the data is of individual contributor
            for record in current_quarter_data["records"]:
                close_date = datetime.strptime(record.get('CloseDate'), '%Y-%m-%d') if record.get('CloseDate') else None
                amount = int(record.get('Amount', 0)) if record.get('Amount') else 0
                amount_str = '$' + locale.format('%d', amount, grouping=True) if amount else '-'
                record_type = record.get('attributes', {}).get('type')
                record = {
                    "link": self.instance_url + "/" + record["Id"],
                    "text1": record.get("Name"),
                    "text2": amount_str,
                    "text3": record.get('StageName', '').split('.')[-1].strip(),
                    "text4": close_date.strftime('%m-%d-%y') if close_date else '',
                    'amount': amount
                }
                table_data.append(record)
            return sorted(table_data, key=lambda i: i['amount'], reverse=True)
        # the data is of manager
        owner_to_sales_data = {}
        for record in current_quarter_data['records']:
            owner_name = record.get('Owner')['Name']
            if not owner_to_sales_data.get(owner_name):
                owner_to_sales_data[owner_name] = {'amount': record.get('Amount', 0) if record.get('Amount') else 0,
                                                    'num_oppo': 1}
            else:
                owner_to_sales_data[owner_name]['amount'] += record.get('Amount', 0) if record.get('Amount') else 0
                owner_to_sales_data[owner_name]['num_oppo'] += 1
        for key, val in owner_to_sales_data.items():
            amount_str = '$' + locale.format('%d', int(val['amount']), grouping=True)
            table_data.append({'owner_name': key,
                               'amount_str': amount_str,
                               'num_oppo': val['num_oppo'],
                               'amount': int(val['amount'])})
        return sorted(table_data, key=lambda i: i['amount'], reverse=True)


    def get_sales_opportunities(self, email, business_unit):
        current_quarter_data = self.get_query_data(email, business_unit, 'current_quarter_opportunity_query')
        last_quarter_won_data = self.get_query_data(email, business_unit, 'last_quarter_won_query')
        won_total, is_manager1 = self._process_sales_data(last_quarter_won_data)
        opportunity_amount, is_manager2 = self._process_sales_data(current_quarter_data)
        is_manager = is_manager1 or is_manager2
        table_data = self._process_current_quarter_data(current_quarter_data, is_manager)
        data = {'is_manager': is_manager,
                'won_total': '$' + locale.format('%d', int(won_total), grouping=True),
                'opportunity_amount': '$' + locale.format('%d', int(opportunity_amount), grouping=True),
                'table_data': table_data
               }

        return data

    def get_sdr_data(self, email, business_unit):
        sdr_data = self.get_query_data(email, business_unit, 'query')
        table_data = []
        for record in sdr_data['records']:
            created_date = datetime.strptime(record.get('CreatedDate').split('T')[0], '%Y-%m-%d') if record.get('CreatedDate') else None
            table_data.append({'Company': record.get('Company'),
                               'link': self.instance_url + "/" + record["Id"],
                                'CreatedDate': created_date.strftime('%m-%d-%y') if created_date else '',
                              })
            if len(table_data) >= NUM_RECORDS:
                break
        return {'total_leads': sdr_data['totalSize'],
                'table_data': table_data
               }

    def get_engagement_manager_data(self, email, business_unit):
        em_data = self.get_query_data(email, business_unit, 'query')
        table_data = []
        for record in em_data['records']:
            deadline_date = datetime.strptime(record.get('MPM4_BASE__Deadline__c'), '%Y-%m-%d') if record.get('MPM4_BASE__Deadline__c') else None
            table_data.append({'Name': record['MPM4_BASE__Account__r'].get('Name'),
                               'link': self.instance_url + "/" + record["Id"],
                               'Status': record.get('Overall_Project_Status__c'),
                               'DeadlineDate': deadline_date.strftime('%m-%d-%y') if deadline_date else '',
                              })
            if len(table_data) >= NUM_RECORDS:
                break
        return {'total_size': em_data['totalSize'],
                'table_data': table_data
               }

def app_handler(event, context):
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings')

    email = request_data.get('employee_email') or request_data.get('email')
    business_unit = request_data.get('business_unit')
    if not email or not business_unit:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Please provide email and business_unit in request_data'}),
        }

    if not app_settings:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'App settings cannot be none'}),
        }

    for field in REQUIRED_FIELDS:
        if not app_settings.get(field):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Field {} cannot be none in app settings'.format(field)}),
            }

    sc = SalesforceConnector(request_data, app_settings)
    try:
        print('Fetching data for email: {}'.format(email))
        data = {
            'title': 'Salesforce',
            'logo_url': SALESFORCE_LOGO_URL,
            'subtitle': '@{}'.format(request_data.get('fullname')) if request_data.get('fullname') else ''
        }
        if business_unit.lower() == 'sales':
            sales_data = sc.get_sales_opportunities(email, business_unit.lower())
            is_manager = sales_data['is_manager']
            data['tiles'] = [
                    {'header': 'Pipeline current quarter', 'value': sales_data['opportunity_amount']},
                    {'header': 'Closed last quarter', 'value': sales_data['won_total']}
            ]
            rows = []
            count = 0
            for record in sales_data.get('table_data'):
                if not is_manager:
                    rows.append([{'value': record.get('text1'),
                                  'link': record.get('link')},
                                 {'value': record.get('text2')},
                                 {'value': record.get('text3')},
                                 {'value': record.get('text4')}
                                ])
                else:
                    rows.append([{'value': record.get('owner_name')},
                                 {'value': record.get('amount_str')},
                                 {'value': str(record.get('num_oppo'))}
                                ])
                count += 1
                if count >= NUM_RECORDS:
                    break

            if rows:
                data['table'] = {
                    'headers': ['Opportunity', 'Amount', 'Stage', 'Close Date'] if not is_manager else ['Team Member', 'Opportunity', 'Num Opportunity'],
                    'rows': rows
                }
                if is_manager:
                    data['footer'] = "* For {}'s sales team".format(request_data.get('firstname')) if request_data.get('firstname') else ''
        elif business_unit.lower() == 'marketing':
            sdr_data = sc.get_sdr_data(email, business_unit.lower())
            data['tiles'] = [
                    {'header': 'Leads current quarter', 'value': sdr_data['total_leads']}
            ]
            rows = []
            for record in sdr_data.get('table_data'):
                rows.append([{'value': record.get('Company'),
                              'link': record.get('link')},
                             {'value': record.get('CreatedDate')}
                            ])
                if len(rows) >= NUM_RECORDS:
                    break
            if rows:
                data['table'] = {
                    'headers': ['Company', 'Created Date'],
                    'rows': rows
                }
        elif business_unit.lower() == 'professional services':
            em_data = sc.get_engagement_manager_data(email, business_unit.lower())
            data['tiles'] = [
                    {'header': 'Total Accounts', 'value': em_data['total_size']}
            ]
            rows = []
            for record in em_data.get('table_data'):
                rows.append([{'value': record.get('Name'),
                              'link': record.get('link')},
                             {'value': record.get('Status')},
                             {'value': record.get('DeadlineDate')}
                            ])
                if len(rows) >= NUM_RECORDS:
                    break
            if rows:
                data['table'] = {
                    'headers': ['Account', 'Status', 'Deadline Date'],
                    'rows': rows
                }
        else:
            data['error'] = 'Sorry, there is no Salesforce data for this user.'

    except Exception as ex:
        print(traceback2.format_exc())
        print(str(ex))
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(ex) or 'Internal Error',
                                'stacktrace': traceback2.format_exc()}),
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
    }
