'''
This file has the code to make API calls to Eightfold environment.
@author: Sadashiva K, Abel Robra- Arjuna LLC
'''
import datetime
import json

class Eightfold():

    def __init__(self, app_settings, req_data,app_sdk):
        self.headers = {"Authorization": app_settings.get("Authorization"),
                        "Accept": app_settings.get("Content-Type")}
        self.candidate_profile_url = "https://apiv2.eightfold.ai/api/v2/core/profiles"
        self.system_id = app_settings.get("system_id") #'bullhorn' # Setting this as default value, need to further check on finalized supported value.
        self.candidate_url_v2 = "https://apiv2.eightfold.ai/api/v2/core/ats-systems/{system_id}/ats-candidates".format(system_id=self.system_id)
        self.req_data = req_data
        self.position_url_v2 = "https://apiv2.eightfold.ai/api/v2/core/ats-systems/{system_id}/ats-positions".format(system_id=self.system_id)
        self.app_sdk = app_sdk

    def create_ef(self, ef_payload, entity, use_retry_with_exception=False):
        """
        Can update or Delete candidate in EF
        :param entity:
        :return:
        """
        if entity == 'Candidate':
            endpoint = self.candidate_url_v2

        if entity == 'Position':
            endpoint = self.position_url_v2
            
        response = None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries('POST', url=endpoint, headers=self.headers, json=ef_payload)            
        else:
            response = self.app_sdk.call_http_method('POST', url=endpoint, headers=self.headers, json=ef_payload)
        res_data = json.loads(response.content)
        return res_data


    def update_ef(self, ef_payload, entity, ats_entity_id):
        """
        Update ATS Candidate Information
        :param bh_payload: BH payload
        :param entity: entity type - Candidate/ JobOrder
        :param ats_entity_id: BH Candidate ID
        :return:
        """
        if entity == 'Candidate':
            endpoint = self.candidate_url_v2 + "/" + str(ats_entity_id)
        if entity == 'Position':
            endpoint = self.position_url_v2 + "/" + str(ats_entity_id)
        response = self.app_sdk.call_http_method('PATCH', url=endpoint, headers=self.headers, json=ef_payload)
        res_data = json.loads(response.content)
        return res_data

    def update_ats_ef(self, bh_payload, entity, ats_entity_id):
        """
        Update ATS Candidate Information
        :param bh_payload: BH payload
        :param entity: entity type - Candidate/ JobOrder
        :param ats_entity_id: BH Candidate ID
        :return:
        """
        if entity == 'Candidate':
            endpoint = self.candidate_url_v2 + "/" + str(ats_entity_id)
            if "lastActivityTs" not in bh_payload or not bh_payload.get("lastActivityTs"):
                curr_dt = datetime.datetime.now()
                last_ts = int(round(curr_dt.timestamp()))
                bh_payload["lastActivityTs"] = last_ts
        if entity == 'Position':
            endpoint = self.position_url_v2 + "/" + str(ats_entity_id)
        response = self.app_sdk.call_http_method('PUT', url=endpoint, headers=self.headers, json=bh_payload)
        res_data = json.loads(response.content)
        return res_data

    def update_ef_profile(self, profile_id, candidate_payload, use_retry_with_exception=False):
        """
        Make EF Profile Patch API call to update the CustomInfo section with Bullhorn Candidate ID
        :param profile_id: EF Candidate Profile ID
        :param candidate_payload: Candidate Payload mainly containing CustomInfo Data
        :return: response from Profile Path API call
        """
        endpoint = f"{self.candidate_profile_url}/{profile_id}"
        response = None
        if response:
            response = self.app_sdk.call_http_method_with_retries('PATCH', url=endpoint, headers=self.headers, json=candidate_payload)
        else:
            response = self.app_sdk.call_http_method('PATCH', url=endpoint, headers=self.headers, json=candidate_payload)
        
        res_data = json.loads(response.content)
        return res_data

    def delete_ef(self, entity, profile_id=None):
        """
        Delete every entities in EF based on the entity ID provided in request data
        :param req_data:
        :return:
        """
        if entity == 'Candidate':
            if not profile_id:
                profile_id = self.req_data.get("profile_id")
            endpoint = self.candidate_profile_url + "/" + str(profile_id)
            response = self.app_sdk.call_http_method('DELETE', url=endpoint, headers=self.headers)
            res_data = json.loads(response.content)
            return res_data

    def get_ef_data_candidate_profile(self, profile_id, use_retry_with_exception=False):
        """
        Make EF Get Profile API Call to pull candidate data.
        :param profile_id:
        :return:
        """
        url = self.candidate_profile_url + "/" + str(profile_id)
        params = {
            "include": "resume,tags,applications,notes"
        }
        response = None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries('GET', url=url, headers=self.headers,params=params)
        else:
            response = self.app_sdk.call_http_method('GET', url=url, headers=self.headers,params=params)
        res_data = json.loads(response.content)
        return res_data

    def get_ats_candidate(self, bh_id, use_retry_with_exception=False):
        """
        Make EF GET ATS Candidate API call to pull ATS candidate information
        :param bh_id: Bullhorn Candidate ID
        :return: Payload from EF GET ATS Candidate API call
        """
        try:
            ats_url = self.candidate_url_v2 + f"/{bh_id}"
            params = {
                "include": "resume,applications,notes"
            }
            response = None
            if use_retry_with_exception:
                response = self.app_sdk.call_http_method_with_retries('GET', url=ats_url, headers=self.headers, params=params)
            else:
                response = self.app_sdk.call_http_method('GET', url=ats_url, headers=self.headers, params=params)
            res_data = json.loads(response.content)
            if res_data and "message" not in res_data:
                return res_data
        except Exception as ex:
            if str(ex).find('status_code: 404') !=-1: # ie not found in EF 
                return None
            raise ex # any other case
