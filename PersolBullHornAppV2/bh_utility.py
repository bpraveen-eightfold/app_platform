'''
Code to parse sub-entities like education, experience etc.
@author: Sadashiva K, Abel Robra- Arjuna LLC
'''
import re

def get_query_for_id_list(id_list):
    event_batch_query_string = "id:"
    for id in id_list:
        event_batch_query_string = event_batch_query_string + str(id) + " "
    
    query = {"query": event_batch_query_string}
    return query

def get_query_string(id_list, param_type="id", next_page=False):
    """
    Prepare a query string that can be used with BH API calls
    :param id_list: BH IDs
    :param param_type: interested params for search
    :param next_page: if more data is needed in the api call
    :return: structured query string
    """
    if next_page:
        partial_string = f" AND {param_type} <> ".join(id_list)
        complete_string = f"{param_type} <> " + partial_string

    else:
        partial_string = f" OR {param_type} = ".join(id_list)
        complete_string = f"({param_type} = " + partial_string + ")"

    complete_string = re.sub(r"[^a-zA-Z0-9 =<>()\']", "", complete_string)
    return complete_string

def get_query_json(id_list, param_type="id"):
    """
    Create query string for BH API Call
    :param id_list: id's list for querying
    :param param_type: default to param -id
    :return: structured query string
    """
    all_ids = " ".join(id_list)
    query_dict = dict()
    query_dict["query"] = f"{param_type}:0 " + all_ids
    return query_dict

def process_education_data(edu_data):
    """
    Process education data and create payload that can be used in EF API calls
    :param edu_data: Education data from BH
    :return: education data list for EF
    """
    education_list = []
    for each_edu in edu_data["data"]:
        education_dict = dict()
        education_dict["degree"] = each_edu["degree"]
        education_dict["school"] = each_edu["school"]
        education_dict["startTs"] = round(each_edu["startDate"]/1000) if each_edu["startDate"] else 0
        education_dict["endTs"] = round(each_edu["endDate"]/1000) if each_edu["endDate"] else 0
        location = each_edu["city"]
        education_dict["location"] = location if location else ""
        education_dict["major"] = each_edu["major"]
        education_dict["description"] = each_edu["comments"]
        if education_dict["school"] or education_dict["degree"] or education_dict["major"]:
            education_list.append(education_dict)
    return education_list


def process_work_histories_data(work_histories):
    """
    Process Bullhorn WorkHistories and prepare experiences payload for EF
    :param work_histories: WorkHistories of a Candidate in BH
    :return: experience list of a candidate for EF
    """
    work_list = []
    for each_work in work_histories["data"]:
        work_history_dict = dict()
        work_history_dict["company"] = each_work["companyName"]
        work_history_dict["startTs"] = round(each_work["startDate"]/1000) if each_work["startDate"] else 0
        work_history_dict["title"] = each_work["title"]
        work_history_dict["description"] = each_work["comments"]
        work_history_dict["location"] = ""
        work_history_dict["endTs"] = round(each_work["endDate"]/1000) if each_work["endDate"] else 0
        work_history_dict["isCurrent"] = False  # Setting default value.
        work_history_dict["isInternal"] = False
        if work_history_dict["company"] or work_history_dict["title"] or work_history_dict["description"]:
            work_list.append(work_history_dict)
    return work_list


def process_skills_data(skills_data):
    """
    Pull out the skill name from all the BH skill objects
    :param skills_data: skills information from BH
    :return: list of skill names
    """
    skills_list = []
    for each_skill in skills_data["data"]:
        skills_list.append(each_skill["name"])
    return skills_list


def process_notes_data(notes_data):
    """
    Process notes of BH and create a new list of notes information that can be used in EF API Call
    :param notes_data: Notes information of a candidate from BH
    :return:  notes list that can be used to make EF API call
    """
    notes_list = []
    for note in notes_data["data"]:
        note_dict = dict()
        note_dict["cc"] = []
        note_dict["creationTs"] = round(note["dateAdded"]/1000) if note["dateAdded"] else 0
        note_dict["body"] = note["comments"]
        note_dict["sender"] = note["commentingPerson"]["firstName"]
        note_type = note["action"]
        if note_type not in ["email", "note", "other"]:
            note_dict["noteType"] = "other"
        else:
            note_dict["noteType"] = note_type
        note_dict["creator"] = note["commentingPerson"]["lastName"]
        notes_list.append(note_dict)
    return notes_list


