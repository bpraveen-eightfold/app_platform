# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependencies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import json
import traceback

import requests


def error_response(error_str):
    data = {'error': error_str}
    print(json.dumps(data))
    return {
        'statusCode': 500,
        'body': json.dumps(data)
    }


def str2bool(v):
    return str(v).lower() in ("yes", "true", "t", "1")


def del_resume(candidate_data):
    if candidate_data and candidate_data is not None:
        cd_copy = candidate_data.copy()
        if 'resume' in cd_copy:
            del cd_copy['resume']
    else:
        cd_copy = ""
    return cd_copy

def app_log(candidate_data, request_headers, url):
    cd_copy = del_resume(candidate_data)
    print(json.dumps(cd_copy))
    print('Headers: ', request_headers, 'WAND url : ', url)


def wand_put_call(pro_base_url, proxy_servers, request_headers, candidate_data, workerId):
    api_url_call = pro_base_url + '/candidates/' + workerId
    put_response = requests.put(api_url_call, proxies=proxy_servers, data=json.dumps(candidate_data),
                                headers=request_headers, verify=False)
    print('PUT call:', put_response, put_response.text)
    return put_response


def wand_post_call(pro_base_url, proxy_servers, request_headers, candidate_data):
    api_url_call = pro_base_url + '/candidates'
    post_response = requests.post(api_url_call, proxies=proxy_servers, data=json.dumps(candidate_data),
                                  headers=request_headers, verify=False)
    print('POST call:', post_response, post_response.text)
    return post_response


def entity_update_action(candidate_data, profile_enc_id, workerId):
    entity_action_data = {
        'candidate_data': candidate_data,
        'actions': [{
            'action_name': 'entity_update_action',
            'request_data': {
                'entity_type': 'candidate',
                'entity_id': profile_enc_id,
                'update_payload': {
                    'custom_info': {
                        'worker_id': workerId
                    }
                }
            }
        }]
    }
    return entity_action_data


def candidate_load(request_data, app_settings):
    firstName = request_data.get('firstName')
    lastName = request_data.get('lastName')
    atsEntityId = request_data.get('atsEntityId')
    email = request_data.get('email')
    skills = request_data.get('skills')
    # customFields = request_data.get('customFields')
    source = app_settings.get("source")
    title = request_data.get('title')
    positionId = ''
    candidateId = ''
    workerId = None

    # Fetching Resume
    ef_api_key = app_settings.get("ef_api_key")
    ef_get_candidate_url = app_settings.get("ef_get_candidate_url")
    profile_enc_id = request_data.get('id')

    ef_headers = {
        "Accept": "application/json",
        "Authorization": ef_api_key
    }

    url = ef_get_candidate_url + '/' + profile_enc_id
    candidate_response = requests.request("GET", url, headers=ef_headers, params={'include': 'resume'})

    if candidate_response.status_code !=200:
        raise Exception(candidate_response.json()) 

    candidate_response_json = candidate_response.json()

    resume = candidate_response_json['resume']
    email_load = candidate_response_json['email']
    customFields = candidate_response_json['customFields']
    education = candidate_response_json['education']
    tags = candidate_response_json['tags']
    location = candidate_response_json['location']
    phones = candidate_response_json['phone']
    experience = candidate_response_json['experience']
    summary = candidate_response_json['summary']
    race = candidate_response_json['race']
    urls = candidate_response_json['urls']
    notes = candidate_response_json['notes']
    awards = candidate_response_json['awards']
    gender = candidate_response_json['gender']
    highlights = candidate_response_json['highlights']
    imageUrl = candidate_response_json['imageUrl']
    industries = candidate_response_json['industries']
    candidateTitle = candidate_response_json['title']

    applications = request_data.get("applications")
    candidate_load_data = ''
    candidate_data = ''

    if applications:
        ats_application = []
        matchScore = []
        currentStage = ''
        application_source_type = ''

        # Track if candidate is wand sourced or if the candidate should be "send to wand"
        is_candidate_wand_sourced = False
        is_candidate_send_to_wand = False

        for application in applications:
            positionId = application['positionId']
            candidateId = application['candidateId']
            applicationTime = application['applicationTime']
            currentStage = application['currentStage']
            sourceType = application['sourceType']
            sourceName = application['sourceName']
            positionTitle = application['positionTitle']
            applicationStatus = application['applicationStatus']
            atsJobId = application['atsJobId']
            lastModifiedTime = application['lastModifiedTime']
            applicationId = application['applicationId']
            visaStatus = application['visaStatus']
            applicationAnswers = application['applicationAnswers']
            
            if not applicationAnswers:
                answer_data = [
                        {'answer': 'not answered by the candidate', 'questionId': None, 'question': 'Earliest_Availability'},
                        {'answer': 'not answered by the candidate', 'questionId': None, 'question': 'Desired_Hourly_Pay_Rate'},
                        {'answer': 'not answered by the candidate', 'questionId': None, 'question': 'I_have_worked_here_before_as_an_employee'},
                        {'answer': 'not answered by the candidate', 'questionId': None, 'question': 'I_have_worked_here_as_a_contractor_or_provided_services_through_a_third_party_supplier'},
                        {'answer': 'not answered by the candidate', 'questionId': None, 'question': 'I_have_a_family_member_who_works_here'}
                ]
                applicationAnswers = answer_data

            # wand sourcing is on the application thus making the application wand sourced
            # and the candidate also wand sourced. Strictly this is not a good definition of
            # wand sourced but it is a working definition
            is_application_wand_sourced = sourceName and sourceName.lower() == 'wand'
            is_candidate_wand_sourced = is_candidate_wand_sourced or is_application_wand_sourced

            # once a curator/recruiter pick an application to be send to wand we should also
            # consider the candidate to be "send to wand"
            is_application_send_to_wand = currentStage and currentStage.lower() == 'send to wand'
            is_candidate_send_to_wand = is_candidate_send_to_wand or is_application_send_to_wand
            
            # only if the application is wand sourced of application is "send to wand" we should add
            # to the application items
            if is_application_wand_sourced or is_application_send_to_wand:
                ats_item = {
                    'positionId': atsJobId,
                    'applicationTime': applicationTime,
                    'currentStage': currentStage,
                    'sourceType': sourceType,
                    'sourceName': sourceName,
                    'positionTitle': positionTitle,
                    'applicationStatus': applicationStatus,
                    'candidateId': candidateId,
                    'atsJobId': atsJobId,
                    'lastModifiedTime': lastModifiedTime,
                    'applicationId': applicationId,
                    'visaStatus': visaStatus,
                    'applicationAnswers': applicationAnswers
                }

                ats_application.append(ats_item)

                matchingScore = application['matchingData']

                if matchingScore is None or matchingScore == '':
                    print("No Matching Data found")
                else:
                    totalRelevantExperience = ''
                    totalRelevantSkills = ''
                    totalRelevanceScore = ''
                    matchScoreInsights = []

                    for score in matchingScore:
                        scoreType = score.get('scoreType')
                        # print(scoreType)
                        if scoreType == 'skill':
                            totalRelevantSkills = score.get('relevantScoreTypeVal')
                        elif scoreType == 'experience':
                            totalRelevantExperience = score.get('relevantScoreTypeVal')
                        elif scoreType == 'overall':
                            totalRelevanceScore = score['scoreRaw']

                        topMatch_item = {
                            "topMatches": score.get('topMatches'),
                            "score": score.get('score'),
                            "scoreRaw": score.get('scoreRaw'),
                            "scoreType": scoreType
                        }
                        matchScoreInsights.append(topMatch_item)

                    matchScore_item = {
                        "positionId": atsJobId,
                        "matchScore": {
                            "totalRelevantExperience": totalRelevantExperience,
                            "totalRelevantSkills": totalRelevantSkills,
                            "idealCandidatePercentage": '',
                            "totalRelevanceScore": totalRelevanceScore,
                            "matchScoreInsights": matchScoreInsights
                        }
                    }

                    matchScore.append(matchScore_item)

        candidate_data = {
            "id": profile_enc_id,
            "atsEntityId": atsEntityId,
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "title": candidateTitle,
            "skills": skills,
            "education": education,
            "experience": experience,
            "awards": awards,
            "summary": summary,
            'highlights': highlights,
            'imageUrl': imageUrl,
            'industries': industries,
            "race": race,
            "gender": gender,
            "phone": phones,
            "location": location,
            "notes": notes,
            "tags": tags,
            "urls": urls,
            "source": source,
            "applications": ats_application,
            "customFields": customFields,
            "resume": resume,
            "matchScoreDetails": matchScore
        }

        pro_base_url = app_settings.get("proul_base_url")
        api_key = app_settings.get("api_key")

        proxy_servers = app_settings.get("proxy_servers")

        request_headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }

        workerId = customFields.get('worker_id', '')
        print(f'WorkerId: {workerId}; Profile id: {profile_enc_id}; currentStage: {currentStage}')
        print(f'is_candidate_wand_sourced: {is_candidate_wand_sourced}; is_candidate_send_to_wand: {is_candidate_send_to_wand}')

        api_url_call = ''
        if is_candidate_wand_sourced:
            # Candidate is wand_sourced
            if workerId:
                api_url_call = pro_base_url + '/candidates/' + workerId
                #  and has a worked_id
                r = wand_put_call(pro_base_url, proxy_servers, request_headers, candidate_data, workerId)

                if r.status_code != 200:
                    raise Exception(r.json())

            else:
                print("Candidate profile id: " + profile_enc_id + " is wand sourced with no worker_id.")
        elif is_candidate_send_to_wand:
            # Candidate is "send to wand" i.e. one of the application is "send to wand"
            if not workerId:
                api_url_call = pro_base_url + '/candidates'
                # no workerId found therefore post to WAND
                r = wand_post_call(pro_base_url, proxy_servers, request_headers, candidate_data)
                
                if r.status_code != 200:
                    raise Exception(r.json())

                if r.status_code == 200:
                    customField = r.text
                    workerId = customField.split()[1].replace("#", "")
                    print('Profile id:', profile_enc_id, 'WorkerId:', workerId)

                    # Entity Update workerId
                    candidate_load_data = entity_update_action(candidate_data, profile_enc_id, workerId)
            else:
                # workerId found therefore put to WAND, this could be the case where the candidate is once again
                # being send to wand for a different application, it can also happen when the candidate is updated
                # after already been sent
                api_url_call = pro_base_url + '/candidates/' + workerId
                r = wand_put_call(pro_base_url, proxy_servers, request_headers, candidate_data, workerId)
    
                if r.status_code != 200:
                    raise Exception(r.json())
        else:
            print(
                "Candidate profile id: " + profile_enc_id + " did not meet criteria to be POST or PUT to WAND." + application_source_type,
                workerId, currentStage)

        app_log(candidate_data, request_headers, api_url_call)
    else:
        print('Candidate Applications cannot be empty')

    candidate_load_data = del_resume(candidate_data)

    return candidate_load_data


def candidate_update_handler(event, context):
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})

    candidate_data = candidate_load(request_data, app_settings)
    print("ProUL App invoked")

    data = candidate_data
    # print(data)

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }


def candidate_create_handler(event, context):
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})

    candidate_data = candidate_load(request_data, app_settings)
    print("ProUL App invoked")

    data = candidate_data
    # print(data)

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }


def app_handler(event, context):
    request_data = event.get('request_data', {})
    trigger_name = event.get("trigger_name")
    print('Trigger Name: ', trigger_name)
    # print('event: ', event)

    try:
        if trigger_name == 'candidate_create':
            return candidate_create_handler(event, context)
        elif trigger_name == 'candidate_update':
            return candidate_update_handler(event, context)
        else:
            return error_response("Unknown trigger.")

    except Exception as e:
        error_str = 'Something went wrong, traceback: {} , exception args: {}'.format(traceback.format_exc(), e.args)
        return error_response(error_str)