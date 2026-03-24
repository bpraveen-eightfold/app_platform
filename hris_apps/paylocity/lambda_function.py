import json
import os
import pandas as pd
import requests
import datetime
import time

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait

from transfer import Sftp

column_list = ['LAST_NAME', 'FIRST_NAME', 'FULL_NAME', 'PREFERRED_FIRST_NAME', 'EMAIL', 'PHONE',
               'HIRING_DATE', 'CURRENT_ROLE_START_DATE', 'TERMINATION_DATE', 'TITLE', 'JOB_LEVEL', 'EMPLOYEE_ID',
               'MANAGER_ID', 'LOCATION',
               'LAST_ACTIVITY_TS', 'BUSINESS_UNIT', 'COMPANY_NAME', 'JOB_CODE', 'EMPLOYEE_TYPE', 'EF_CUSTOM_JOB_CODE',
               'EFCUSTOM_TEXT_SUB_DEPT', 'EFCUSTOM_TEXT_SUB_DEPT2']

ACCESS_TOKEN_URL = 'https://api.paylocity.com/IdentityServer/connect/token'

THIRTY_DAY_IN_S = 30 * 24 * 60 * 60
DAY_IN_S = 24 * 60 * 60


class PaylocityConnector():
    def __init__(self, company_id, client_id, client_secret, employee_type_filters, bu_mapping, max_termination_days,
                 override_entries=None):
        ''' override entries are of form
        {
            "EMPLOYEE_ID": {
                "FIELD_NAME1": "OVERRIDE_VALUE1",
                "FIELD_NAME2": "OVERRIDE_VALUE2",
                ...
            },
            ...
        }
        '''
        self.company_id = company_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.company_id = company_id
        self.active_employee_ids = []
        self.terminated_employee_ids = []
        self.max_termination_days = max_termination_days
        self.employee_type_filter = employee_type_filters
        self.bu_mapping = bu_mapping
        self.employees_results = {}
        self.override_entries = override_entries or {}
        data = {'grant_type': 'client_credentials', 'scope': 'WebLinkAPI'}
        auth = (client_id, client_secret)
        self.access_token = requests.post(ACCESS_TOKEN_URL, data=data, auth=auth).json().get('access_token')

    def get_employees(self):
        headers = {'Authorization': 'Bearer ' + self.access_token}
        pagesize = 100
        params = {
            "pagesize": pagesize,
            "pagenumber": 0
        }
        employees = requests.get('https://api.paylocity.com/api/v2/companies/{}/employees/'.format(self.company_id),
                                 headers=headers, params=params)
        for employee in employees.json():
            if self._is_active_employee(employee):
                self.active_employee_ids.append(employee.get('employeeId'))
            elif self._is_terminated_employee(employee):
                self.terminated_employee_ids.append(employee.get('employeeId'))
        total_employees = employees.headers.get('X-Pcty-Total-Count')
        total_pages = int(int(total_employees) / pagesize) + 1

        for i in range(1, total_pages + 1):
            params = {
                "pagesize": pagesize,
                "pagenumber": i
            }
            employees = requests.get('https://api.paylocity.com/api/v2/companies/{}/employees/'.format(self.company_id),
                                     headers=headers, params=params)
            for employee in employees.json():
                if self._is_active_employee(employee):
                    self.active_employee_ids.append(employee.get('employeeId'))
                elif self._is_terminated_employee(employee):
                    self.terminated_employee_ids.append(employee.get('employeeId'))

    def _is_active_employee(self, employee):
        return employee.get('statusTypeCode') == 'A' or employee.get('statusTypeCode') == 'L' or employee.get(
            'statusType') == 'A'

    def _is_terminated_employee(self, employee):
        return employee.get('statusTypeCode') == 'T'

    def _employee_details(self, employee_id):
        headers = {
            'Authorization': 'Bearer ' + self.access_token
        }
        try:
            res = requests.get(
                'https://api.paylocity.com/api/v2/companies/{}/employees/{}'.format(self.company_id, employee_id),
                headers=headers)
            retries = 1
            while res.status_code in [429, 500] and retries <= 3:
                retries += 1
                print('Retrying for employee {}. retry: {}'.format(employee_id, retries))
                time.sleep(1)
                res = requests.get(
                    'https://api.paylocity.com/api/v2/companies/{}/employees/{}'.format(self.company_id, employee_id),
                    headers=headers)
            if res.status_code != 200 and employee_id in self.active_employee_ids:
                # print('Error getting details of active employee {}'.format(employee_id))
                raise Exception(
                    'Error getting details of active employee {}. status code: {}\n reson: {}'.format(employee_id,
                                                                                                      res.status_code,
                                                                                                      res.reason))
            if res.status_code == 200:
                print('Found data for employee {}'.format(employee_id))
                return res.json()
            if employee_id in self.terminated_employee_ids and res.status_code != 200:
                print('Terminated {} details not found'.format(employee_id))
                return None
        except requests.exceptions.RequestException as e:
            print(e)

    def get_employees_results(self, employees: list):
        with ThreadPoolExecutor(max_workers=1) as executor:
            results = executor.map(self._employee_details, employees)
            executor.shutdown()
        for result in results:
            if result and 'employeeId' in result:
                self.employees_results[result['employeeId']] = result

    def get_employee_details(self, employee_id):
        return self.employees_results[employee_id] if employee_id in self.employees_results else self._employee_details(
            employee_id)

    def get_formatted_date(self, indate, informat='%Y-%m-%dT%H:%M:%S', outformat='%m/%d/%y', strip_leading_zeros=True):
        if not indate:
            return None
        outdate = datetime.datetime.strptime(indate, informat).strftime(outformat)
        if not strip_leading_zeros:
            return outdate
        parts = []
        for part in outdate.split('/'):
            if part.startswith('0'):
                parts.append(part[1:])
            else:
                parts.append(part)
        return '/'.join(parts)

    def get_employee_row(self, employee_details, email_domain, employee_types):
        # it is possible for employee_details to be None, in that case return a default value
        if not employee_details:
            return []
        employee_id = employee_details.get('employeeId')
        overrides = self.override_entries.get(employee_id) or {}
        first_name = overrides.get('FIRST_NAME') or employee_details.get('firstName') or employee_details.get(
            'preferredName')
        last_name = overrides.get('LAST_NAME') or employee_details.get('lastName') or employee_details.get(
            'priorLastName')
        full_name = '{} {}'.format(first_name, last_name)
        preferred_first_name = employee_details.get('preferredName')

        email = employee_details.get('workAddress').get('emailAddress')
        # if an email_domain is provided then adjust the email as appropriate
        if email_domain:
            if not email:
                email = 'unknown@' + email_domain
            elif not email.endswith(email_domain):
                # cases where email is neither user@email_domain not user@ext.email_domain replace the email_domain
                # and is useful mostly for testing scenarios
                current_email_domain = email.split('@')[1]
                email = email.replace(current_email_domain, email_domain)

        phone = overrides.get('PHONE') or employee_details.get('workAddress').get(
            'mobilePhone') or employee_details.get('workAddress').get('phone') or \
                employee_details.get('homeAddress').get('mobilePhone') or employee_details.get('homeAddress').get(
            'phone')

        hire_date = employee_details.get('status').get('reHireDate') or employee_details.get('status').get('hireDate')
        hire_date = self.get_formatted_date(hire_date)
        hire_date = overrides.get('HIRING_DATE') or hire_date

        current_role_start_date = employee_details.get('status').get('adjustedSeniorityDate') or employee_details.get(
            'status').get('reHireDate') or employee_details.get('status').get('hireDate')
        current_role_start_date = self.get_formatted_date(current_role_start_date)
        current_role_start_date = overrides.get('CURRENT_ROLE_START_DATE') or current_role_start_date

        # TODO: If termination date is old say > 6mo, skip adding this record
        termination_date = employee_details.get('status').get('terminationDate')
        override_termination_date = self.get_formatted_date(
            indate=overrides.get('TERMINATION_DATE'),
            informat='%m/%d/%y',
            outformat='%Y-%m-%dT%H:%M:%S'
        )
        termination_date = override_termination_date or termination_date
        if self._is_old_employee_termination(termination_date):
            return []

        department = employee_details.get('departmentPosition')
        if not department or department.get('employeeType') not in employee_types:
            return []
        title = None
        manager_id = None
        business_unit = None
        # extract sub-departments from costCenter3 and costCenter2
        efcustom_text_sub_dept2 = ''
        efcustom_text_sub_dept = ''
        last_modified_ts = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')
        employee_type = None
        if department:
            title = department.get('jobTitle', '').strip()
            manager_id = department.get('supervisorEmployeeId')

            efcustom_text_sub_dept2 = department.get('costCenter3')
            efcustom_text_sub_dept = department.get('costCenter2')
            business_unit = self.bu_mapping.get(department.get('costCenter1'), department.get('costCenter1'))
            employee_type = department.get('employeeType')
        location = employee_details.get('workAddress').get('location')
        company_name = employee_details.get('companyName')

        # Eightfold specific behavior: read 'Job Code' field from customTextFields to derive `job_code`` and `level`` fields
        job_code = ''
        job_level = ''
        ef_custom_job_code = ''
        custom_text_fields = employee_details.get('customTextFields', [])

        for custom_text_field in custom_text_fields:
            if custom_text_field.get('label') == 'Job Code':
                job_code = custom_text_field.get('value')
                ef_custom_job_code, job_level = _parse_job_code_value_str(custom_text_field.get('value'))
                ef_custom_job_code = ef_custom_job_code + '_' + efcustom_text_sub_dept2
                break

        termination_date = self.get_formatted_date(termination_date)

        return [last_name, first_name, full_name, preferred_first_name, email, phone, hire_date,
                current_role_start_date, termination_date, title, job_level, employee_id, manager_id, location,
                last_modified_ts, business_unit, company_name, job_code, employee_type, ef_custom_job_code,
                efcustom_text_sub_dept, efcustom_text_sub_dept2]

    def generate_csv(self, df, f_name):
        f_name = f_name + datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d') + ".csv"
        local_path = os.path.join('/tmp/' + f_name)
        df.to_csv(local_path, index=False)
        return local_path

    def _is_old_employee_termination(self, termination_date):
        if not termination_date:
            return False
        termination_timestamp = datetime.datetime.strptime(termination_date, '%Y-%m-%dT%H:%M:%S').timestamp()
        return (time.time() - termination_timestamp) > (self.max_termination_days * DAY_IN_S)

    def _get_later_timestamp(self, department_effective_date, termination_date):
        """Paylocity API does not provide an explicit latest activity timestamp so pick
        between the department effective date and termination date. Special nuance here is
        that termination date can be in the future and returning a latest timestamp
        from the future does not make sense.
        """
        # this is an expected scenario
        if not termination_date:
            return department_effective_date
        # this case should not happen apart from bad data
        if not department_effective_date:
            return termination_date
        now_dt_obj = datetime.datetime.now()
        ed_dt_obj = datetime.datetime.strptime(department_effective_date, '%Y-%m-%dT%H:%M:%S')
        td_dt_obj = datetime.datetime.strptime(termination_date, '%Y-%m-%dT%H:%M:%S')

        # if termination date is greater than department effective date and is not in the future then
        # use that as the later timestamp
        if td_dt_obj >= ed_dt_obj and td_dt_obj <= now_dt_obj:
            return termination_date
        return department_effective_date


def _parse_job_code_value_str(value_str):
    """
    Given the 'Job Code' custom field value string,
    parse and return the job_code and level values.
    Format of the string: xx-xx-job_code.level
    """
    parsed_strs = value_str.split('-')
    if len(parsed_strs) != 3:
        print('Got a wrong string format for Job Code custom field')
        return '', ''
    job_code_and_level = parsed_strs[-1]
    # EN.SOMF.P5.5 is a valid entry where EN.SOMF is the job code and P5.5 is the job level
    # Our implementation will need to split both the string at the second (.) dot.
    split_idx = job_code_and_level.find('.', job_code_and_level.find('.') + 1)
    if split_idx < 0 or split_idx >= len(job_code_and_level):
        print('Got a wrong string format for job_code and level encoding')
        return '', ''
    return job_code_and_level[:split_idx], job_code_and_level[split_idx + 1:]


def app_handler(event, context):
    # Early return if not the right trigger
    if not event.get('trigger_name').startswith('scheduled_'):
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'unknownTrigger'})
        }

    app_settings = event.get('app_settings')
    client_id = app_settings.get('client_id')
    client_secret = app_settings.get('client_secret')
    company_id = app_settings.get('company_id')
    email_domain = app_settings.get('email_domain')
    csv_file_name = 'employee_data'
    employee_types = app_settings.get('employee_type_filter', 'RFT, RPT, UIN, UTR, CNT, TFT, TPT').replace(' ',
                                                                                                           '').split(
        ',')
    bu_mapping = app_settings.get('bu_mapping')
    override_entries = app_settings.get('override_entries') or {}
    max_termination_days = app_settings.get('max_termination_days') or 30
    pc = PaylocityConnector(company_id, client_id, client_secret, employee_types, bu_mapping, max_termination_days,
                            override_entries)

    if app_settings.get('demo') == 'true':
        data = pc.get_demo_data()
        return {
            'statusCode': 200,
            'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
        }

    pc.get_employees()
    # generate the same single employee filename for active and terminated, depending on the termination date
    # the ingestion process will delete the records
    all_employees = pc.active_employee_ids + pc.terminated_employee_ids
    pc.get_employees_results(all_employees)

    employee_rows = []
    employee_ids = []

    for employee_id in all_employees:
        employee_details = pc.get_employee_details(employee_id)
        employee_row = pc.get_employee_row(employee_details, email_domain, employee_types)

        if not employee_row:
            print(f'Could not find employee_row for {employee_id}')
            continue
        employee_rows.append(employee_row)
        employee_ids.append(employee_id)

    df_all_employee_details = pd.DataFrame(employee_rows, columns=column_list, index=employee_ids)
    for employee_id, row in df_all_employee_details.iterrows():
        manager_id = row['MANAGER_ID']
        overrides = override_entries.get(employee_id, {})
        manager_fullname = ''
        manager_email = ''
        if manager_id and manager_id in df_all_employee_details.index:
            manager_details = df_all_employee_details.loc[manager_id]
            manager_fullname = '{}, {}'.format(manager_details['LAST_NAME'], manager_details['FIRST_NAME'])
            manager_email = manager_details['EMAIL']
        df_all_employee_details.loc[employee_id, 'MANAGER_FULLNAME'] = overrides.get(
            'MANAGER_FULLNAME') or manager_fullname
        df_all_employee_details.loc[employee_id, 'MANAGER_EMAIL'] = overrides.get('MANAGER_EMAIL') or manager_email
    employee_filename = pc.generate_csv(df_all_employee_details, csv_file_name)
    sftp_settings = app_settings.get('sftp_settings') or {}
    if sftp_settings:
        sftp = Sftp(
            sftp_settings['hostname'],
            sftp_settings['username'],
            sftp_settings['sftp_path'],
            sftp_settings['pub'],
            sftp_settings['private']
        )
        sftp(employee_filename)

    return {
        'statusCode': 200,
        'body': json.dumps({'data': 'Successfully completed', 'cache_ttl_seconds': 1800})
    }


def main():
    import pprint
    from pprint import pprint
    payload = {}

    with open(os.path.join(os.path.dirname(__file__), 'payload.json')) as f:
       payload = json.load(f)

    try:
        result = app_handler(payload, None)
        print(80 * '~')
        pprint(result)
    except:
        import traceback
        print(traceback.format_exc())


if __name__ == '__main__':
    main()
