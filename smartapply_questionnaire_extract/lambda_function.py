#!/usr/bin/env python

import glog as log
import json
from pprint import pprint
import traceback
import requests
import time
import datetime
import os
import shutil
import tempfile
import csv

from constants import URLS, ACCESS_TOKEN_URLS, ACCESS_BASIC_TOKEN, QUESTION_LISTS
from constants import ConfiguredFrequecy, SupportedExporters
from transform import ResultXfrm
from transport import Sftp


class InputValidator:
    def __init__(self):
        return


def _errordict(**kwargs):
    return {
        'statusCode': kwargs['status_code'],
        'body': json.dumps({
            'error': kwargs['message'],
            'stacktrace': traceback.format_exc()
        })
    }


def _successdict(**kwargs):
    return {
        'statusCode': kwargs['status_code'],
        'body': json.dumps({
            'message': kwargs['message']
        })
    }


class ApiConnector():
    def __init__(self, region, oauth_username, oauth_password):
        self.oauth_username = oauth_username
        self.oauth_password = oauth_password
        self.region = region

        if oauth_username and oauth_password:
            self.data = {
                "grantType": "password",
                "username": self.oauth_username,
                "password": self.oauth_password
            }
            self.headers = {
                'Authorization': ACCESS_BASIC_TOKEN.get(self.region)
            }
            self.access_token = requests.post(ACCESS_TOKEN_URLS.get(self.region), json=self.data,
                                              headers=self.headers).json().get('data').get('access_token')
            log.info("Access Token: {}".format(self.access_token))

    def get_field_data(self, entity_list, field):
        fields = {}
        for entity in entity_list:
            if entity.get(field):
                fields[entity.get('email')] = entity.get(field)
        return fields

    def get_email_ids(self, entity_list):
        emails = []
        for entity in entity_list:
            emails.append(entity.get('email'))
        return emails

    def get_ats_position_id(self, positionId):
        log.info("Trying to get ATS position for position id: {}".format(positionId))
        url = "https://apiv2.eightfold.ai/api/v2/core/positions/" + str(positionId) + "?include=atsData"
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'accept': 'application/json'
        }

        resp = self.make_api_call(url, 'get', headers=headers)
        if not resp:
            log.info("No response from above API!!")
            return positionId

        json_response = resp.json()
        if json_response.get('atsData'):
            return json_response['atsData']['atsEntityId']

    def get_ats_entity_id_and_application_id(self, dupe_profile_ids, atsPositionId):
        atsEntityId, applicationId = '', ''

        for profile_id in dupe_profile_ids:
            log.info("Trying to get ATS data from dupe profile: {}".format(profile_id))
            url = "https://apiv2.eightfold.ai/api/v2/core/profiles/" + str(profile_id)
            headers = {
                'Authorization': 'Bearer ' + self.access_token,
                'accept': 'application/json'
            }

            resp = self.make_api_call(url, 'get', headers=headers)
            if not resp:
                log.info("No response from API!!")
                continue

            json_response = resp.json()
            if json_response.get('atsData'):
                atsEntityId = json_response['atsData']['candidateId']
                if json_response['atsData'].get('applications'):
                    for application in json_response['atsData']['applications']:
                        if atsPositionId == application['jobs'][0]['atsJobId']:
                            applicationId = application['applicationId']
                            return atsEntityId, applicationId

        return atsEntityId, applicationId

    def write_to_file(self, group_id, field, entity_field_data):
        local_path = group_id.split('.')[0] + '_candidates_' + field + '.csv'
        field_names = ['Profile_Id', 'ATS_Candidate_Id', 'First_Name', 'Last_Name', 'Email', 'ATS_Position_Id',
                       'Application_Id'] + QUESTION_LISTS

        with open(local_path, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()
            rows = []

            for profile in entity_field_data:

                for position in profile['careerSiteQuestions']:
                    positionId = position['positionIdList'][0]

                    # Fetch ats position id from Get Position API
                    atsPositionId = self.get_ats_position_id(positionId)
                    log.info("ATS position id found: {}".format(atsPositionId))

                    # Fetch ats entity id and application id from atsData field, if atsData available
                    atsData = profile.get('atsData')
                    if atsData:
                        atsEntityId = profile['atsData']['candidateId']
                        for application in profile['atsData']['applications']:
                            if atsPositionId == application['jobs'][0]['atsJobId']:
                                applicationId = application['applicationId']
                                break

                    # Fetch ats entity id and application id from GET Profile API with dupe profiles, if atsData not available
                    if not atsData and profile.get('dupeData') and profile['dupeData'].get('profile_ids'):
                        atsEntityId, applicationId = self.get_ats_entity_id_and_application_id(
                            profile['dupeData']['profile_ids'], atsPositionId)
                        log.info("ATS entity id found: {}".format(atsEntityId))
                        log.info("Application id found: {}".format(applicationId))

                    row = {'Profile_Id': profile.get('profileId'), 'ATS_Candidate_Id': atsEntityId, 'First_Name':
                        profile.get('firstName'), 'Last_Name': profile.get('lastName'), 'Email': profile.get('email'),
                           'ATS_Position_Id': atsPositionId, 'Application_Id': applicationId}

                    # add all question's answers to above row
                    for q in position['questions']['default']['answers']:
                        ques = q.get('question')

                        # modifying ques string as header compatible by replacing any non-alphabet chars with _
                        for i in ques:
                            if not i.isalpha():
                                ques = ques.replace(i, '_')

                        row[ques] = q.get('answer')[0]

                    rows.append(row)

            writer.writerows(rows)

        return local_path

    def make_api_call(self, url, api_type, headers, data=None):
        retry_cnt = 1
        retry_max_limit = 5

        while retry_cnt <= retry_max_limit:
            try:
                log.info("Calling API URL: {}".format(url))
                if api_type == 'get':
                    response = requests.get(url, headers=headers)
                elif api_type == 'post':
                    response = requests.post(url, headers=headers, json=data)

                response.raise_for_status()
                return response

            except Exception as err:
                log.info("API failed with msg: {}".format(err))
                wait = retry_cnt * 5
                log.info("Sleep for {} secs and go for retry attempt #{}...\n".format(wait, retry_cnt))
                time.sleep(wait)
                retry_cnt += 1

        log.info("Max limit ({}) reached for retry attempts.".format(retry_max_limit))

    def get_last_modified_ts(self, configured_frequency):
        current_time = datetime.datetime.now()
        if configured_frequency == 'WEEKLY':
            last_modified_ts = current_time - datetime.timedelta(days=7)
        elif configured_frequency == 'DAILY':
            last_modified_ts = current_time - datetime.timedelta(days=1)
        elif configured_frequency == 'HOURLY':
            last_modified_ts = current_time - datetime.timedelta(hours=1)

        log.info("Fetching Candidates from LAST_MODIFIED_TS: ** {} **".format(last_modified_ts))
        return last_modified_ts.strftime('%s')

    def get_data(self, entity, field, configured_frequency, region):
        last_modified_ts = self.get_last_modified_ts(configured_frequency)
        entity_region = entity + '_' + region
        base_url = URLS.get(entity_region) + '?filterQuery=lastModified:[' + last_modified_ts + ' TO *]&include=' + field

        log.info(f"Base URL: {base_url}")
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'accept': 'application/json'
        }

        start = 0
        entity_data = []
        total_records = 1
        log.info(f"Fetching data from Entity: ** {entity.upper()} ** and Field: ** {field.upper()} **\n")

        while start < total_records:
            log.info(f"Processing records from {start + 1} to {start + 100}")
            url = base_url + '&limit=100&start=' + str(start)
            start += 100

            resp = self.make_api_call(url=url, api_type='get', headers=headers)
            if not resp:
                log.info(f"No response from API!!\n")
                continue

            json_response = resp.json()
            json_data = json_response.get("data")
            meta_data = json_response.get('meta')
            total_records = int(meta_data.get('totalCount'))
            log.info(f"API response meta data: {meta_data}\n")

            for profile in json_data:
                if profile.get('careerSiteQuestions'):
                    log.info("Profile ID having careerSiteQuestions: {}".format(profile.get('profileId')))
                    entity_data.append(profile)

        log.info("** Total Candidates having careerSiteQuestions: {} **\n".format(len(entity_data)))
        return entity_data


def app_handler(event, context):
    app_settings = event.get('app_settings', {})
    trigger = event.get('trigger_name')
    log.info('Event: {}'.format(str(event)))
    log.info('Context: {}\n'.format(str(context)))
    group_id = event.get('group_id')
    oauth_username = app_settings.get('oauth_username')
    oauth_password = app_settings.get('oauth_password')
    region = app_settings.get('region')

    ef = ApiConnector(region, oauth_username, oauth_password)
    unconfigured_triggers = []
    result_xfrm = ResultXfrm(group_id)
    for config in app_settings['exporter_config']:
        configured_frequency = config['exporter_frequency']
        if configured_frequency == ConfiguredFrequecy.HOURLY.value and trigger != 'scheduled_hourly' or \
                configured_frequency == ConfiguredFrequecy.DAILY.value and trigger != 'scheduled_daily' or \
                configured_frequency == ConfiguredFrequecy.WEEKLY.value and trigger != 'scheduled_weekly':
            unconfigured_triggers.append({'configured_frequency': configured_frequency, 'triggered_frequency': trigger})
            continue
        entity = config.get('entity')
        field = config.get('field')
        result_filename_prefix = config.get('result_filename_prefix')
        for exporter in config['exporter']:
            if exporter not in [e.value for e in SupportedExporters]:
                return _errordict(status_code=500, message='Unknown exporter_type - {}'.format(exporter))

        entity_data = ef.get_data(entity, field, configured_frequency, region)

        log.info("Writing to file...")
        result_location = ef.write_to_file(group_id, field, entity_data)

        for transport in config['exporter']:
            if transport == SupportedExporters.SFTP.value:
                s3filename = result_location
                workdir = tempfile.mkdtemp()
                zip_filepath = ''
                metafilepath = None
                # Transform
                localfile = result_xfrm.result_prefix(
                    config.get('result_filename_prefix', '%G.%D.%S'),
                    config.get('result_files_seq_start', '0'),
                    config.get('timestamp_format', '%Y%m%d-%H%M%S'),
                    config.get('suffix', s3filename),
                    config.get('extension', 'csv')
                )
                log.info(f"local file name: {localfile}")
                filepath = os.path.join(workdir, localfile)
                shutil.copyfile(result_location, filepath)

                result_files = [filepath, metafilepath] if metafilepath else [filepath]
                log.info(f"result files: {result_files}")

                if config.get('zip'):
                    zip_prefix = config.get('result_zip_file_prefix')
                    zip_filename = os.path.splitext(zip_prefix + localfile)[0]
                    indir = os.path.dirname(filepath)
                    zip_filepath = result_xfrm.zipper(zip_filename, indir)
                    result_files.append(zip_filepath)
                    result_files.remove(filepath)
                    result_files.remove(metafilepath)

                sftp_path = config['sftp_path']
                Sftp(config['hostname'], config['username'], sftp_path, config['id_rsa.pub'],
                     config['id_rsa']).put(*result_files)
            if zip_filepath:
                shutil.rmtree(os.path.dirname(zip_filepath))
            shutil.rmtree(os.path.dirname(filepath))
    if len(unconfigured_triggers) == len(app_settings['exporter_config']):
        return _successdict(status_code=200,
                            message='Received unconfigured triggers (skipping): {}'.format(unconfigured_triggers))
    return _successdict(status_code=200, message='App invocation successful with {} trigger'.format(trigger))


def main():
    with open(os.path.join(os.path.dirname(__file__), 'payload.json')) as f:
        payload = json.load(f)

    result = app_handler(payload, None)
    print(80 * '~')
    pprint(result)


if __name__ == '__main__':
    main()
