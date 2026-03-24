'''
This file provides functionalities to sync data between BullHorn - Persol Kelly ATS system to Eightfold.
It can process candidate_create, candidate_update, application_create, application_update, app_notify triggers from Eightfold
It can subscribe to events in Bullhorn and pull out updates for Candidate, JobOrder entities.
@author: Sadashiva K, Abel Robra- Arjuna LLC
'''

import collections
import re
import os
import time
import json
import random
import traceback2
import datetime
import bh_utility
import traceback
import copy
from bullhorn_adapter import BullHorn
from eightfold_adapter import Eightfold
from ef_app_sdk import EFAppSDK
from diff_checker import DiffChecker
from country_ids import COUNTRY_IDS as country_ids
import string_utils
from exceptions import RetryableException, NonRetryableException

syncStages = ["Submission", "CV_Sent_&_Interview", "CV Sent & Interview", "Rejected", "Offer & Placement", "Confirmed", "Placed"]

CANDIDATE_FIELDS = "id,occupation,dateOfBirth,customText3,address,email, email2,mobile,gender,ethnicity,firstName,customText1," \
                   "lastName,dateLastModified,primarySkills[15],educations[15],workHistories[15],notes[15],submissions[15],fileAttachments,customTextBlock1"
EDUCATION_FIELDS = "id,degree,school,startDate,endDate,city,major,comments"
WORK_HISTORIES_FIELDS = "id,companyName,startDate,title,comments,endDate"
SKILLS_FIELDS = "id,name"
NOTES_FIELDS = "dateAdded,comments,commentingPerson,action"
SUBMISSION_FIELDS = "id,dateAdded,dateLastModified,status,comments,source,candidate,jobOrder,sendingUser,customText1"
CANDIDATE_SUB_ENTITIES = ['primarySkills', 'educations', 'workHistories', 'notes', 'fileAttachments']
CANDIDATE_EDIT_FIELDS = "educations[15],workHistories[15],notes[15],submissions[15],customDate1"

wh_keys = ['endDate', 'comments', 'companyName', 'title', 'startDate']
edu_keys = ['degree', 'school', 'major', 'comments', 'startDate', 'endDate']
note_keys = ['dateAdded', 'comments', 'action']

ALL_CANDIDATE_FIELDS = CANDIDATE_FIELDS.split(",") + CANDIDATE_SUB_ENTITIES

JOB_ORDER_FIELDS = "id,title,description,clientCorporation,status,isOpen,correlatedCustomText10,dateLastModified,dateAdded,publishedCategory,customText13,owner,address,clientContact"

MAX_RETRY_COUNT = 5
MAX_RETRY_COUNT_EXISTING_CHECK = 3

MAX_REASON_LENGTH = 255

class SynchronizeAdapter():
    """
    This class initializes Eightfold and Bullhorn adaptors classes, that can further make API calls to BH or EF.
    This has code to process all EF originated triggers and events from BH.
    """

    def __init__(self, app_settings, req_data, app_sdk):
        """
        Initialize Bullhorn, Eightfold classes, app sdk.
        :param app_settings: input params to initialize EF, BH
        :param req_data: Input request data that contains payload from BH/ EF
        :param app_sdk: app sdk, mainly used for logging.
        """
        self.bh = BullHorn(app_settings, app_sdk=app_sdk)
        self.ef = Eightfold(app_settings, req_data, app_sdk=app_sdk)
        self.diff_check = DiffChecker(app_sdk)
        self.bh_data = None
        self.app_sdk = app_sdk
        self.bh.setup()

    def filter_events(self, updated_events):
        # 1. Maintain the initial order (ie sorted by timestamp)
        # 2. BH Production environment can pull only 200 records at a time with search API call
        # 3. For each entity type of events, we need to remove the events that dont show up in the search call to BH using the received ids (ie they dont exist for the credentials provided)
        # 4. Bull horn has provided credentials for Singapore region but the subscription events are coming for all regions.   
        if not updated_events:
            return []
        filtered_events = []
        entity_name_dict = {}
        for event in updated_events:
            entity_name = event.get('entityName')
            if entity_name not in entity_name_dict:
                entity_name_dict[entity_name] = []
            entity_name_dict[entity_name].append(event)

        for entity_name, events in entity_name_dict.items():
            if entity_name not in ['Candidate','JobOrder']: 
                # Search API throws error for 'CandidateEducation' ,'CandidateWorkHistory'
                # Also query API is done to match these entitities later in pull_events
                filtered_events.extend(events)
                continue

            batch_size = 200 # BH Production environment can pull only 200 records at a time with search API call
            event_batches = [events[i:i+batch_size] for i in range(0, len(events), batch_size)]
            for event_batch in event_batches:
                batch_ids_list = [event.get('entityId') for event in event_batch if 'entityId' in event]
                query = bh_utility.get_query_for_id_list(batch_ids_list)
                valid_event_batch_id_response = self.bh.search_entity_post(entity_name, query, "id", batch_size, use_retry_with_exception=True)
                valid_event_batch_id_response_data = valid_event_batch_id_response.get("data")

                if valid_event_batch_id_response_data:
                    valid_event_id_data_list = [each_rec.get("id") for each_rec in valid_event_batch_id_response_data if 'id' in each_rec]
                    filtered_event_batch = [event for event in event_batch if event.get('entityId') in valid_event_id_data_list]
                    filtered_events.extend(filtered_event_batch)

        sorted_filtered_events_list = sorted(filtered_events, key=lambda x: x['eventTimestamp'])
        return sorted_filtered_events_list

    def filter_candidates(self, candidate_ids):
        filtered_candidate_ids = []
        batch_size = 200
        candidate_batches = [candidate_ids[i:i+batch_size] for i in range(0, len(candidate_ids), batch_size)]
        for candidate_batch in candidate_batches:
            query = bh_utility.get_query_for_id_list(candidate_batch)
            valid_candidate_batch_id_response = self.bh.search_entity_post('Candidate', query, "id", batch_size, use_retry_with_exception=True)
            valid_candidate_batch_id_response_data = valid_candidate_batch_id_response.get("data")

            if valid_candidate_batch_id_response_data:
                valid_candidate_id_data_list = [each_rec.get("id") for each_rec in valid_candidate_batch_id_response_data if 'id' in each_rec]
                filtered_candidate_ids.extend(valid_candidate_id_data_list)
        return filtered_candidate_ids

    def get_subscription_events(self):
        """
        Get all latest events from Bullhorn, aggregate Candidate Sub-entities(CandidateWorkHistory, CandidateEducation, JobSubmission),
         JobOrder and create the schedule_app_notification action to process each of these events using app_notify trigger.
        :return: None
        """
        self.app_sdk.log("Print I am inside of Subscription Events")
        start_ts = int(time.time())
        data = None
        total_actions_list = []
        data = {
            "actions": []
        }

        def pull_events(time_delay=0):
            events_pulled = 0
            actions_list = list()
            updated_events = self.bh.get_events_update()
            self.app_sdk.log(updated_events)

            filtered_events = None
            filter_success = False

            if updated_events and updated_events.get("events"):
                try:
                    filtered_events = self.filter_events(updated_events.get("events"))
                    filter_success = True
                except Exception as e:
                    # we cant retry since self.bh.get_events_update() will fetch furter events
                    err_str = f"Filtering of events failed with error: { traceback.format_exc() }"
                    self.app_sdk.log(err_str)

                if filter_success:
                    # use filtered events if filter_events was able to successfully filter events 
                    self.app_sdk.log(f"filtered events : {filtered_events}")
                    self.app_sdk.log(f"updated_events count : {len(updated_events['events'])} filtered_events count : {len(filtered_events)} ")
                    updated_events['events'] = filtered_events
                        
            if updated_events:
                event_data_dict = dict()
                work_history_ids = list()
                education_ids = list()
                submission_ids = list()
                # Aggregate candidate sub-entities data and send out single candidate update/ create notification.
                for each_event in updated_events.get("events"):
                    events_pulled = events_pulled + 1
                    entity_name = each_event["entityName"]
                    entity_id = each_event["entityId"]
                    if entity_name == "CandidateWorkHistory":
                        work_history_ids.append(str(entity_id))
                    elif entity_name == "CandidateEducation":
                        education_ids.append(str(entity_id))
                    elif entity_name == "JobSubmission":
                        submission_ids.append(str(entity_id))
                    else:
                        entity_event = each_event["entityEventType"]
                        entity_updates = each_event.get("updatedProperties", [])
                        record = [entity_name, entity_id, entity_event, entity_updates]
                        if event_data_dict.get(entity_id):
                            event_data_dict[entity_id] = event_data_dict[entity_id] + [record]
                        else:
                            event_data_dict[entity_id] = [record]
                work_list = list()
                education_list = list()
                submission_list = list()
                sub_entity_list = list()
                if work_history_ids:
                    n = 200
                    # BH Production environment can pull only 200 records at a time with search API call
                    wh_batches = [work_history_ids[i:i+n] for i in range(0, len(work_history_ids), n)]
                    for wh_batch in wh_batches:
                        work_query_string = bh_utility.get_query_string(wh_batch)
                        self.app_sdk.log("WorkHistories Query String - " + work_query_string)
                        try:
                            w_data = self.bh.search_entity("CandidateWorkHistory", work_query_string, "candidate", use_retry_with_exception=True)
                            if w_data["data"]:
                                w_list = [each_rec["candidate"]["id"] for each_rec in w_data["data"]]
                                work_list = work_list + w_list
                        except Exception:
                            self.app_sdk.log(f"Exception occurred while fetching work history from work history ids: { traceback.format_exc() }")
                if education_ids:
                    n = 200
                    edu_batches = [education_ids[i:i+n] for i in range(0, len(education_ids), n)]
                    for edu_batch in edu_batches:
                        edu_query_string = bh_utility.get_query_string(edu_batch)
                        self.app_sdk.log("Education Query String - " + edu_query_string)
                        try:
                            edu_data = self.bh.search_entity("CandidateEducation", edu_query_string, "candidate", use_retry_with_exception=True)
                            if edu_data["data"]:
                                e_list = [each_rec["candidate"]["id"] for each_rec in edu_data["data"]]
                                education_list = education_list + e_list
                        except Exception:
                            self.app_sdk.log(f"Exception occurred while fetching candidates from candidate education ids: { traceback.format_exc() }")
                if submission_ids:
                    n = 200
                    sub_batches = [submission_ids[i:i+n] for i in range(0, len(submission_ids), n)]
                    for sub_batch in sub_batches:
                        sub_query_string = bh_utility.get_query_string(sub_batch)
                        try:
                            sub_data = self.bh.search_entity("JobSubmission", sub_query_string, "candidate", use_retry_with_exception=True)
                            if sub_data["data"]:
                                s_list = [each_rec["candidate"]["id"] for each_rec in sub_data["data"]]
                                submission_list = submission_list + s_list
                        except Exception:
                            self.app_sdk.log(f"Exception occurred while fetching candidates from candidate submission ids: { traceback.format_exc() }")
                sub_entity_list = set(education_list + work_list + submission_list)

                # We are seeing cases where CandidateWorkHistory belonging to Singapore region have candidate which are not from singapore region so filter out
                # candidates which are not from singapore region
                filtered_candidate_ids = None
                filter_candidates_success = False
                try:
                    filtered_candidate_ids = self.filter_candidates(list(sub_entity_list))
                    filter_candidates_success = True
                except Exception:
                    # we cant retry since self.bh.get_events_update() will fetch furter events
                    err_str = f"Filtering of candidates from sub_entity failed with error: { traceback.format_exc() }"
                    self.app_sdk.log(err_str)
                
                if filter_candidates_success:
                    self.app_sdk.log(f"filtered candidate ids from sub_entity: {filtered_candidate_ids}")
                    self.app_sdk.log(f"candidates from sub_entity count before filtering: {len(sub_entity_list)} , candidates from sub_entity count after filtering : {len(filtered_candidate_ids)} ")
                    sub_entity_list = filtered_candidate_ids

                if sub_entity_list:
                    for each_rec in sub_entity_list:
                        if each_rec not in event_data_dict:
                            event_data_dict[each_rec] = [["Candidate", each_rec, "UPDATED", []]]

                for each_id, each_payload in event_data_dict.items():
                    if len(each_payload) == 1:
                        final_payload = each_payload[0]
                    else:
                        e_types = [e_data[2] for e_data in each_payload]
                        if "INSERTED" in e_types:
                            create_index = e_types.index("INSERTED")
                            final_payload = each_payload[create_index]
                        else:
                            all_updates = list()
                            for e_data in each_payload:
                                all_updates = all_updates + e_data[3]
                            if "isDeleted" in all_updates:
                                final_payload = each_payload[0]
                                final_payload[2] = "DELETED"
                            else:
                                final_payload = each_payload[0]
                                final_payload[3] = all_updates

                    # Added time delay with each trigger to ensure that we don't run into rate limit exceeded - 429 Error

                    time_delay += 5 #10 Changed this to 5 sec, as we are expecting too many events in an hour
                    action = {
                        'action_name': 'schedule_app_notification',
                        'request_data': {
                            "schedule_after_secs": time_delay,
                            "notification_payload": {'event': final_payload,
                                                     'trigger_name': 'app_notify'
                                                     }
                        }}
                    actions_list.append(action)
            return actions_list, time_delay, events_pulled

        ac_list, t_delay, events_pulled = pull_events()
        total_actions_list = total_actions_list + ac_list
        total_events_pulled = events_pulled

        # As the aws lambda has request timeout limit of 15 mins, we will it process only for 10 mins(5 mins buffer) and remaining events in the queue will be picked up by
        # next scheduled hourly
        while ac_list and events_pulled > 0:
            if int(time.time()) > start_ts + 600:
                self.app_sdk.log(f"Time limit of 10 mins exceeded for this scheduled hourly request. Request started at start_ts: {start_ts} and ended at: {int(time.time())}\n Process remaining events in the next scheduled hourly request")
                break
            ac_list, t_delay, events_pulled = pull_events(t_delay)
            total_actions_list = total_actions_list + ac_list
            total_events_pulled = total_events_pulled + events_pulled
        
        data["actions"] = total_actions_list

        self.app_sdk.log(f"Total events pulled : {total_events_pulled}")
        self.app_sdk.log(f"Total events used   : {len(total_actions_list)}")
        return data

    def process_education_data(self):
        """
        Process education information from BH -ids,  and create education records for adding these to EF.
        :return: list of education records
        """
        education_count = self.bh_data["educations"]["total"]
        education_data = self.bh_data["educations"]["data"]
        education_list = []
        if education_count:
            try:
                education_ids = [str(edu["id"]) for edu in education_data]
                edu_query_string = bh_utility.get_query_string(education_ids)
                self.app_sdk.log("Education Query String - " + edu_query_string)
                edu_data = self.bh.search_entity("CandidateEducation", edu_query_string, EDUCATION_FIELDS)
                if edu_data["data"]:
                    education_list = bh_utility.process_education_data(edu_data)
            except Exception as ex:
                self.app_sdk.log("Issue processing Education Data")
                self.app_sdk.log(ex)
        return education_list

    def process_work_histories(self):
        work_count = self.bh_data["workHistories"]["total"]
        work_data = self.bh_data["workHistories"]["data"]
        work_list = []
        if work_count:
            try:
                work_ids = [str(work["id"]) for work in work_data]
                work_query_string = bh_utility.get_query_string(work_ids)
                self.app_sdk.log("WorkHistories Query String - " + work_query_string)
                w_data = self.bh.search_entity("CandidateWorkHistory", work_query_string, WORK_HISTORIES_FIELDS)
                if w_data["data"]:
                    work_list = bh_utility.process_work_histories_data(w_data)
            except Exception as ex:
                self.app_sdk.log("Issue processing Work History")
                self.app_sdk.log(ex)
        return work_list

    def process_skills(self):
        skills_count = self.bh_data["primarySkills"]["total"]
        skills_data = self.bh_data["primarySkills"]["data"]
        skills_list = []
        if skills_count:
            try:
                skill_ids = [str(skill["id"]) for skill in skills_data]
                skill_query_string = bh_utility.get_query_string(skill_ids)
                self.app_sdk.log("Skill Query String - " + skill_query_string)
                s_data = self.bh.search_entity("Skill", skill_query_string, SKILLS_FIELDS)
                if s_data["data"]:
                    skills_list = bh_utility.process_skills_data(s_data)
            except Exception as ex:
                self.app_sdk.log("Issue processing Primary Skills")
                self.app_sdk.log(ex)
        return skills_list

    def process_notes_data(self):
        notes_count = self.bh_data["notes"]["total"]
        notes_data = self.bh_data["notes"]["data"]
        notes_list = []
        if notes_count:
            try:
                notes_ids = [str(note["id"]) for note in notes_data]
                notes_query_string = bh_utility.get_query_json(notes_ids)
                self.app_sdk.log("Notes Query String - ")
                self.app_sdk.log(notes_query_string)
                note_info = self.bh.search_entity_post("Note", notes_query_string, NOTES_FIELDS)
                if note_info["data"]:
                    notes_list = bh_utility.process_notes_data(note_info)
            except Exception as ex:
                self.app_sdk.log("Exception in Notes")
                self.app_sdk.log(ex)
        return notes_list

    def process_submission_data(self):
        candidate_id = str(self.bh_data["id"])
        submission_count = self.bh_data["submissions"]["total"]
        submissions_data = self.bh_data["submissions"]["data"]
        applications_list = []
        if submission_count:
            try:
                submission_ids = [str(submission["id"]) for submission in submissions_data]
                submission_query_string = bh_utility.get_query_json(submission_ids)
                self.app_sdk.log("Submission Query String - ")
                self.app_sdk.log(submission_query_string)
                submission_info = self.bh.search_entity_post("JobSubmission", submission_query_string,
                                                             SUBMISSION_FIELDS)
                if submission_info["data"]:
                    applications_list = self.process_job_submission_data(submission_info, candidate_id)

            except Exception as ex:
                self.app_sdk.log("Exception in Application processing")
                self.app_sdk.log(ex)
        return applications_list

    def process_job_submission_data(self, submission_info, candidate_id):
        submission_list = []
        job_id_list = []
        for submission in submission_info["data"]:
            submission_dict = dict()
            submission_dict["applicationTs"] = round(submission["dateAdded"] / 1000) if submission["dateAdded"] else 0
            submission_dict["candidateId"] = candidate_id
            submission_dict["lastModifiedTs"] = round(submission["dateLastModified"] / 1000) if submission[
                "dateLastModified"] else 0
            job_order_dict = submission.get("jobOrder")
            if job_order_dict:
                s_id = str(job_order_dict.get("id", ""))
                job_dict = {
                    "atsJobId": s_id,
                    "name": job_order_dict.get("title", "")
                }
                submission_dict["jobs"] = [job_dict]
                if s_id in job_id_list:
                    continue
                else:
                    job_id_list.append(s_id)
            if submission.get("customText1", ""):
                submission_dict["applicationId"] = submission.get("customText1")
            else:
                submission_dict["applicationId"] = str(submission["id"])
            submission_status = submission.get("status", "")
            if submission_status:
                submission_dict["currentStage"] = dict()
                submission_dict["currentStage"]["wfStage"] = submission.get("status", "")
                submission_dict["currentStage"]["stageTs"] = submission_dict["lastModifiedTs"]
                submission_dict["currentStage"]["reason"] = " "
                submission_dict["currentStage"]["wfSubStage"] = ""
                user_dict = dict()
                if submission.get("sendingUser"):
                    user_id = submission["sendingUser"]["id"]
                    corporate_user = self.bh.get_entity_data("CorporateUser", user_id, "externalEmail,email,name")
                    if corporate_user and corporate_user["data"]:
                        c_user_data = corporate_user["data"]
                        user_dict["name"] = c_user_data.get("name", " ")
                        user_dict["email"] = c_user_data["email"] if c_user_data.get("email") else c_user_data.get("externalEmail", " ")
                    else:
                        user_dict["name"] = " "
                        user_dict["email"] = " "
                else:
                    user_dict["name"] = " "
                    user_dict["email"] = " "
                submission_dict["currentStage"]["user"] = user_dict

            valid_status = ["active", "hired", "rejected", "converted"]
            if submission["status"] in valid_status:
                submission_dict["status"] = submission["status"]
            # Truncate or limit the reason if it's longer than the MAX_REASON_LENGTH since API v2 has a validation of 5000 on this field
            submission_dict["reason"] = submission["comments"][:MAX_REASON_LENGTH]
            submission_dict["sourceName"] = submission["source"]
            submission_list.append(submission_dict)
        return submission_list

    def process_resume_content(self, entity_name, entity_id):
        attachment_count = self.bh_data["fileAttachments"]["total"]
        resume_content = dict()
        if attachment_count:
            try:
                resume_id = self.bh.get_resume_file_id(entity_name, entity_id)
                if resume_id:
                    base64_code, extension = self.bh.get_resume_raw_data("Candidate", entity_id, resume_id)
                    self.app_sdk.log("Processing %s file" % extension)
                    resume_content = {
                        "isBase64": True,
                        "content": base64_code,
                        "extension": extension if extension else ".txt"
                    }
            except Exception as ex:
                self.app_sdk.log("Exception in processing files")
                self.app_sdk.log(ex)
        return resume_content

    def map_candidate_all_fields(self, entity_name, entity_id):
        """
        Get data from BH and prepare a payload that can be use to create data in EF
        :param entity_name: BH Entity name
        :param entity_id: BH Entity Id
        :return: transformed payload
        """
        mapped_data = self.bh.map_fields(entity_name, self.bh_data)
        education_list = self.process_education_data()
        if education_list:
            mapped_data["education"] = education_list

        work_list = self.process_work_histories()
        if work_list:
            mapped_data["experience"] = work_list

        skills_list = self.process_skills()
        if skills_list:
            mapped_data["skills"] = skills_list

        notes_list = self.process_notes_data()
        if notes_list:
            mapped_data["notes"] = notes_list

        applications_list = self.process_submission_data()
        if applications_list:
            mapped_data["applications"] = applications_list

        resume_content = self.process_resume_content(entity_name, entity_id)
        if resume_content:
            mapped_data["resumeContent"] = resume_content

        mapped_data["candidateId"] = str(mapped_data["candidateId"])
        m_keys = mapped_data.keys()

        # field validation
        if "firstName" in mapped_data and mapped_data["firstName"] == "":
            mapped_data["firstName"] = " "

        if "visaStatuses" in m_keys:
            mapped_data["visaStatuses"] = list(mapped_data["visaStatuses"].split(","))
        if "dateOfBirth" in m_keys:
            try:
                dob = str(datetime.datetime.fromtimestamp(mapped_data["dateOfBirth"] / 1000).date()) if \
                    mapped_data["dateOfBirth"] else ""
                if dob:
                    mapped_data["dateOfBirth"] = dob
            except Exception as ex:
                self.app_sdk.log("DOB value issue")
                del mapped_data["dateOfBirth"]
        return mapped_data

    def process_bh_event(self, event_payload, req_data):
        self.app_sdk.log("Inside Event")
        entity_name, entity_id, entity_event, entity_updates = event_payload
        self.app_sdk.log(f"Reported updates from BH for {entity_id} are : {entity_updates} ")
        if entity_name == 'Candidate':
            try:
                bullhorn_data = self.bh.get_entity_data(entity_name, entity_id, CANDIDATE_FIELDS)
            except Exception as ex:
                self.app_sdk.log(str(ex))
                range_info = list(range(60, 200))
                retry_time = random.choice(range_info)
                self.app_sdk.log(f"Failed to get a profile in BH, retry in {retry_time}")
                ret_data = None
                if req_data.get("retry_count", 0) < MAX_RETRY_COUNT:
                    ret_data = create_ret_data_internal_trigger(retry_time, "app_notify", req_data)
                return ret_data
            self.bh_data = bullhorn_data["data"]
            if entity_event == "DELETED":
                profile_id = self.bh_data["customText1"]
                if profile_id:
                    self.ef.delete_ef("Candidate", profile_id)

            ef_data = self.ef.get_ats_candidate(entity_id)
            mapped_data = self.map_candidate_all_fields(entity_name, entity_id)
            last_activity = mapped_data["lastActivityTs"]
            mapped_data["lastActivityTs"] = round(last_activity/1000)
            if "firstName" not in mapped_data:
                mapped_data["firstName"] = " "

            if entity_event == "INSERTED":
                print(mapped_data)
                if "emails2" in mapped_data:
                    if mapped_data["emails2"]:
                        email1 = mapped_data["emails"]
                        mapped_data["emails"] = str(email1) + "," + str(mapped_data["emails2"])
                    del mapped_data["emails2"]
                if ef_data:
                    self.app_sdk.log(f"Candidate found - {str(entity_id)}. entity_event: {entity_event}, actual operation: UPDATED")
                    result = None
                    # only in candidate_update 
                    if not self.diff_check.has_difference(copy.deepcopy(ef_data), copy.deepcopy(mapped_data), entity_id):
                        self.app_sdk.log(f"Skipping update for entity_id : {entity_id} since no difference found. entity_event: {entity_event}, actual operation: UPDATED")
                        return None
                    try:
                        self.app_sdk.log(entity_id)
                        result = self.ef.update_ef(mapped_data, 'Candidate', entity_id)
                        self.app_sdk.log(f"Event Successfully Updated - Entity ID - {str(entity_id)}. entity_event: {entity_event}, actual operation: UPDATED")
                    except Exception as ex:
                        self.app_sdk.log(f"ERROR: Unable to update the Entity. entity_event: {entity_event}")
                        self.app_sdk.log(str(ex))
                        retry_time = 180
                        ret_data = create_ret_data_internal_trigger(retry_time, "app_notify", req_data)
                        self.app_sdk.log("Retry event in 3 minutes")
                        return ret_data
                else:
                    self.app_sdk.log(f"Processing Insert Event  - Candidate- Entity ID - {str(entity_id)}. entity_event: {entity_event}, actual operation: INSERTED")
                    try:
                        self.ef.create_ef(mapped_data, 'Candidate')
                        self.app_sdk.log(f"Event Successfully Inserted - Entity ID - {str(entity_id)}. entity_event: {entity_event}, actual operation: INSERTED")
                    except Exception as ex:
                        self.app_sdk.log(f"ERROR: Unable to insert the Entity. entity_event: {entity_event}")
                        self.app_sdk.log(ex)
                        retry_time = 180
                        ret_data = create_ret_data_internal_trigger(retry_time, "app_notify", req_data)
                        self.app_sdk.log("Retry event in 3 minutes")
                        return ret_data
                return None

            if entity_event == "UPDATED":
                self.app_sdk.log(f"Processing Update Event  - Candidate- Entity ID - {str(entity_id)}. entity_event: {entity_event}")
                print(mapped_data)
                if "emails2" in mapped_data:
                    if mapped_data["emails2"]:
                        email1 = mapped_data["emails"]
                        mapped_data["emails"] = str(email1) + "," + str(mapped_data["emails2"])
                    del mapped_data["emails2"]

                result = None

                # only in candidate_update 
                if not self.diff_check.has_difference(copy.deepcopy(ef_data), copy.deepcopy(mapped_data), entity_id):
                    self.app_sdk.log(f"Skipping update for entity_id : {entity_id} since no difference found. entity_event: {entity_event}")
                    return None
                if ef_data:
                    try:
                        self.app_sdk.log(entity_id)
                        result = self.ef.update_ef(mapped_data, 'Candidate', entity_id)
                        self.app_sdk.log(f"Event Successfully Updated - Entity ID - {str(entity_id)}. entity_event: {entity_event}, actual operation: UPDATED")
                    except Exception as ex:
                        self.app_sdk.log(str(ex))
                        self.app_sdk.log(f"ERROR: Unable to update the Entity. entity_event: {entity_event}")
                        retry_time = 180
                        ret_data = create_ret_data_internal_trigger(retry_time, "app_notify", req_data)
                        self.app_sdk.log("Retry event in 3 minutes")
                        return ret_data
                else:
                    try:
                        self.ef.create_ef(mapped_data, 'Candidate')
                        self.app_sdk.log(f"Event Successfully Inserted - Entity ID - {str(entity_id)}. entity_event: {entity_event}, actual operation: INSERTED")
                    except Exception as ex:
                        self.app_sdk.log(str(ex))
                        self.app_sdk.log(f"ERROR: Unable to insert the Entity. entity_event: {entity_event}")
                        retry_time = 180
                        ret_data = create_ret_data_internal_trigger(retry_time, "app_notify", req_data)
                        self.app_sdk.log("Retry event in 3 minutes")
                        return ret_data
                return None
            else:
                self.app_sdk.log(f"Fails in mapping data")

        elif entity_name == 'JobOrder':
            self.app_sdk.log("Processing Event Type - Job Order- Entity ID - " + str(entity_id))
            try:
                bullhorn_data = self.bh.get_entity_data(entity_name, entity_id, JOB_ORDER_FIELDS)
            except Exception as ex:
                self.app_sdk.log("Entity Not Found")
                return
            if not bullhorn_data or "data" not in bullhorn_data:
                return
            self.bh_data = bullhorn_data.get("data")

            if self.bh_data['status'] == 'Draft' or self.bh_data['status'] == 'Template':
                self.app_sdk.log(f"JobOrder status {self.bh_data['status']}, ignore" )
                return

            mapped_data = self.bh.map_fields(entity_name, self.bh_data)
            mapped_data["open"] = True if mapped_data.get("open") else False
            mapped_data["atsEntityId"] = str(mapped_data["atsEntityId"])
            mapped_data["posted"] = True  # Allowed values - external, internal, all. Currently its not mapped in BH
            if mapped_data["createdAt"]:
                mapped_data["createdAt"] = mapped_data["createdAt"] / 1000
            if mapped_data["lastUpdated"]:
                mapped_data["lastUpdated"] = mapped_data["lastUpdated"] / 1000  # int(mapped_data["lastUpdated"])
            ever_green = mapped_data.get("evergreen")
            if ever_green and (ever_green.count("months") > 0 or ever_green.count("years") > 0):
                mapped_data["evergreen"] = True
            else:
                mapped_data["evergreen"] = False
            if entity_event == 'INSERTED':
                result = self.ef.create_ef(mapped_data, 'Position')
                if result:
                    self.app_sdk.log("Event Successfully Inserted or Updated- Entity ID - " + str(entity_id))
            elif entity_event == 'UPDATED':
                ats_position_id = str(self.bh_data["id"])
                try:
                    result = self.ef.update_ef(mapped_data, 'Position', ats_position_id)
                except Exception as ex:
                    result = self.ef.create_ef(mapped_data, 'Position')
                if result:
                    self.app_sdk.log("Event Successfully Updated or Updated- Entity ID - " + str(entity_id))

    def compare_previous_and_current_data(self, previous_data, current_data, keys=[]):
        p_records = [tuple([str(ex_data[key]) for key in keys]) for ex_data in previous_data]
        c_records = [tuple([str(e_dat[key]) for key in keys]) for e_dat in current_data]
        removed_data = set(p_records) - set(c_records)
        new_data = set(c_records) - set(p_records)
        return list(removed_data), list(new_data)

    def start_event_subscription(self):
        """
        One time run to subscribe to Bullhorn events
        :return: None
        """
        # One time initialization
        # self.bh.delete_subscription()
        self.bh.event_subscription()

    def create_chunks(self, lis, chunk_size=10):
        """
        Method to split a long list into mutiple lists of equal sizes
        :param lis: input data list
        :param chunk_size: size of each list in the resultant list
        :return:
        """
        for i in range(0, len(lis), chunk_size):
            yield lis[i:i + chunk_size]

    def process_skills_object(self, skills_list):
        """
        Get the BH associated Skill Ids with each of the skill provided in skills_list
        :param skills_list: List of EF candidate's skills
        :return: aggregated skill ids from BH.
        """
        if skills_list and type(skills_list[0]) == dict:
            skills_list = [skills_list[n]['displayName'] for n in range(len(skills_list)) if skills_list[n]['displayName'] != None and skills_list[n]['displayName'] != ""]
        else: # always getting this only.
            skills_list = [skill for skill in skills_list if skill != ""]
        if len(skills_list) == 0:
            return False

        # Code to GET corresponding Skill IDs from BH and then attach to Candidate
        skill_ids = []
        skill_name_processed = []
        if len(skills_list) > 10:
            skills_chunks = list(self.create_chunks(skills_list))
        else:
            skills_chunks = [skills_list]
        for each_chunk in skills_chunks:
            skills_format = ["\'" + str(s_string.replace("\'", " ")) + "\'" for s_string in each_chunk if len(s_string) > 0]
            skill_query_string = bh_utility.get_query_string(skills_format, param_type="name")
            s_data = self.bh.search_entity("Skill", skill_query_string, SKILLS_FIELDS, use_retry_with_exception=True)

            skill_res = s_data.get("data")
            if skill_res:
                for ski in skill_res:
                    if not ski.get('name') in skill_name_processed:
                        skill_ids.append(ski.get("id"))
                        skill_name_processed.append(ski.get("name"))
        if skill_ids:
            return {"replaceAll": skill_ids}
        return None

    def compare_and_del_entity(self, entity_data, entity_count, del_exp, new_exp, entity_list, entity_type, entity_fields, candidate_id=False, keys=[]):
        """
        Method to sync entities information between BH and EF. This code is mainly used for Education and Experience
        :param entity_data: BH Candidate Education/ WorkHistory data
        :param entity_count: BH Candidate Education/ WorkHistory record count
        :param del_exp: entity records that are to be deleted
        :param new_exp: entity records that are to be newly created in BH
        :param entity_list: entity list information from EF
        :param entity_type: either CandidateEducation/ CandidateWorkHistory
        :param entity_fields: entity fields in BH
        :param candidate_id: Candidate Id in BH
        :param keys: Mandatory fields with in an entity
        :return:
        """
        try:
            if not entity_data:
                for each_exp in entity_list:
                    self.bh.create_entity(entity_type, each_exp)
                return None

            entity_ids = [str(entity["id"]) for entity in entity_data]
            entity_query_string = bh_utility.get_query_string(entity_ids) + ' AND isDeleted=false'
            w_response = self.bh.search_entity(entity_type, entity_query_string, entity_fields)
            w_data = w_response["data"]
            if len(entity_data) == 15 and candidate_id:
                entity_query_string = bh_utility.get_query_string(entity_ids, next_page = True)
                entity_query_string += f' AND candidate={candidate_id} AND isDeleted=false'
                w_data_next = self.bh.search_entity(entity_type, entity_query_string, entity_fields)
                entity_ids_next = [str(entity["id"]) for entity in w_data_next["data"]]
                entity_ids += entity_ids_next
                w_data += w_data_next["data"]

            bh_exp_data = [tuple([str(each_w[key]) for key in keys]) for each_w in w_data]
            unique_records = set(bh_exp_data)
            if len(unique_records) != len(bh_exp_data):
                duplicate_records = [item for item, count in collections.Counter(bh_exp_data).items() if count > 1]
                for each_r in duplicate_records:
                    for each_exp in w_data:
                        if list(each_r).sort(key=str) == list(each_exp[key] for key in keys).sort(key=str):
                            self.app_sdk.log("Duplicate record of experience/ education is deleted")
                            entity_id = each_exp["id"]
                            self.bh.delete_entity(entity_type, entity_id)
                            break

            if del_exp and entity_count:
                for each_w in w_data:
                    each_rec = tuple([str(each_w[key]) for key in keys])
                    if each_rec in del_exp:
                        entity_id = each_w["id"]
                        self.bh.delete_entity(entity_type, entity_id)
            if new_exp:
                for each_exp in entity_list:
                    exp_d = tuple([str(each_exp[key]) for key in keys])
                    if exp_d in new_exp and exp_d not in bh_exp_data:
                        self.bh.create_entity(entity_type, each_exp)
        except Exception as ex:
            traceback.print_exc()
            self.app_sdk.log(f"Error in process EF records: {ex}")

    def compare_create_note(self, notes_info_list, bh_comments):
        """
        Method to sync notes information frmo EF to BH
        :param notes_info_list: Notes records from EF
        :param bh_comments: Notes records from BH
        :return:
        """
        for each_note in notes_info_list:
            note_info = [each_note[key] for key in note_keys]
            if note_info not in bh_comments:
                self.bh.create_entity("Note", each_note)


    def create_file_bh(self, resume_file_name, raw_file_content, entity_id):
        """
        Create a file from EF resume Base64 code and upload this file to BH
        :param resume_file_name: resume file name
        :param raw_file_content: base64 code of resume file
        :param entity_id: BH candidate Id
        :return:
        """
        bh_file_names = self.bh.get_resume_file_names('Candidate', entity_id, use_retry_with_exception=True)
        if bh_file_names:
            if resume_file_name in bh_file_names:
                self.app_sdk.log("File already exist in BH")
                return

        import base64
        decoded_data = base64.b64decode(raw_file_content)
        resume_file_name = '/tmp/' + resume_file_name
        with open(resume_file_name, 'wb') as resume_file:
            resume_file.write(decoded_data)
        self.bh.attach_files_entity("Candidate", entity_id, resume_file_name, use_retry_with_exception=True)
        resume_file.close()
        os.remove(resume_file_name)

    def is_candidate_in_bh(self, candidate_ats_id):
        # this function is also used in handle_create_candidate
        """
        Check if the candidate already exists in Bullhorn
        :param candidate_ats_id:  ATS Entity Id of the Candidate in EF
        :return: True or False based on candidate presence in Bullhorn
        """
        try:
            resp_data = self.bh.get_entity_data("Candidate", candidate_ats_id, "id,email,customText1", use_retry_with_exception=False)
            if resp_data:
                self.app_sdk.log(f"Candidate is already created in BH with data: {resp_data.get('data')}")
                return True
            return False
        except Exception as ex:
            if str(ex).find('status_code: 404') !=-1 or str(ex).find('"errorCode":404') !=-1 :
                return False
            self.app_sdk.log(f"get_entity_data exception : {ex} ")
            raise ex

    def delete_and_create_resume_in_bullhorn(self, resume_spec_item, candidate_id, profile_id):
        
        try:
            data_from_ef_api = self.ef.get_ef_data_candidate_profile(profile_id, use_retry_with_exception=True)
        except Exception as ex:
            traceback.print_exc()

        if not data_from_ef_api:
            return
        
        raw_file_content = data_from_ef_api.get("resume") if "resume" in data_from_ef_api else data_from_ef_api.get("resumeContent")
        resume_file_name = data_from_ef_api.get("resumeFileName")
        
        if resume_file_name and raw_file_content:
            self.create_file_bh(resume_file_name, raw_file_content, candidate_id)
    
        return

    def datetime_to_timestamp(self, date_datetime):
        try:
            date_timestamp = string_utils.parse_datetime(date_datetime).timestamp()
        except Exception as ex:
            err_str = f"Could not convert {date_datetime} into timestamp. traceback: {traceback.format_exc()}"
            self.app_sdk.log(err_str)
            return None
        return date_timestamp

    def delete_and_create_experience_in_bullhorn(self, experience_section_list, candidate_id):
        new_bh_experience_list = []

        for experience in experience_section_list:
            new_bh_experience =  {}

            if experience.get("title"):
                new_bh_experience["title"] = experience.get("title")

            if experience.get("description"): 
                new_bh_experience["comments"] = experience.get("description")

            new_bh_experience["companyName"] = experience.get("work") if experience.get("work") else 'Not specified'

            new_bh_experience["candidate"] = {"id": candidate_id}
            
            ef_start_date = experience.get('start_date')
            if ef_start_date and ef_start_date not in ['', 'notKnown']:
                start_date = self.datetime_to_timestamp(ef_start_date)
                if start_date:
                    new_bh_experience['startDate'] = int(start_date*1000)

            ef_end_date = experience.get('end_date')
            if ef_end_date and ef_end_date not in ['', 'Present', 'current', 'notKnown']:
                end_date = self.datetime_to_timestamp(ef_end_date)
                if end_date:
                    new_bh_experience['endDate'] = int(end_date*1000)
            
            new_bh_experience_list.append(new_bh_experience)

        query = f"candidate.id = {candidate_id} and isDeleted = false"
        json_body = { "where": query}
        

        bh_response = self.bh.query_entity_post(entity_type="CandidateWorkHistory", fields="id", search= json_body, use_retry_with_exception=True)
        if bh_response["data"]:
            current_bh_experiences = bh_response["data"]
            for current_bh_experience in current_bh_experiences:

                self.bh.delete_entity("CandidateWorkHistory", current_bh_experience["id"], use_retry_with_exception=True)

        for new_experience in new_bh_experience_list:
            # todo Error handling ?
            self.bh.create_entity("CandidateWorkHistory", new_experience, use_retry_with_exception=True)

    def delete_and_create_education_in_bullhorn(self, education_section_list, candidate_id):      
        new_bh_education_list = []

        for education in education_section_list:
            new_bh_education = {}

            if education.get("degree"):
                new_bh_education["degree"] = education.get("degree")

            if education.get("school"):        
                new_bh_education["school"] = education.get("school")

            if education.get("major"):      
                new_bh_education["major"] = education.get("major")
            
            if education.get("description"):
                new_bh_education["comments"] = education.get("description")
            
            new_bh_education["candidate"] = {"id": candidate_id}

            ef_start_date = education.get('start_date')
            if ef_start_date and ef_start_date not in ['', 'notKnown']:
                start_date = self.datetime_to_timestamp(ef_start_date)
                if start_date:
                    new_bh_education['startDate'] = int(start_date*1000)

            ef_end_date = education.get('end_date')
            if ef_end_date and ef_end_date not in ['', 'Present', 'current', 'notKnown']:
                end_date = self.datetime_to_timestamp(ef_end_date)
                if end_date:
                    bh_end_date=int(end_date*1000)
                    new_bh_education['endDate'] = bh_end_date
                    new_bh_education['graduationDate'] = bh_end_date

            new_bh_education_list.append(new_bh_education)
        
        query = f"candidate.id = {candidate_id} and isDeleted = false"
        json_body = { "where": query}
        
        bh_response = self.bh.query_entity_post(entity_type="CandidateEducation", fields="id", search= json_body, use_retry_with_exception=True)
        current_bh_educations = bh_response["data"]

        for current_bh_education in current_bh_educations:
            self.bh.delete_entity("CandidateEducation", current_bh_education["id"], use_retry_with_exception=True)

        for new_education in new_bh_education_list:
            self.bh.create_entity("CandidateEducation", new_education, use_retry_with_exception=True)

    def handle_change_application_stage(self, event_context):
        #update status, last modified and comments
    
        application =  event_context.get("application")
        if not application:
            err_str = f" No applicaiton found in handle_change_application_stage for {event_context}"
            raise NonRetryableException(err_str)

        if 'application_id' not in application:
            err_str = f" No applicaiton id found in handle_change_application_stage for {event_context}"
            raise NonRetryableException(err_str)

        bh_application_payload = {}
        bh_application_payload['id'] =  int(application['application_id'])
        
        if event_context.get("comment"):
            bh_application_payload["comments"] = event_context.get("comment")
        
        ef_new_stage = event_context.get("new_ats_stage")
        if ef_new_stage:
            bh_application_payload["status"] = ef_new_stage.get("stage")
            stage_ts =  ef_new_stage.get("stage_ts")
            if stage_ts:
                bh_application_payload['dateLastModified'] = stage_ts*1000
            else:
                bh_application_payload['dateLastModified'] = int(time.time()*1000)
        else:
            bh_application_payload["status"] = ""    
            bh_application_payload['dateLastModified'] = int(time.time()*1000) 
        
        return self.bh.update_entity("JobSubmission", bh_application_payload, use_retry_with_exception=True)

    def handle_add_application(self, event_context):
        application =  event_context.get('application')
        if not application and event_context.get('candidate', {}).get('applications'):
            application = event_context.get('candidate', {}).get('applications')[0]
        if not application:
            err_str = f"No application found in handle_add_application method for {event_context}"
            raise NonRetryableException(err_str)

        candidate_id = event_context.get('candidate_id')
        if not candidate_id:
           candidate_id = application.get('candidate_id')
        if not candidate_id:
            err_str = f"No candidate_id found anywhere in handle_add_application for {event_context}"
            raise NonRetryableException(err_str)
    
        candidate_info= {"id":int(candidate_id)}
        
        bh_application_payload = {}
        bh_application_payload["candidate"] = candidate_info

        if application.get("application_ts"):
            bh_application_payload["dateAdded"] = application["application_ts"] * 1000
        else:
            bh_application_payload["dateAdded"] = int(time.time()*1000) 
            
        if application.get('last_modified_ts'): 
            bh_application_payload["dateLastModified"] = application["last_modified_ts"] * 1000
        else:
            bh_application_payload["dateLastModified"] = int(time.time()*1000)
        
        ef_current_stage = application["current_stage"]      
        if ef_current_stage:
            bh_application_payload["status"] = ef_current_stage.get("stage")
        else:
            bh_application_payload["status"] = ""
        
        bh_application_payload["source"] = "Eightfold API user"

        if event_context.get("comment"):
            bh_application_payload["comments"] = event_context.get("comment")

        job_id = None
        if event_context.get("job_id"):
            job_id = event_context.get("job_id")
            bh_application_payload["jobOrder"] = {"id": int(event_context.get("job_id"))}
        elif 'jobs' in application:
            jobs = application.get('jobs')
            if len(jobs) > 1:
                err_str = f"Multiple jobs found for handle_add_application : {candidate_id}"
                raise NonRetryableException(err_str)
            job = jobs[0]
            job_id  = job[0]
            bh_application_payload["jobOrder"] = {"id": int(job_id)}
        else:
            err_str = f" No job_id found anywhere in handle_add_application for {candidate_id}"
            raise NonRetryableException(err_str)

        # Check whether an application is already created with this pair of candidate and job to avoid duplication
        bullhorn_data = self.bh.get_entity_data('Candidate', candidate_id, CANDIDATE_FIELDS)
        applications_from_ef =  dict()
        if bullhorn_data['data'].get('customTextBlock1'):
            applications_from_ef = json.loads(bullhorn_data['data']['customTextBlock1'])
            application_id = applications_from_ef.get(job_id)
            if application_id:
                err_str = f"An application with application id: {application_id} for candidate id: {candidate_id} and job id: {job_id} is already created from eightfold"
                self.app_sdk.log(err_str)
                return None

        if "ats_action_user" in event_context and event_context['ats_action_user']['email'] != "":
            added_by_email = event_context['ats_action_user']['email']
            corporate_user = self.bh.search_entity(entity_type="CorporateUser",
                                                    search=f"externalEmail='{added_by_email}' OR email='{added_by_email}'", use_retry_with_exception=True)
            if len(corporate_user['data']) > 0:
                self.app_sdk.log("Adding sendingUserV2")
                bh_application_payload["sendingUser"] = {"id": corporate_user['data'][0]['id']}

        resp = self.bh.create_entity("JobSubmission", bh_application_payload, use_retry_with_exception=True)

        # Update customTextBlock1 in BH candidate data that application has been added for this pair of candidate and job to avoid duplicate applications
        bh_request = dict()
        bh_request['id'] = candidate_id
        applications_from_ef[job_id] = resp.get('changedEntityId')
        bh_request['customTextBlock1'] = json.dumps(applications_from_ef)
        resp = self.bh.update_entity('Candidate', bh_request)
        
        # Sync back add application to EF immediately
        time.sleep(2)
        request_data = {"event":["Candidate",candidate_id,"UPDATED",[]],"trigger_name":"app_notify"}
        self.process_bh_event(request_data["event"], request_data)
        return resp

    def handle_add_candidate_note(self, event_context):
        candidate_id = event_context['candidate_id']

        note = event_context['note']

        bh_note = {}
        if note.get('creation_ts'):
            bh_note["dateAdded"] = int(note.get('creation_ts')*1000)

        if note.get("body"):
            bh_note["comments"] = note.get("body") # TODO what to map comments to ?  note['body'] ?

        if note.get('note_type'):
            bh_note["action"] = note.get("note_type")
        
        candidate_info = {"id":int(candidate_id)}
        bh_note["personReference"] = candidate_info
        bh_note["candidates"] = [candidate_info]
        
        sender_email = note.get('sender')
        if sender_email and str(sender_email).find("@"):
                corp_user = self.bh.search_entity(entity_type="CorporateUser",
                              search=f"externalEmail='{sender_email}' OR email='{sender_email}'", use_retry_with_exception=True)
                if len(corp_user['data']) > 0:
                    bh_note["commentingPerson"] = {
                        "id": corp_user['data'][0]['id']
                    }
        elif sender_email:
                corp_user = self.bh.search_entity(entity_type="CorporateUser",
                                               search=f"firstName='{sender_email}'", use_retry_with_exception=True)
                if len(corp_user['data']) > 0:
                    bh_note["commentingPerson"] = {
                        "id": corp_user['data'][0]['id']
                    }

        # simply add the new note to BH
        return self.bh.create_notes_data([bh_note])
    
    def check_existing_candidate_in_bh_using_ef_customInfo(self, data_from_ef_api):
        synced_ats_id = data_from_ef_api["customInfo"].get("efcustom_text_bullhorn_id", "") if data_from_ef_api.get("customInfo") else ""
        if synced_ats_id:
            self.app_sdk.log("Candidate is already present in BH, Bullhorn id present in custom Info of EF profile")
            return True
        return False
    
    def check_existing_candidate_in_bh_using_candidate_id(self, candidate_id):
        try: 
            if candidate_id:
                is_bh_candidate = self.is_candidate_in_bh(candidate_id)
                if is_bh_candidate: 
                    self.app_sdk.log("A profile with same candidate id already exists in BH")
                    return True
        except Exception as ex:       
            self.app_sdk.log(f"Transient error while trying to check for existing candidate in BullHorn using candidate id, traceback { traceback.format_exc() } ")
            raise RetryableException(str(ex)) 
        return False
    
    def existing_candidate_in_bh_using_bh_customText1_and_ef_email(self, data_from_ef_api):
        emails =  data_from_ef_api.get('email')
        if emails:
            emails_list = [email.strip() for email in emails.split(',')]
            try:
                for email in emails_list:
                    submission_query_string = {'query': 'email:{}'.format(email)}
                    candidate_list_dict = self.bh.search_entity_post(entity_type="Candidate", search=submission_query_string, fields="id,email,customText1")
                    candidates_list = candidate_list_dict.get('data', [])
                    for candidate in candidates_list:
                        if candidate.get('customText1') == data_from_ef_api.get('id'):
                            self.app_sdk.log("Candidate is already present in BH, customText1 contains same profile Id")
                            return candidate
            except NonRetryableException as ex:
                error_string = f"NonRetryableException while trying to check for existing candidate in BullHorn using BH customText1 and ef email, traceback { traceback.format_exc() }" 
                self.app_sdk.log(error_string)
                raise NonRetryableException(error_string)
            except Exception as ex:
                error_string = f"Retryable/Unknown exception while trying to check for existing candidate in BullHorn using BH customText1 and ef email, traceback: {traceback.format_exc()}"
                self.app_sdk.log(error_string)
                raise RetryableException(error_string) 
        return False
    
    def check_existing_candidate_in_bh(self, data_from_ef_api, candidate_id):
        # Case 1: Check existing candidate in BH on the basis of efcustom_text_bullhorn_id in customInfo of ef profile data
        if self.check_existing_candidate_in_bh_using_ef_customInfo(data_from_ef_api): return True
        # Case 2: Check existing candidate in BH from ats_candidate_id directly
        if self.check_existing_candidate_in_bh_using_candidate_id(candidate_id): return True
        # Case 3: Check existing candidate in BH based on ef email and customtext1 of BH profile
        if self.existing_candidate_in_bh_using_bh_customText1_and_ef_email(data_from_ef_api): return True
        return False
    
    def should_create_application(self, event_context):
        application =  event_context.get('application')
        if not application and event_context.get('candidate', {}).get('applications'):
            application = event_context.get('candidate', {}).get('applications')[0]
        if application: 
            return True
        else:
            return False
        
    def handle_add_candidate(self, event_context):
        profile_id = event_context.get('profile_id')
        candidate_id =  event_context.get('candidate_id')
        # Get ef profile data from profile_id
        try:
            data_from_ef_api = self.ef.get_ef_data_candidate_profile(profile_id, use_retry_with_exception=True)
            profile_id_from_ef = data_from_ef_api.get('id', False)
        except Exception as ex:
            traceback.print_exc()
            profile_id_from_ef = False
        finally:
            if not profile_id_from_ef:
                self.app_sdk.log("Candidate Not found in EF")
                raise RetryableException(f"Candidate Not found in EF, traceback : { traceback.format_exc() } ") 
        
        if data_from_ef_api.get("email") == "":
            self.app_sdk.log("Candidate Email is empty")
            return None

        valid_emails = get_valid_emails(data_from_ef_api.get('email'))
        if valid_emails == "":
            self.app_sdk.log("Candidate does not have a valid email")
            return None
        data_from_ef_api['email'] = valid_emails

        if self.check_existing_candidate_in_bh(data_from_ef_api, candidate_id):
            if self.should_create_application(event_context):
                try:
                    resp = self.handle_add_application(event_context)
                except NonRetryableException as ex:
                    raise ex
                except Exception as ex:
                    raise RetryableException(f"Could not add application to candidate. Retry in sometime, traceback : {traceback.format_exc()} ") 
            return None
    
        # Again do the above checks to ensure we don't create a duplicate profiles in BH
        time.sleep(25)
        
        if self.check_existing_candidate_in_bh(data_from_ef_api, candidate_id):
            if self.should_create_application(event_context):
                try:
                    resp = self.handle_add_application(event_context)
                except NonRetryableException as ex:
                    raise ex
                except Exception as ex:
                    raise RetryableException(f"Could not add application to candidate. Retry in sometime, traceback : {traceback.format_exc()} ") 
            return None
        
        bh_request = self.bh.create_bh_request_dict(data_from_ef_api, candidate_id)
        
        skills_list = data_from_ef_api.get("skills")
        education = data_from_ef_api.get("education")
        experience = data_from_ef_api.get("experiences")
        notes_info = data_from_ef_api.get("notes")
        raw_file_content = None
        resume_file_name = None
        skills_list = data_from_ef_api.get("skills")
        if skills_list:
            skills_dict = self.process_skills_object(skills_list)
            if skills_dict:
                bh_request["primarySkills"] = skills_dict
                
                
        if data_from_ef_api.get("resumeFileName"):
            raw_file_content = data_from_ef_api.get("resume") if "resume" in data_from_ef_api else data_from_ef_api.get("resumeContent")
            resume_file_name = data_from_ef_api.get("resumeFileName")
            
        bh_request.pop('id')
        updated = data_from_ef_api.get("lastUpdated", False)
        bh_request['customDate1'] = updated*1000 if updated else None
        bh_request['customText1'] = profile_id_from_ef
        candidate_response = self.bh.create_entity("Candidate", bh_request, use_retry_with_exception=True)
        if candidate_response:
            self.app_sdk.log("Candidate Created in BH")
            entity_id = candidate_response["changedEntityId"]
        else:
            # There can be case when candidate response in None but BH profile is created
            candidate_in_bh = self.existing_candidate_in_bh_using_bh_customText1_and_ef_email(data_from_ef_api)
            if candidate_in_bh:
                entity_id = candidate_in_bh["id"]
                self.app_sdk.log(f"Candidate Created in BH with candidate_id : {entity_id}")
            else:
                self.app_sdk.log("Failed to create a profile in BH")
                raise RetryableException("Failed to create a profile in BH") 
        
        # Update custom info of in EF profile
        ef_patch_payload = {"customInfo": {"efcustom_text_bullhorn_id": entity_id}}
        try:
            result = self.ef.update_ef_profile(profile_id, ef_patch_payload, use_retry_with_exception=True)
        except Exception as ex:
            self.app_sdk.log(f"Failed to save BH id in ef profile customInfo, traceback: { traceback.format_exc() }")
        
        # Save other fields like education, experience, resume etc for BH candidate
        try:
            candidate_info = {"id": entity_id}
            education_list = self.bh.process_education_data(education, candidate_info) if education else []
            experience_list = self.bh.process_experience_data(experience, candidate_info) if experience else []
            notes_info_list = self.bh.process_notes_data(notes_info, candidate_info) if notes_info else []

            if education_list:
                education_data = self.bh.create_education_data(education_list)
            if experience_list:
                experience_data = self.bh.create_experience_data(experience_list)
            if notes_info_list:
                notes_data = self.bh.create_notes_data(notes_info_list)

            if resume_file_name and raw_file_content:
                self.create_file_bh(resume_file_name, raw_file_content, entity_id)
        except Exception as ex:
            self.app_sdk.log(f"Failed to save some field like education, experience, resume etc for candidate_id : {entity_id}, traceback : {traceback.format_exc()} ")
            
        # Add application to the candidate if required
        try:
            if self.should_create_application(event_context):
                event_context['candidate_id'] = entity_id
                resp = self.handle_add_application(event_context)
        except Exception as ex:
            self.app_sdk.log(f"Failed to add application for candidate_id : {entity_id} , traceback : { traceback.format_exc() } ")
        
        # Create P2 in EF immediately
        try:
            bullhorn_data = self.bh.get_entity_data('Candidate', entity_id, CANDIDATE_FIELDS, use_retry_with_exception=True)
            self.bh_data = bullhorn_data["data"]
            ef_data = self.ef.get_ats_candidate(entity_id, use_retry_with_exception=True)
            
            if ef_data:
                self.app_sdk.log(f"P2 was already available for entity_id : {entity_id} " )
                return
            
            # Repeating the steps done in process bh event for candidate creation in ef from bh data
            mapped_data = self.map_candidate_all_fields('Candidate', entity_id)
            last_activity = mapped_data["lastActivityTs"]
            mapped_data["lastActivityTs"] = round(last_activity/1000)
            if "firstName" not in mapped_data:
                mapped_data["firstName"] = " "

            self.ef.create_ef(mapped_data, 'Candidate', use_retry_with_exception=True)
        except Exception as ex:
            self.app_sdk.log(f"Failed to create P2 in EF for candidate_create for entity_id : {entity_id} and exception : {ex.args}, traceback : { traceback.format_exc() } ")

        return candidate_response
    
    
    def handle_update_candidate(self, event_context):
        # make BH request using update_spec, candidate_id and using EF app sdk
        candidate_id = event_context['candidate_id']
        profile_id = event_context['profile_id']
        update_spec = event_context['update_spec']
        
        bh_request = {}
        bh_request['id'] = candidate_id
        fullName = None

        for spec in update_spec:            
            if spec['section_name'] == 'firstName':
                bh_request['firstName'] = spec['section_item']

                #since we dont know the order in which spec might come
                if not fullName:
                    fullName = bh_request['firstName']
                else:
                    fullName =  bh_request['firstName'] + fullName

            if spec['section_name'] == 'lastName':
                bh_request['lastName'] = spec['section_item']
                if fullName:
                    fullName = fullName + bh_request['lastName']
                else:
                    fullName = bh_request['lastName']

            if spec['section_name'] == 'title':
                bh_request['occupation'] = spec['section_item']

            # {'section_name': 'emails', 'section_item': 'email1,email2,email3'}
            if spec['section_name'] == 'emails':
                # list of comma separated emails.
                email_list = spec['section_item'].split(",")
                if len(email_list) > 0:
                    bh_request['email'] = email_list[0]
                if len(email_list) > 1:
                    bh_request['email2'] = email_list[1]
                if len(email_list) > 2:
                    bh_request['email3'] = email_list[2]

            # {'section_name': 'phones', 'section_item': '1234567890,2345678231'} #need to raise this issue
            if spec['section_name'] == 'phones':
                bh_request['mobile'] = spec['section_item']


            #  {"section_name": "gender","section_item": "male"}
            #  {'section_name': 'gender', 'section_item': 'none'
            if spec['section_name'] == 'gender':
                if spec['section_item'] == 'none':
                    bh_request['gender'] = "U" #unknown 
                else:
                    bh_request['gender'] = spec['section_item'][0].upper() # "M" , "F"
            
            # {'section_name': 'location', 'section_item': 'India'}
            # mappping countryID if its in location and has entry present
            if spec['section_name'] == 'location':
                if spec['section_item'] in country_ids.keys():
                    mapped_country_id  = country_ids[spec['section_item']] 
                    bh_request['address'] = {}
                    bh_request['address']['countryID'] = mapped_country_id

            #[{'section_name': 'skills', 'section_item': ['Branch', 'C++', 'Python', 'Customer Support']}]
            # all skills removed[{'section_name': 'skills', 'section_item': ['']}]
            if spec['section_name'] == 'skills':
                skills_list = spec['section_item']
                skills_dict = self.process_skills_object(skills_list) #this replaces all skills in BH with all skills in EF
                if skills_dict:
                    bh_request["primarySkills"] = skills_dict
            
            # Context : for nested fields we delete all entries in Bh and create new entries from update_spec data
            if spec['section_name'] == 'education':
                self.delete_and_create_education_in_bullhorn(spec['all_section_items'] , candidate_id)

            if spec['section_name'] == 'experience':
                self.delete_and_create_experience_in_bullhorn(spec['all_section_items'] , candidate_id)

            # [{'section_name': 'resume_filename', 'section_item': 'Linn Zayar-EqgPjZM07.pdf'}]
            if spec['section_name'] == 'resume_filename':
                self.delete_and_create_resume_in_bullhorn(spec['section_item'] , candidate_id, profile_id)

        if fullName:
            bh_request['name'] = fullName

        if len(bh_request.keys()) == 1 and 'id' in bh_request.keys():
            #ie update spec had nested fields and have been already handled
            return

        resp = self.bh.update_entity('Candidate', bh_request, use_retry_with_exception=True)
        return resp

    def handle_fetch_candidate(self, event_context):
        entity_id = event_context.get('candidate_id')
        try:
            bullhorn_data = self.bh.get_entity_data('Candidate', entity_id, CANDIDATE_FIELDS, use_retry_with_exception=True)
        except Exception as ex:
            # return None if candidate is not present in BH otherwise raise Exception
            if str(ex).find('status_code: 404') !=-1 or str(ex).find('"errorCode":404') !=-1:
                self.app_sdk.log(f"Candidate with candidate id {entity_id} not found in BH")
                raise NonRetryableException(f"Candidate with candidate id {entity_id} not found in BH")
            self.app_sdk.log(f"Transient error while trying to check for candidate with {entity_id} in BullHorn, retry in sometime")
            raise RetryableException("Transient error while trying to check for candidate in BullHorn, retry in sometime")
        self.bh_data = bullhorn_data["data"]
        mapped_data = self.map_candidate_all_fields('Candidate', entity_id)
        last_activity = mapped_data["lastActivityTs"]
        mapped_data["lastActivityTs"] = round(last_activity/1000)
        if "firstName" not in mapped_data:
            mapped_data["firstName"] = " "
        return mapped_data

    def handle_ats_adapter_integration(self, request_data):

        event_context = request_data.get('eventContext')
        operation = request_data.get('eventType')
        
        # TODO what if candidate does not exists in BH ?

        if operation == 'update_candidate':
            return self.handle_update_candidate(event_context)
        elif operation == 'add_candidate_note':
            return self.handle_add_candidate_note(event_context)
        elif operation == 'add_candidate':
            return self.handle_add_candidate(event_context)
        elif operation == 'add_application':
            return self.handle_add_application(event_context)    
        elif operation == 'change_appl_stage':
            return self.handle_change_application_stage(event_context)    
        elif operation == 'fetch_candidate':
            return self.handle_fetch_candidate(event_context)
        else:
            err_str = f" Operation : {operation} is not supported yet"
            raise NonRetryableException(err_str) 


    def handle_create_candidate(self, trigger_name, req_data): # ONLY candidate_create + 1 case of update_candidate 
        candidate_in_bh = False
        updated = req_data.get("lastUpdated", False)
        
        candidate_ats_id = req_data.get("atsEntityId")
        profile_id = req_data.get("id")
        synced_ats_id = req_data["customInfo"].get("efcustom_text_bullhorn_id", "") if req_data.get("customInfo") else ""
            
        is_bh_candidate = None  
        
        try: 
            if candidate_ats_id:
                is_bh_candidate = self.is_candidate_in_bh(candidate_ats_id)
        except Exception as ex:
            retry_time = 25
            if req_data.get("retry_count", 0) < MAX_RETRY_COUNT_EXISTING_CHECK:
                self.app_sdk.log(f"Transient error while trying to check for existing candidate in BullHorn, retry in {retry_time}")
                ret_data = create_ret_data_internal_trigger(retry_time, trigger_name, req_data)
                return ret_data
            self.app_sdk.log(f"is_candidate_in_bh exception, Retried 3 times to check for exsiting candidate in BullHorn but got an exception : {str(ex)} ")
            raise NonRetryableException(f"is_candidate_in_bh exception, Retried 3 times to check for exsiting candidate in BullHorn but got an exception : {str(ex)} ")

        try:
            if self.existing_candidate_in_bh_using_bh_customText1_and_ef_email(req_data):
                is_bh_candidate = True
        except Exception as ex:
            retry_time = 25
            if req_data.get("retry_count", 0) < MAX_RETRY_COUNT_EXISTING_CHECK:
                self.app_sdk.log(f"Transient error while trying to check for existing candidate in BullHorn, retry in {retry_time}")
                ret_data = create_ret_data_internal_trigger(retry_time, trigger_name, req_data)
                return ret_data
            self.app_sdk.log(f"existing_candidate_in_bh_using_bh_customText1_and_ef_email exception, Retried 3 times to check for exsiting candidate in BullHorn but got an exception : {str(ex)} ")
            raise ex
        
        if synced_ats_id or is_bh_candidate:
            candidate_in_bh = True

        '''
        Primary focus: Avoid process profile without emails or a create event when the profile was already created
        Context: Only profiles with emails are inside the scope of this integration.
        '''
        if candidate_in_bh:
            self.app_sdk.log(f"There is a profile in BH with the profile id saved inside a custom field")
            return None

        if req_data.get("email") == "":
            self.app_sdk.log("Candidate Email is empty")
            return None
        
        valid_emails = get_valid_emails(req_data.get('email'))
        if valid_emails == "":
            self.app_sdk.log("Candidate does not have a valid email")
            return None
        req_data['email'] = valid_emails
        '''
        Primary focus: Set up a BH Profile object and others BH entities / variables
        Context: -
        Comment: Setting skills to empty until we get fix from EF
        '''
        entity_id = synced_ats_id if synced_ats_id else candidate_ats_id
        bh_request = self.bh.create_bh_request_dict(req_data, entity_id)

        skills_list = req_data.get("skills")
        education = req_data.get("education")
        experience = req_data.get("experiences")
        notes_info = req_data.get("notes")
        raw_file_content = None
        resume_file_name = None
        if skills_list:
            skills_dict = self.process_skills_object(skills_list)
            if skills_dict:
                bh_request["primarySkills"] = skills_dict

        '''
        Primary focus: Retrieve data from EF and check if the profile is available
        Context: Due to that any event can create a profile in BH, we retrieve the data from EF
        '''
        try:
            data_from_ef_api = self.ef.get_ef_data_candidate_profile(profile_id, use_retry_with_exception=True)
            profile_id_from_ef = data_from_ef_api.get('id', False)
        except Exception as ex:
            traceback.print_exc()
            profile_id_from_ef = False
        finally:
            if not profile_id_from_ef:
                retry_time = 25
                self.app_sdk.log(f"Candidate not found in EF, retry in {retry_time}")
                ret_data = None
                if req_data.get("retry_count", 0) < MAX_RETRY_COUNT:
                    ret_data = create_ret_data_internal_trigger(retry_time, trigger_name, req_data)
                return ret_data

        '''
        Primary focus: Set up resume variables
        Context:
        '''
        if req_data.get("resumeFileName"):
            raw_file_content = data_from_ef_api.get("resume") if "resume" in data_from_ef_api else data_from_ef_api.get("resumeContent")
            resume_file_name = data_from_ef_api.get("resumeFileName")

        '''
        Primary focus: Last check before create the profile in BH. If there is not a profile in BH, we create it and save BH id inside the profile
        Context: In this point we checked BH system and EF payload.
            Could happen that other event create the profile and there is the BH Id inside the custom info that we retrieve

        '''
        if not candidate_in_bh and data_from_ef_api.get("customInfo").get("efcustom_text_bullhorn_id", ""):
            self.app_sdk.log("Candidate Already created by other event")
            entity_id = data_from_ef_api.get("customInfo").get("efcustom_text_bullhorn_id", "")
        elif not candidate_in_bh:
            bh_request.pop('id')
            bh_request['customDate1'] = updated*1000 if updated else None
            bh_request['customText1'] = profile_id_from_ef
            candidate_response = self.bh.create_entity("Candidate", bh_request, use_retry_with_exception=True)
            if candidate_response:
                self.app_sdk.log("Candidate Created in BH")
                entity_id = candidate_response["changedEntityId"]
            else:
                # There can be case when candidate response in None but BH profile is created
                candidate_in_bh = self.existing_candidate_in_bh_using_bh_customText1_and_ef_email(data_from_ef_api)
                if candidate_in_bh:
                    entity_id = candidate_in_bh.get("id")
                    self.app_sdk.log(f"Candidate Created in BH with candidate_id {entity_id}")
                else:
                    retry_time = 25
                    self.app_sdk.log(f"Failed to create a profile in BH, retry in {retry_time}")
                    ret_data = None
                    if req_data.get("retry_count", 0) < MAX_RETRY_COUNT:
                        ret_data = create_ret_data_internal_trigger(retry_time, trigger_name, req_data)
                    return ret_data

            ef_patch_payload = {"customInfo": {"efcustom_text_bullhorn_id": entity_id}}
            try:
                result = self.ef.update_ef_profile(profile_id, ef_patch_payload, use_retry_with_exception=True)
            except Exception as ex:
                self.app_sdk.log(f"Failed to save BH id in EF, traceback : { traceback.format_exc() }")
            
            try:
                data_from_ef_api = self.ef.get_ef_data_candidate_profile(profile_id, use_retry_with_exception=True)
                skills_list = data_from_ef_api.get("skills")
                education = data_from_ef_api.get("education")
                experience = data_from_ef_api.get("experiences")
                notes_info = data_from_ef_api.get("notes")
                raw_file_content = data_from_ef_api.get("resume") if "resume" in data_from_ef_api else data_from_ef_api.get("resumeContent")
                resume_file_name = data_from_ef_api.get("resumeFileName")

                # Many to Many fields
                candidate_info = {"id": entity_id}
                education_list = self.bh.process_education_data(education, candidate_info) if education else []
                experience_list = self.bh.process_experience_data(experience, candidate_info) if experience else []
                notes_info_list = self.bh.process_notes_data(notes_info, candidate_info) if notes_info else []

                if education_list:
                    education_data = self.bh.create_education_data(education_list)
                if experience_list:
                    experience_data = self.bh.create_experience_data(experience_list)
                if notes_info_list:
                    notes_data = self.bh.create_notes_data(notes_info_list)

                if resume_file_name and raw_file_content:
                    self.create_file_bh(resume_file_name, raw_file_content, entity_id)
            except Exception as ex:
                self.app_sdk.log(f"Failed to save some field like education, experience, resume etc for candidate_id : {entity_id} , traceback : { traceback.format_exc() } " )

            # Create P2 in EF immediately
            try:
                bullhorn_data = self.bh.get_entity_data('Candidate', entity_id, CANDIDATE_FIELDS, use_retry_with_exception=True)
                self.bh_data = bullhorn_data["data"]
                ef_data = self.ef.get_ats_candidate(entity_id, use_retry_with_exception=True)
                
                if ef_data:
                    self.app_sdk.log(f"P2 was already available for entity_id : {entity_id} " )
                    return
                
                # Repeating the steps done in process bh event for candidate creation in ef from bh data
                mapped_data = self.map_candidate_all_fields('Candidate', entity_id)
                last_activity = mapped_data["lastActivityTs"]
                mapped_data["lastActivityTs"] = round(last_activity/1000)
                if "firstName" not in mapped_data:
                    mapped_data["firstName"] = " "

                self.ef.create_ef(mapped_data, 'Candidate', use_retry_with_exception=True)
            except Exception as ex:
                self.app_sdk.log(f"Failed to create P2 in EF for candidate_create for entity_id : {entity_id} and exception : {ex.args} , traceback : { traceback.format_exc() } ")

            return candidate_info

def is_valid_email_address(email):
    return email and re.match(r'[^@\s]+@[^@\s]+\.[^@\s]+', email.strip())

# returns comma separated valid emails string from a set of comma separated emails
def get_valid_emails(emails):
    emails = emails.split(',')
    valid_emails = ""
    for email in emails:
        if is_valid_email_address(email):
            if valid_emails != "":
                valid_emails += ","
            valid_emails += email
    return valid_emails

def create_ret_data_internal_trigger(time_delay, trigger_name, req_data):
    """
    Create schedule_app_notification action with the given request data but with additional time delay.
    Here we capture the count of re-tries with each trigger and limit this count to MAX_RETY_COUNT.
    Raises an exception when the retry limit is exhausted
    :param time_delay: time to replay the trigger
    :param trigger_name: current trigger name, will be populated as internal_trigger during replay.
    :param req_data: Original request data with the input trigger
    :return: scheduled_app_notification actions
    """
    ret_data = {
        "actions": []
    }

    req_data["internal_trigger"] = trigger_name
    req_data["retry_count"] = req_data.get("retry_count", 0) + 1
    if req_data.get("retry_count") == MAX_RETRY_COUNT:
        raise Exception(f"Retry limit exhausted for trigger {trigger_name} and req_data : {req_data} ")
    req_data["trigger_name"] = "app_notify"
    action = {
        'action_name': 'schedule_app_notification',
        'request_data': {
            "schedule_after_secs": time_delay,
            "notification_payload": req_data
        }}

    ret_data["actions"].append(action)
    return ret_data

def eligible_for_BH_create(app_sdk, req_data):
    ef_candidate_id = req_data.get('id')
    pre_data = req_data.get("previous", False)
    previous_data = json.loads(pre_data) if pre_data and type(pre_data) == str else pre_data
    previous_email = previous_data.get("email")
    current_email  = req_data.get("email")
    previous_email = get_valid_emails(previous_email)
    current_email  = get_valid_emails(current_email)
    if previous_email == "" and current_email:
        app_sdk.log(f"Allowing candidate creation for special case of manual email addition for ef_candidate_id : {ef_candidate_id} ")
        return True
    return False

def app_handler(event, context):
    app_sdk = EFAppSDK(context)
    app_sdk.log('Starting App Invocation')

    """
    This method is triggered with the lambda function. Further specific function is invoked from here based on trigger.
    :param event: Contains request data and app settings needed for the app
    :param context: Context related to the app. Can be None
    :return:
    """
    app_settings = event.get('app_settings', {})
    event_context = event.get('context')
    system_id = event_context['system_id']
    app_settings["system_id"] = system_id
    
    sync_adapter = None
    data = None

    req_data = event.get('request_data', {})
    
    trigger_name = req_data.get('trigger_name') if req_data.get('trigger_name') else event.get("trigger_name")

    if "internal_trigger" in req_data:
        trigger_name = req_data["internal_trigger"]

    app_sdk.log('Call received for trigger_name: {}'.format(trigger_name))

    if trigger_name == 'candidate_update' and not eligible_for_BH_create(app_sdk, req_data):
        app_sdk.log("Skipping candidate update")
        return None

    try:
        try:
            sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        except Exception as ex:
            app_sdk.log("Error in generating the Bullhorn Rest Token and Rest URL")
            app_sdk.log(str(ex))
            if trigger_name == 'ats_adapter_integration':
                err_str = f"Error in generating the Bullhorn Rest Token and Rest URL with exception : {str(ex)}"
                raise RetryableException(err_str)
            if req_data.get("retry_count", 0) < MAX_RETRY_COUNT:
                data = create_ret_data_internal_trigger(100, trigger_name, req_data)

        if sync_adapter:
            if trigger_name == 'candidate_create' or trigger_name == 'candidate_update' :
                try:                   
                    data = sync_adapter.handle_create_candidate(trigger_name, req_data)
                except (NonRetryableException, RetryableException) as ex:
                    '''
                    DB level triggers should either raise a 500 error if failed (ie they should not throw NonRetryable/Retryable exceptions), because these
                    exceptions make sense only for write back level triger like ats_adapter_integration.
                    Also, this function is called in app_notify when a first invocation to candidate_create/candidate_update failed and it was added to be retried
                    using app_notify.

                    This code will simply transform any of the above 2 exceptions raised into Exception
                    '''
                    raise Exception from ex

            elif trigger_name == 'post_install':
                sync_adapter.start_event_subscription()

            elif trigger_name == "scheduled_hourly":
                try:
                    data = sync_adapter.get_subscription_events()
                except (NonRetryableException, RetryableException) as ex:
                    '''
                    DB level triggers should either raise a 500 error if failed (ie they should not throw NonRetryable/Retryable exceptions), because these
                    exceptions make sense only for write back level triger like ats_adapter_integration.
                    '''
                    raise Exception from ex

            elif trigger_name == "ats_adapter_integration":
                data = sync_adapter.handle_ats_adapter_integration(req_data)
                
            elif trigger_name == "app_notify":
                event_payload = req_data.get("event")
                if event_payload:
                    data = sync_adapter.process_bh_event(event_payload, req_data)
    except RetryableException as ex:
        err_str = f"Handler for trigger_name: {trigger_name} failed with Retryable error: { traceback.format_exc() }"
        app_sdk.log(err_str)
        return {
            'statusCode': 200,
            'body': json.dumps({'error': err_str}),
            'retryStatus':'FAIL_RETRY_OK'
        }
    except NonRetryableException as ex:
        err_str = f'Handler for trigger_name: {trigger_name} failed with Non Retryable error: { traceback.format_exc() }'
        app_sdk.log(err_str)
        return {
            'statusCode': 200,
            'body': json.dumps({'error': err_str}),
            'retryStatus':'FAIL_NO_RETRY'
        }
    except Exception as ex:
        err_str = f'Handler for trigger_name: {trigger_name} failed with error: { traceback.format_exc() }'
        app_sdk.log(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': err_str})
        }
    app_sdk.log(data)
    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }


if __name__ == "__main__":
    # If running in local use Mocking.
    import mock_context
    ctxt = mock_context.get_context("Test Mock", "1.2.0")
    import time
    start = time.time()
    env = "Sandbox"
    if env == "Sandbox":
        event = {"request_data":{"event":["Candidate",2905828,"UPDATED",[]],"trigger_name":"app_notify"},
                # "trigger_name": "post_install", # this is needed if we don't pass trigger_name in request_data
                 "context": {"system_id": "PK-BullHorn-EntitySync"},
                 "app_settings": {
                    "subscription_id": "test", 
                    "Authorization": "SET EF AUTHORIZATION KEY HERE",  # PK SANDBOX
                    "Content-Type": "application/json",
                    "client_id": "SET CLIENT ID HERE",
                    "client_secret": "SET CLIENT SECRET HERE",
                    "username": "SET BH USERNAME HERE",
                    "password": "SET BH PASSWORD HERE",
                    "redirect_uri": "https://eightfold.ai",
                    "system_id": "PK-BullHorn-EntitySync",
                    "auth_domain": "auth-west9" # For sandbox this datacenter is preferred

                }
                 }
    elif env == "PROD":
        event = {"request_data": {"event":["JobOrder",550630,"UPDATED",["status"]],"trigger_name":"app_notify"},
                 "trigger_name": "post_install",
                 "context": {"system_id": "PK-BullHorn-EntitySync"},
                 "app_settings": {
                     "subscription_id":"test", 
                     "Authorization": "SET EF AUTHORIZATION KEY HERE",  # PK PROD
                     "Content-Type": "application/json",
                     "client_id": "SET CLIENT ID HERE",
                     "client_secret": "SET CLIENT SECRET HERE",
                     "username": "SET BH USERNAME HERE",
                     "password": "SET BH PASSWORD HERE",
                     "redirect_uri": "https://eightfold.ai",
                     "system_id": "PK-BullHorn-EntitySync",
                     "auth_domain": "auth-apac" # For production this datacenter is preferred
                 }
                 }

    app_handler(event, ctxt)
    end = time.time()
    diff = end - start
    print("time difference %s" % str(diff))


