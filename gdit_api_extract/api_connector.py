from datetime import datetime, timedelta
import csv
import glog as log
import gnupg
import time
import sys
import pytz
import requests

from constants import URLS, ACCESS_TOKEN_URLS, ACCESS_BASIC_TOKEN
from xml_util import *


class ApiConnector():
    def __init__(self, region, oauth_username, oauth_password):
        self.oauth_username = oauth_username
        self.oauth_password = oauth_password
        self.region = region
        self.retry_max_limit = 2
        self.sleep_timer = 5

        if oauth_username and oauth_password:
            self.oauth_data = {
                "grantType": "password",
                "username": self.oauth_username,
                "password": self.oauth_password
            }
            self.oauth_headers = {
                'Authorization': ACCESS_BASIC_TOKEN.get(self.region)
            }

            self.oauth_url = ACCESS_TOKEN_URLS.get(self.region)
            self.access_token = self.generate_access_token()

    def generate_access_token(self):
        retry_cnt = 0
        while retry_cnt <= self.retry_max_limit:
            try:
                log.info(f"Generating Access Token via API URL: {self.oauth_url}")
                response = requests.post(url=self.oauth_url, headers=self.oauth_headers, json=self.oauth_data)
                response.raise_for_status()

                if response and response.json().get('data', {}).get('access_token'):
                    access_token = response.json().get('data', {}).get('access_token')
                    log.info(f"Access token generated: {access_token}\n")
                    return access_token

            except Exception as err:
                log.info(f"API failed with msg: {err}\n")
                retry_cnt += 1
                wait = retry_cnt * self.sleep_timer
                log.info(f"Sleep for {wait} secs and go for retry attempt #{retry_cnt}...\n")
                time.sleep(wait)

        sys.exit(f"** Not able to generate access token. Retry max limit ({self.retry_max_limit}) reached, exiting app!! **\n")

    def get_api_call(self, url):
        retry_cnt = 0
        while retry_cnt <= self.retry_max_limit:
            try:
                headers = {
                    'Authorization': 'Bearer ' + self.access_token,
                    'accept': 'application/json'
                }
                log.info(f"Get API URL: {url}")
                response = requests.get(url=url, headers=headers)
                response.raise_for_status()
                return response.json()

            except Exception as err:
                log.info(f"API failed with msg: {err}\n")
                retry_cnt += 1
                wait = retry_cnt * self.sleep_timer
                log.info(f"Sleep for {wait} secs and go for retry attempt #{retry_cnt}...\n")
                time.sleep(wait)

                if retry_cnt == self.retry_max_limit:
                    log.info("Regenerating access token for last attempt...\n")
                    self.access_token = self.generate_access_token()

        log.info(f"Retry max limit ({self.retry_max_limit}) reached.\n")

    def get_field_data(self, entity_list, field):
        fields = {}
        for entity in entity_list:
            if entity.get(field):
                if entity.get('employeeInfo') and entity.get('employeeInfo').get('employeeId') and field in ["skills", "resume"]:
                    fields[entity.get('employeeInfo').get('employeeId')] = entity.get(field)
                elif entity.get('employeeId'):
                    fields[entity.get('employeeId')] = entity.get(field)
        return fields
    
    def remove_invalid_chars(self, string):
        chars_to_remove = ['\\', '\n', '\t', '\r', '"', '\u2022']
        for char in chars_to_remove:
            string = string.replace(char, '')
        return string

    def process_data(self, entity_field_data, field, field_list):
        data_rows = []
        for key, values in entity_field_data.items():
                if values is None:
                    continue
                if len(key) == 0:
                    continue
                if isinstance(values, str):
                    data_rows.append([key, values])
                else:
                    for value in values:
                        row = []
                        row.append(key)
                        for index in field_list[1:]:
                            if field=="certificates":
                                if index=='endDate':
                                    # Try endDate first, then validToDate as fallback
                                    date_value = value.get('endDate') or value.get('validToDate')
                                    if date_value:
                                        date = int(date_value)
                                        if date != 0:
                                            row.append(datetime.fromtimestamp(date, pytz.timezone("US/Eastern")).strftime('%m/%d/%Y'))
                                        else:
                                            row.append("")
                                    else:
                                        row.append("")
                                elif index=='startDate':
                                    # Try startDate first, then validFromDate as fallback
                                    date_value = value.get('startDate') or value.get('validFromDate')
                                    if date_value:
                                        date = int(date_value)
                                        if date != 0:
                                            row.append(datetime.fromtimestamp(date, pytz.timezone("US/Eastern")).strftime('%m/%d/%Y'))
                                        else:
                                            row.append("")
                                    else:
                                        row.append("")
                                elif index == 'title':
                                    row.append(self.remove_invalid_chars(value.get(index)))
                                elif index in field_list:
                                    row.append(value.get(index))
                            elif field=="education":
                                if index=='startTime' or index=="endTime":
                                    if value.get(index):
                                        date = int(value.get(index))
                                        if date != 0:
                                            row.append(datetime.fromtimestamp(date, pytz.timezone("US/Eastern")).strftime('%m/%d/%Y'))
                                    else:
                                        row.append("")
                                elif index=='school':
                                    row.append(self.remove_invalid_chars(value.get(index)))
                                elif index=='degree':
                                    row.append(self.remove_invalid_chars(value.get(index)))
                                elif index=='major':
                                    row.append(self.remove_invalid_chars(value.get(index)))
                                elif index in field_list:
                                    row.append(value.get(index))
                            else:
                                row.append(value.get(index))
                        data_rows.append(row)
        return data_rows

    def write_to_file(self, field, entity_field_data, result_filename_prefix, encryptipon_key, timestamp_format):
        field_name = ''        
        header = []
        field_list = []

        if field == "certificates":
            field_name = "CERTIFICATIONS"
            field_list = ['employeeId', 'title', 'certificateId', 'issuingAuthority', 'startDate', 'endDate']
            header = ['EMPLOYEE_ID', 'CERT_NAME', 'CERT_NUMBER', 'ISSUED_BY', 'ISSUE_DATE', 'EXPIRY_DATE']   
        if field == "education":
            field_name = "EDUCATION"
            field_list = ['employeeId', 'school', 'degree', 'major', 'startTime', 'endTime']
            header = ['EMPLOYEE_ID', 'SCHOOL', 'DEGREE', 'FIELD_OF_STUDY', 'FIRST_YR_ATTENDED', 'LAST_YR_ATTENDED']                 
        if field == "languages":
            field_name = "LANGUAGE"
            field_list = ['employeeId', 'language', 'overall']
            header = ['EMPLOYEE_ID', 'LANGUAGE', 'LANG_PROFICIENCY']
        if field == "skills":
            field_name = "SKILLS"
            field_list = ['id', 'displayName']
            header = ['EMPLOYEE_ID', 'SKILL_NAME']

        data_rows = []
        if entity_field_data:
            data_rows = self.process_data(entity_field_data, field, field_list)

        date = datetime.now().date().strftime(timestamp_format)
        local_path = result_filename_prefix + field_name + '_' + date + '.csv'

        with open(local_path, 'w') as f:
            writer = csv.writer(f, delimiter='^')
            writer.writerow(header)

            for single_row in data_rows:
                writer.writerow(single_row)

        if len(encryptipon_key):
            gpg = gnupg.GPG()
            import_result = gpg.import_keys(encryptipon_key)
            if import_result.count != 1:
                raise ValueError("Public Key import failed")
            key_id = import_result.fingerprints[0]
            key = gpg.list_keys().key_map[key_id]
            with open(local_path, 'rb') as f:
                local_path = local_path + ".pgp"
                status = gpg.encrypt_file(f, output=local_path, recipients="Eightfold_to_GDIT_PGPKeyPair", always_trust=True)
        
        return local_path


    def get_url(self, extract_type, field, region, start_ts):
        if extract_type == "full":
            if field == 'skills':
                return URLS.get("profile_" + region) + "?filterQuery=employees:*&limit=100&start="
            else:
                return URLS.get("employee_" + region) + "?limit=100&start="

        elif extract_type == "delta":
            if start_ts == "":
                dt = datetime.now() - timedelta(days=1)
                start_ts = dt.strftime('%s')

            if field == 'skills':
                return URLS.get("profile_" + region) + "?filterQuery=(employees:* AND lastModified:[" + start_ts + " TO *])&limit=100&start="
            else:
                return URLS.get("employee_" + region) + "?filterQuery=lastModified:([" + start_ts + " TO *])&limit=100&start="

        else:
            log.error("extract_type is not valid. Retry with one of: 'full' or 'delta'")
            exit()


    def get_data(self, field, region, start_ts, extract_type):
        base_url = self.get_url(extract_type, field, region, start_ts)
        log.info(f"URL: {base_url}")

        start = 0
        total_records = 1
        field_data = {}

        log.info(f"\nFetching data for Field: **{field.upper()}**\n")
        while start < 300:

            log.info(f"Processing records from {start + 1}")
            url = base_url + str(start)
            start += 100

            json_response = self.get_api_call(url=url)
            if not json_response:
                log.info("No response from API, moving ahead!!\n")
                continue

            meta_data = json_response.get('meta')
            total_records = int(meta_data.get('totalCount'))
            log.info(f"API response meta data: {meta_data}\n")

            json_data = json_response.get("data")
            if json_data:
                field_data.update(self.get_field_data(json_data, field))

        return field_data if field_data else None

