'''
This file has the code to make API calls to BullHorn environment.
'''
import time
import json
from urllib import parse
import base64
import traceback
from country_ids import COUNTRY_IDS as country_ids
from candidate_mapping import ef_to_bh_candidate
from position_job_order_mapping import ef_to_bh_position, bh_to_ef_position

event_types = 'INSERTED,UPDATED,DELETED'
entity_names = 'Candidate,CandidateEducation,CandidateWorkHistory,JobOrder,JobSubmission'
candidate_url = "https://api.eightfold.ai/v1/candidate"


class BullHorn():
    """
    This class handles all the assessment details of a candidate,
    get interviews data, create interviews, upload resume etc.
    """

    def __init__(self, app_settings, app_sdk):
        """
        Initialize the class with given app settings
        :param app_settings: App configuration that is set during EF installation
        """
        self.client_id = app_settings.get("client_id")
        self.client_secret = app_settings.get("client_secret")
        self.username = app_settings.get("username")
        self.password = app_settings.get("password")
        self.refresh_token = app_settings.get("refresh_token")
        self.redirect_uri = app_settings.get("redirect_uri")
        self.bh_rest_token = ""
        self.headers = {"BhRestToken": self.bh_rest_token}
        self.rest_url = ""
        self.auth_domain = app_settings.get("auth_domain")
        self.auth_url = "https://{auth_domain}.bullhornstaffing.com/oauth/".format(auth_domain=self.auth_domain)
        self.rest_domain = self.auth_domain.replace("auth", "rest")
        self.rest_login_url = "https://{rest_domain}.bullhornstaffing.com/rest-services/login".format(rest_domain=self.rest_domain)
        self.app_sdk = app_sdk
        self.subscription_id = app_settings.get("subscription_id")
        # self.req_data = req_data

    def setup(self):
        """
        Setup the webhook to listen the realtime updates from Client/ HV system
        :param req_data: payload containing ef settings
        :return: response object with webhook setup status
        """
        if self.refresh_token:
            tokens = self.generate_new_token()
        else:
            print("Ask auth code")
            auth_code = self.generate_auth_code()
            print("Generate token")
            tokens = self.generate_token(auth_code)
        access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]
        print("Generate REST token")
        try:
            self.generate_rest_token_url(access_token)
        except Exception as ex:
            traceback.print_exc()
            time.sleep(5)
            auth_code = self.generate_auth_code()
            tokens = self.generate_token(auth_code)
            access_token = tokens["access_token"]
            self.generate_rest_token_url(access_token)
        return

    def generate_auth_code(self):
        """
        Generate Authorization code for BH APIs
        :return: Authorization code
        """
        auth_code_url = self.auth_url + "authorize"
        auth_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "action": "Login",
            "username": self.username,
            "password": self.password,
            "redirect_uri": self.redirect_uri
        }
        response = self.app_sdk.call_http_method("POST", url=auth_code_url, params=auth_params, allow_redirects=False)
        cache_key = response.headers["Location"].split("code=")[1]
        auth_code = cache_key.split("&")[0]
        print("Authorization Code", auth_code)
        return auth_code

    def generate_token(self, auth_code):
        """
        Generate Bullhorn Token
        :param auth_code: Authorization code needed to generate BhRestToken
        :return: Bullhorn Rest API Token
        """
        token_url = self.auth_url + "token"
        token_params = {
            "grant_type": "authorization_code",
            "code": parse.unquote(auth_code),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }
        response = self.app_sdk.call_http_method("POST", url=token_url, params=token_params)
        tokens = json.loads(response.content)
        return tokens

    def generate_new_token(self):
        """
        Generate a new Bullhorn Rest API Token based on refresh token
        :return: Bullhorn Rest API Token
        """
        token_url = self.auth_url + "token"
        token_params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            # "redirect_uri": self.redirect_uri
        }
        response = self.app_sdk.call_http_method("POST", url=token_url, params=token_params)
        tokens = json.loads(response.content)
        return tokens

    def generate_rest_token_url(self, access_token):
        """
        Generate Rest Token URL
        :param access_token: Access Token needed to generate Rest Token URL
        :return:
        """
        try:
            params = {
                "version": "*",
                "access_token": access_token
            }
            response = self.app_sdk.call_http_method("POST", url=self.rest_login_url, params=params)
            resp_data = json.loads(response.content)
        except Exception as ex:
            print(ex)
            retry_count = 0
            bh_token_generated = False
            while retry_count < 10:
                try:
                    auth_code = self.generate_auth_code()
                    tokens = self.generate_token(auth_code)
                    access_token = tokens["access_token"]
                    params = {
                        "version": "*",
                        "access_token": access_token
                    }
                    response = self.app_sdk.call_http_method("POST", url=self.rest_login_url, params=params)
                    resp_data = json.loads(response.content)
                    bh_token_generated = True
                except Exception as ex:
                    print("Failed to generate BH access token with exception message: {}. Retry count: {}".format(str(ex), retry_count))
                    time.sleep(1)
                    if retry_count == 9:
                        raise ex
                if bh_token_generated:
                    break
                else:
                    retry_count+=1

        self.bh_rest_token = resp_data["BhRestToken"]
        self.rest_url = resp_data["restUrl"]
        self.headers = {"BhRestToken": self.bh_rest_token}
        print("BH Rest Token -", self.bh_rest_token)
        print("Rest URL -", self.rest_url)
        return

    def create_association(self, entity_name, entity_id, sub_entity_name, data):
        data_ids = ",".join(data)
        response = self.app_sdk.call_http_method("PUT",
                                       url=self.rest_url + "entity/{entity_name}/{entity_id}/{sub_entity_name}/{data_ids}".format(
                                           entity_name=entity_name, entity_id=entity_id,
                                           sub_entity_name=sub_entity_name, data_ids=data_ids, headers=self.headers))
        res_data = json.loads(response.content) if response.content else ''
        return res_data

    def delete_entity(self, entity, id, use_retry_with_exception=False):
        """
        Delete an entity in Bullhorn
        :param entity: entity type
        :param id: Bullhorn Entity ID
        :return:
        """
        response = None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries("DELETE",
                                       url=self.rest_url + "entity/{entityname}/{entityid}".format(entityname=entity,
                                                                                                   entityid=id),
                                       headers=self.headers)
        else:
            response = self.app_sdk.call_http_method("DELETE",
                                       url=self.rest_url + "entity/{entityname}/{entityid}".format(entityname=entity,
                                                                                                   entityid=id),
                                       headers=self.headers)
        res_data = json.loads(response.content) if response.content else ''
        return res_data

    def create_entity(self, entity, data, use_retry_with_exception=False):
        """
        API Call to create an entity in BH
        :param entity: entity name such as Candidate/ CandidateEducation/ JobOrder
        :param data: payload containing the candidate information
        :return: api call response
        """
        try:
            params = json.dumps(data)
            response = None
            if use_retry_with_exception:
                if entity == "Candidate":
                    # in case of candidate create, there were cases where 500 error code was thrown by BH but the candidate was actually created, hence exluding 500 for retry.
                    response = self.app_sdk.call_http_method_with_retries("PUT", url=self.rest_url + "entity/{entityname}".format(entityname=entity),
                                           data=params, headers=self.headers, exclude_500_retry=True)
                else:
                    response = self.app_sdk.call_http_method_with_retries("PUT", url=self.rest_url + "entity/{entityname}".format(entityname=entity),
                                            data=params, headers=self.headers)
            else:
                response = self.app_sdk.call_http_method("PUT", url=self.rest_url + "entity/{entityname}".format(entityname=entity),
                                            data=params, headers=self.headers)
            res_data = response.content
            if res_data:
                return json.loads(res_data)
        except Exception as ex:
            traceback.print_exc()
            print("Exception in creating entity", str(ex))
            return None

    def update_entity(self, entity, data, use_retry_with_exception=False):
        """
        Update BH Entity
        :param entity: Entity Name of interest
        :param data: Payload that need to be added to entity
        :return: BH API response
        """
        params = json.dumps(data)
        endpoint = "{url}entity/{entityname}/{id}".format(url=self.rest_url, entityname=entity, id=data["id"])
        response=None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries("POST", url=endpoint, data=params, headers=self.headers)
        else:
            response = self.app_sdk.call_http_method("POST", url=endpoint, data=params, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def event_subscription(self):
        """
        Call BH system and create a subscription
        :return:
        """
        subscription_url = self.rest_url + "event/subscription/{subscriptionId}".format(subscriptionId=self.subscription_id)
        params = {
            "type": "entity",
            "names": entity_names,
            "eventTypes": event_types,
            "BhRestToken": self.bh_rest_token
        }
        response = self.app_sdk.call_http_method("PUT", url=subscription_url, params=parse.urlencode(params, safe=","))
        return

    def delete_subscription(self):
        """
        Call BH System to delete an existing subscription
        :return:
        """
        subscription_url = self.rest_url + "event/subscription/{subscriptionId}".format(subscriptionId=self.subscription_id)
        params = {
            "BhRestToken": self.bh_rest_token
        }
        response = self.app_sdk.call_http_method("DELETE", url=subscription_url, params=parse.urlencode(params, safe=","))
        return

    def get_events_update(self):
        subscription_url = self.rest_url + "event/subscription/{subscriptionId}".format(subscriptionId=self.subscription_id)
        params = {
            "maxEvents": 1000
        }
        response = self.app_sdk.call_http_method_with_retries("GET", url=subscription_url, headers=self.headers, params=params)
        event_updates = None
        if response.text != '':
            event_updates = json.loads(response.text)
        return event_updates

    def get_entity_data(self, entity_type, entity_id, field_list="id", use_retry_with_exception=False):
        """
        Get th entity information from BH system
        :param entity_type: Type of entity - Candidate/ JobOrder etc
        :param entity_id: BH entity id
        :param field_list: comma separated list of params that are needed in response
        :return: entity data from BH
        """
        subscription_url = self.rest_url + "entity/{entityType}/{entityId}?fields={fieldList}".format(
            entityType=entity_type, entityId=entity_id, fieldList=field_list)
        response = None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries("GET", url=subscription_url, headers=self.headers)
        else:
            response = self.app_sdk.call_http_method("GET", url=subscription_url, headers=self.headers)
        res_data = response.content
        if res_data:
            json_data = json.loads(res_data)
            return json_data

    def get_all_candidate_notes(self, entity_type, entity_id, field_list="comments"):
        """
        Get all notes of an entity from BH
        :param entity_type: entity type
        :param entity_id:  BH entity Id
        :param field_list: fields that are needed in response
        :return:
        """
        query_url = self.rest_url + f"search/{entity_type}?query=id:{entity_id}&fields=notes({field_list})&count=198"
        response = self.app_sdk.call_http_method("GET", url=query_url, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def get_all_note_entity(self, entity_id):
        query_url = self.rest_url + f"query/NoteEntity?where=targetEntityID={entity_id}&fields=note&count=500"
        response = self.app_sdk.call_http_method("GET", url=query_url, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def get_all_notes(self):
        clientCorpId = 4
        notes_url = self.rest_url + "allCorpNotes?clientCorpId={clientCorpId}&fields=start=0&count=5".format(
            clientCorpId=clientCorpId)

        response = self.app_sdk.call_http_method("GET", url=notes_url, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def get_entity_notes(self, id, entity_type="Candidate"):
        # Can you additional filters like - &start=0&sort=id&count=100
        notes_url = self.rest_url + "search/{entity_type}?query=id:{id}&fields=notes(id,comments,isDeleted)&showTotalMatched=True".format(
            entity_type=entity_type, id=id)

        response = self.app_sdk.call_http_method("GET", url=notes_url, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def get_job_query_data(self, id, entity_name, fields, where="", count=500):
        """
        Search BH for list of entities with id and additional conditions.
        :param id: entity id in BH
        :param entity_name: entity type in BH
        :param fields: params that are expected in the api response
        :param where: additional filters
        :param count: limitation on the number of records returned in response.
        :return: query results from BH
        """
        query_url = self.rest_url + f"search/{entity_name}?query=candidate.id:{id} AND isDeleted:0&fields={fields}&count={count}"
        response = self.app_sdk.call_http_method("GET", url=query_url, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)


    def search_entity(self, entity_type="Candidate", search="name in ('javascript','mysql')", fields="id", count=500, use_retry_with_exception=False):
        """
        API call to search entity information in BH
        :param entity_type: type of entity - Candidate/ JobOrder
        :param search: search params - ex: BH entity ids
        :param fields: fields that are expected in the api response
        :param count: limit of records that are expected in api repsonse
        :return:
        """
        url = self.rest_url + "query/{entity_type}?where={search}&fields={fields}&count={count}".format(entity_type=entity_type,
                                                                                          search=search, fields=fields, count=count)
        print("Search URL " + url)
        response = None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries("GET", url=url, headers=self.headers)
        else:
            response = self.app_sdk.call_http_method("GET", url=url, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def search_entity_post(self, entity_type="Candidate", search="name in ('javascript','mysql')", fields="id", count=500, use_retry_with_exception=False):
        url = self.rest_url + "search/{entity_type}?fields={fields}&count={count}".format(entity_type=entity_type, fields=fields, count=count)
        print("Search URL " + url)
        response = None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries("POST", url=url, json=search, headers=self.headers)
        else:
            response = self.app_sdk.call_http_method("POST", url=url, json=search, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def query_entity_post(self, entity_type="Candidate", search="name in ('javascript','mysql')", fields="id", count=500, use_retry_with_exception=False):
        url = self.rest_url + "query/{entity_type}?fields={fields}&count={count}".format(entity_type=entity_type, fields=fields, count=count)
        print("Search URL " + url)
        
        response = None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries("POST", url=url, json=search, headers=self.headers)
        else:
            response = self.app_sdk.call_http_method("POST", url=url, json=search, headers=self.headers)
        
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def get_entity_files(self, entity_type, entity_id):
        field_list = "id,type,fileExtension"
        subscription_url = self.rest_url + "entity/{entityType}/{entityId}/fileAttachments?fields={fieldList}".format(
            entityType=entity_type, entityId=entity_id, fieldList=field_list)

        response = self.app_sdk.call_http_method("GET", url=subscription_url, headers=self.headers)
        res_data = response.content
        if res_data:
            file_list = json.loads(res_data)
            if file_list and file_list['data']:
                for file_rec in file_list['data']:
                    if file_rec['type'] == "Resume":
                        file_id = file_rec['id']
                        file_extension = file_rec['fileExtension'] if file_rec['fileExtension'] else ".txt"
                        file_name = str(file_id) + file_extension
                        raw_file_url = self.rest_url + "file/{entityType}/{entityId}/{fileId}/raw".format(
                            entityType=entity_type, entityId=entity_id, fieldList=field_list, fileId=file_id)
                        response_file = self.app_sdk.call_http_method("GET", url=raw_file_url, headers=self.headers)
                        file_type = file_rec.get('type', 'Sample')
                        complete_file_name = file_type + "-" + file_name if file_type else file_name
                        with open(complete_file_name, 'wb') as f:
                            f.write(response_file.content)
                        return complete_file_name

    def get_resume_file_names(self, entity_type, entity_id, use_retry_with_exception=False):
        field_list = "name"
        file_names = list()
        subscription_url = self.rest_url + "entity/{entityType}/{entityId}/fileAttachments?fields={fieldList}".format(
            entityType=entity_type, entityId=entity_id, fieldList=field_list)
        print(subscription_url)
        response = None
        if use_retry_with_exception:
            response = self.app_sdk.call_http_method_with_retries("GET", url=subscription_url, headers=self.headers)
        else:
            response = self.app_sdk.call_http_method("GET", url=subscription_url, headers=self.headers)
        res_data = response.content
        if res_data:
            file_list = json.loads(res_data)
            if file_list and file_list['data']:
                file_names = [file['name'] for file in file_list['data']]
                
        return file_names


    def get_resume_file_id(self, entity_type, entity_id):
        """
        Get resume entity id of a candidate from BH.
        :param entity_type: Parent entity time - Candidate here
        :param entity_id: Bullhorn entity id of the candidate
        :return: CandidateFileAttachment BH entity Id
        """
        field_list = "id,type"
        subscription_url = self.rest_url + "entity/{entityType}/{entityId}/fileAttachments?fields={fieldList}".format(
            entityType=entity_type, entityId=entity_id, fieldList=field_list)
        print(subscription_url)
        response = self.app_sdk.call_http_method("GET", url=subscription_url, headers=self.headers)
        res_data = response.content
        if res_data:
            file_list = json.loads(res_data)
            if file_list and file_list['data']:
                for file_rec in file_list['data']:
                    if file_rec['type'] == "Resume" or file_rec['type'] == "Client Resume":
                        file_id = file_rec['id']
                        return file_id

    def get_resume_raw_data(self, entity_type, entity_id, resume_id):
        """
        Get base64 code of resume file, by querying BH with resume entity Id
        :param entity_type: Parent entity type of file attachment - Candidate here
        :param entity_id: BH Candidate Id
        :param resume_id: Resume ID of candidate in BH
        :return: base64 code of resume data
        """
        # Try using optional param for -raw for multipart encoded data- file/{entityType}/{entityId}/{fileId}(/raw)
        resume_url = self.rest_url + "file/{entityType}/{entityId}/{fileId}".format(entityType=entity_type,
                                                                                    entityId=entity_id,
                                                                                    fileId=resume_id)
        response = self.app_sdk.call_http_method("GET", url=resume_url, headers=self.headers)
        res_data = json.loads(response.content)
        base64_code = res_data['File']["fileContent"]
        extension = res_data['File']["name"].split(".")[-1]
        return base64_code, extension

    def attach_files_entity(self, entity_type, entity_id, file_name, use_retry_with_exception=False):
        file_upload_url = self.rest_url + "file/{entityType}/{entityId}/raw?filetype=SAMPLE&externalID=portfolio".format(
            entityType=entity_type, entityId=entity_id)
        files = {'files': open(file_name, 'rb')}
        resp = None
        if use_retry_with_exception:
            resp = self.app_sdk.call_http_method_with_retries("PUT", url=file_upload_url, files=files, headers=self.headers)
        else:
            resp = self.app_sdk.call_http_method("PUT", url=file_upload_url, files=files, headers=self.headers)

    def attach_resume_file_entity(self, entity_type, entity_id, file_name):
        file_upload_url = self.rest_url + "file/{entityType}/{entityId}".format(entityType=entity_type,
                                                                                entityId=entity_id)
        with open(file_name, "rb") as fi:
            content = fi.read()
        file_content = base64.b64encode(content)
        headers = {**self.headers, **{"Content-Type": "application/json"}}
        import mimetypes
        content_type = mimetypes.guess_type(file_name)[0]
        # content_type = "text/plain"
        params = {"externalID": "portfolio",
                  "fileContent": str(file_content)[2:-1],
                  "fileType": "SAMPLE", "name": file_name, "contentType": content_type,
                  "description": "Resume file for candidate.", "type": "cover"}
        resp = self.app_sdk.call_http_method("PUT", url=file_upload_url, params=params, headers=headers)

    def attach_raw_resume_file_entity(self, entity_type, entity_id, raw_file_content, file_name):
        file_upload_url = self.rest_url + "file/{entityType}/{entityId}".format(entityType=entity_type,
                                                                                entityId=entity_id)
        headers = {**self.headers, **{"Content-Type": "application/json"}}
        params = {"externalID": "portfolio",
                  "fileContent": str(raw_file_content)[2:-1] if raw_file_content[0] == "b'" else str(raw_file_content),
                  "fileType": "SAMPLE", "name": file_name,  # "contentType": content_type,
                  "description": "Resume file for candidate.", "type": "cover"}
        resp = self.app_sdk.call_http_method("PUT", url=file_upload_url, params=params, headers=headers)

    def get_entity_meta(self, entity_type):
        field_list = "id"
        subscription_url = self.rest_url + "meta/{entityType}?fields={fieldList}".format(
            entityType=entity_type, fieldList=field_list)

        response = self.app_sdk.call_http_method("GET", url=subscription_url, headers=self.headers)
        res_data = response.content
        if res_data:
            return json.loads(res_data)

    def map_fields(self, entity, bh_data):
        """
        Map fields between BH and EF and create a payload for EF
        :param entity:  Entity type in BH
        :param bh_data: Bullhorn Entity data
        :return: payload that can be used with EF api calls
        """
        ef_entity = dict()
        if entity == 'Candidate':
            data_dict = ef_to_bh_candidate
        elif entity == "JobOrder":
            data_dict = ef_to_bh_position
            # Mandatory field
            ef_entity["recruiter"] = dict()
            ef_entity["recruiter"]["name"] = bh_data["owner"]["firstName"] + " " + bh_data["owner"]["lastName"]
            address = bh_data["address"]
            if address:
                if address["address1"] and address["city"]:
                    location = address["address1"] + " " + address["city"]
                    ef_entity["locations"] = [location]
            if 'owner' in bh_data:
                owner_first_name = bh_data["owner"].get("firstName", False)
                if owner_first_name:
                    ef_entity["hiringManager"] = dict()
                    ef_entity["hiringManager"]["name"] = bh_data["owner"]["firstName"]
                    try:
                        client_contact = self.get_entity_data('CorporateUser', bh_data["owner"]["id"], "email")
                        ef_entity["hiringManager"]["email"] = client_contact["data"]["email"]
                    except Exception as ex:
                        print(str(ex))
        
        for ef_key, bh_key in data_dict.items():
            if bh_key and bh_key.find(".") != -1:
                data_keys = bh_key.split(".")
                ef_entity[ef_key] = bh_data.get(data_keys[0]).get(data_keys[1]) if bh_data.get(data_keys[0]) else ""
            else:
                if bh_data.get(bh_key):
                    ef_entity[ef_key] = bh_data.get(bh_key, "")

        return ef_entity

    def map_job_order_fields(self, ef_data):
        result_data = dict()
        for bh_key, ef_key in bh_to_ef_position.items():
            data_val = ef_data.get(ef_key, "")
            if data_val:
                result_data[bh_key] = data_val

        return result_data

    def process_education_data(self, education, candidate_info):
        """
        Process education data from EF and prepare payload to write this data to BH
        :param education: education data list from EF
        :param candidate_info: contains the BH Candidate ID
        :return: education list data that can be written to BH
        """
        education_list = []
        for each_education in education:
            education_dict = dict()
            education_dict["degree"] = each_education["degree"]
            education_dict["school"] = each_education["school"]    
            education_dict["major"] = each_education["major"]
            education_dict["comments"] = each_education["description"]
            education_dict["candidate"] = candidate_info

            if 'startTime' in each_education.keys():
                if type(each_education["startTime"]) == str:
                    if "." in each_education["startTime"]:
                        each_education["startTime"] = each_education["startTime"].split(".")[0]
                        
                    if "." in each_education["endTime"]:
                        each_education["endTime"] = each_education["endTime"].split(".")[0]
                    
                    each_education["startTime"] = int(each_education["startTime"])
                    each_education["endTime"] = int(each_education["endTime"])
                education_dict["startDate"] = each_education["startTime"] * 1000 if each_education["startTime"] else 0
                education_dict["endDate"] = each_education["endTime"] * 1000 if each_education["endTime"] else 0
            elif 'startTs' in each_education.keys():
                if type(each_education["startTs"]) == str:
                    if "." in each_education["startTs"]:
                        each_education["startTs"] = each_education["startTs"].split(".")[0]
                        
                    if "." in each_education["endTs"]:
                        each_education["endTs"] = each_education["endTs"].split(".")[0]
                    
                    each_education["startTs"] = int(each_education["startTs"])
                    each_education["endTs"] = int(each_education["endTs"])
                education_dict["startDate"] = each_education["startTs"] * 1000 if each_education["startTs"] else 0
                education_dict["endDate"] = each_education["endTs"] * 1000 if each_education["endTs"] else 0
            else:
                education_dict["startDate"] = 0
                education_dict["endDate"] = 0
            education_dict["graduationDate"] = education_dict["endDate"]
            education_list.append(education_dict)

        return education_list

    def create_education_data(self, education_list):
        """
        Create BH CandidateEducation entity in BH
        :param education_list: list of education records that need to be created in BH
        :return: Ids of newly created CandidateEducatin entities
        """
        education_ids = list()
        for education_dict in education_list:
            resp_data = self.create_entity("CandidateEducation", education_dict, use_retry_with_exception=True)
            if resp_data:
                education_id = resp_data["changedEntityId"]
                education_ids.append(str(education_id))
        return education_ids

    def process_experience_data(self, experience, candidate_info):
        """
        Process experience records from Eightfold and re-structure the records to add them as WorkHistories in BH
        :param experience: list of candidate experiences in EF
        :param candidate_info: BH ATS Candidate ID
        :return: list of candidate experiences which can be added to BH
        """
        work_list = list()
        for each_work in experience:
            work_history_dict = dict()
            work_history_dict["title"] = each_work["title"]
            work_history_dict["candidate"] = candidate_info
            work_history_dict["comments"] = each_work["description"]
            if "company" in each_work:
                work_history_dict["companyName"] = each_work["company"] if each_work[
                    "company"] else 'Not specified'
            else:
                work_history_dict["companyName"] = each_work["work"] if each_work[
                    "work"] else 'Not specified'

            if 'startTs' in each_work:
                if type(each_work["startTs"]) == str:
                    if "." in each_work["startTs"]:
                        each_work["startTs"] = each_work["startTs"].split(".")[0]
                        
                    if "." in each_work["endTs"]:
                        each_work["endTs"] = each_work["endTs"].split(".")[0]
                    
                    each_work["startTs"] = int(each_work["startTs"])
                    each_work["endTs"] = int(each_work["endTs"])
                work_history_dict["startDate"] = each_work["startTs"] * 1000 if each_work["startTs"]  else 0
                work_history_dict["endDate"] = each_work["endTs"] * 1000 if each_work["endTs"] else 0
            elif 'startTime' in each_work:
                if type(each_work["startTime"]) == str:
                    if "." in each_work["startTime"]:
                        each_work["startTime"] = each_work["startTime"].split(".")[0]
                        
                    if "." in each_work["endTime"]:
                        each_work["endTime"] = each_work["endTime"].split(".")[0]
                    
                    each_work["startTime"] = int(each_work["startTime"])
                    each_work["endTime"] = int(each_work["endTime"])
                work_history_dict["startDate"] = each_work["startTime"] * 1000 if each_work["startTime"] else 0
                work_history_dict["endDate"] = each_work["endTime"] * 1000 if each_work["endTime"] else 0
            else:
                work_history_dict["startDate"] = 0
                work_history_dict["endDate"] = 0
                
            work_list.append(work_history_dict)

        return work_list

    def create_experience_data(self, work_data):
        """
        Create CandidateWorkHistory entity in BH
        :param work_data: list of experiences of a candidate
        :return: list of candidateWorkHistory ids, that are created in BH
        """
        work_list = []
        for work_history_dict in work_data:
            resp_data = self.create_entity("CandidateWorkHistory", work_history_dict, use_retry_with_exception=True)
            if resp_data:
                work_id = resp_data["changedEntityId"]
                work_list.append(str(work_id))
        return work_list

    def process_notes_data(self, notes_info, candidate_info):
        """
        Process notes data from EF and create new notes list that can be directly added to Bullhorn
        :param notes_info: Notes list from EF
        :param candidate_info: Bullhorn Candidate Id
        :return: Notes list that can be directly used to create Notes entities
        """
        notes_list = list()
        for note in notes_info:
            note_dict = dict()
            note_dict["dateAdded"] = note["createdTime"] * 1000
            note_dict["comments"] = note["note"]
            note_dict["candidates"] = [candidate_info]
            note_dict["action"] = note["noteType"]
            note_dict[
                "personReference"] = candidate_info
            sender_email = note.get("sender")
            if sender_email and str(sender_email).find("@"):
                corp_user = self.search_entity(entity_type="CorporateUser",
                              search=f"externalEmail='{sender_email}' OR email='{sender_email}'")
                if len(corp_user['data']) > 0:
                    note_dict["commentingPerson"] = {
                        "id": corp_user['data'][0]['id']
                    }
            elif sender_email:
                corp_user = self.search_entity(entity_type="CorporateUser",
                                               search=f"firstName='{sender_email}'")
                if len(corp_user['data']) > 0:
                    note_dict["commentingPerson"] = {
                        "id": corp_user['data'][0]['id']
                    }
            notes_list.append(note_dict)
        return notes_list

    def create_notes_data(self, notes_info_list):
        """
        Create Note entity for each of the notes list
        :param notes_info_list: notes list that need to be created in BH
        :return: list of notes ids that are created in BH
        """
        notes_list = list()
        for note_dict in notes_info_list:
            resp_data = self.create_entity("Note", note_dict, use_retry_with_exception=True)
            if resp_data:
                note_id = resp_data["changedEntityId"]
                notes_list.append(note_id)
        return notes_list


    def process_req_payload_application_data(self, req_payload, candidate_info):
        """
        Get application data from request payload and create a new payload that can be used to create JobSubmission in BH
        :param req_payload: input request payload to the trigger
        :param candidate_info: Contains Bullhorn Candidate I
        :return: new payload that can be used for creating JobSubmission in BH
        """
        application_dict = dict()
        app_id = req_payload.get("applicationId")
        if app_id and str(app_id).startswith("vs-"):
            application_dict["customText1"] = req_payload["applicationId"]
        application_dict["dateAdded"] = req_payload["applicationTime"] * 1000
        application_dict["dateLastModified"] = req_payload["lastModifiedTime"] * 1000
        application_dict["candidate"] = candidate_info
        app_status = req_payload["currentStage"] if req_payload["currentStage"] else ""
        application_dict["status"] = app_status
        application_dict["source"] = "Eightfold API user"
        application_dict["comments"] = req_payload.get("comment", "")
        application_dict["jobOrder"] = {"id": req_payload["atsJobId"]}
        return application_dict

    def create_application_data(self, application_info_list):
        application_list = list()
        for application_dict in application_info_list:
            resp_data = self.create_entity("JobSubmission", application_dict)

            if resp_data:
                application_id = resp_data["changedEntityId"]
                application_list.append(application_id)
        return application_list

    def create_bh_request_dict(self, data, entity_id):
        """
        Create a new data dictionary that can be directly added to BH for creating a candidate
        :param data: candidate payload from EF
        :param entity_id: BH Entity ID of a candidate
        :return: New payload for adding this data to BH
        """
        item = dict()
        item['id'] = entity_id
        item['firstName'] = data.get("firstName", "")
        item['lastName'] = data.get("lastName", "")
        item['name'] = item['firstName'] + " " + item['lastName']
        email_data = data.get("email") if 'email' in data.keys() else data.get("emails", "")
        phone_num = data.get("phone") if 'phone' in data.keys() else data.get("phones", "")

        if email_data and "," in email_data:
            emails = email_data.split(",")
            item['email'] = emails[0]
            item['email2'] = emails[1] 
        else:
            item['email'] = email_data
        
        item['mobile'] = phone_num
        if item['mobile'] and  "," in item['mobile']:
            item['mobile'] = phone_num.split(',')[0]
        if phone_num and len(phone_num) > 20:
            item['mobile'] = ""
        item['occupation'] = data.get("title", "")[:90] if data.get("title") else ""
        # Not available for ATS candidate
        if data.get("atsData") and data["atsData"].get("dateOfBirth"):
            item['dateOfBirth'] = data["atsData"]["dateOfBirth"]
        item['gender'] = data.get("gender")[0].upper() if data.get("gender") else "U"
        if data.get("atsData") and data["atsData"].get("visaStatuses"):
            visaStatuses = data["atsData"]["visaStatuses"] #this is an array of string
            item['customText3'] = ",".join(visaStatuses) # item['customText3'] is string
        item['address'] = {}
        item['address']['countryID'] = country_ids[data.get("location")] if data.get("location") and data.get("location") in country_ids.keys() else ""
        return item
