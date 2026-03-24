# pylint: disable:ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import json
import requests
from bs4 import BeautifulSoup
from urllib import parse
from ef_app_sdk import EFAppSDK

"""
    - Provide an entry point function for your app.
    - Your function must accept two args -> event and context
    - The context arg can be ignored completely
    - The event arg will contain all needed params to properly invoke your app
"""

all_test_map = {}

def transform_test_to_entity_obj(test):
    entity_obj = {}
    entity_obj['entity_id'] = test.get('id', 0)
    entity_obj['title'] = test.get('title', '')
    subtitle_html = BeautifulSoup(test.get('test_description') or '', 'html.parser')
    entity_obj['subtitle'] = subtitle_html.get_text()
    entity_obj['description'] = subtitle_html.get_text()
    entity_obj['image_url'] = None
    entity_obj['cta_url'] = f'http://www.hackerearth.com/{test.get("slug", "")}'
    entity_obj['cta_label'] = 'Take Test'
    entity_obj['card_label'] = 'Hackerearth'
    entity_obj['metadata'] = []
    return entity_obj
   
def get_entity_if_skill_match(test, skills):
    if not skills:
        return {}
    entity_obj = transform_test_to_entity_obj(test)
    event_skills = []
    event_skills.extend(test.get('skills', []))
    event_skills.extend(test.get('skills_at_creation', []))
    event_skills.extend(test.get('tags', '').split(','))
    matched_skill = list(set(event_skills).intersection(skills))
    score  = len(matched_skill)
    if score < 1:
        return {}
    entity_obj['metadata'].append({'name': 'score', 'value': score})
    entity_obj['metadata'].append({'name': 'tags', 'value': matched_skill})
    return entity_obj

def get_skills(event):
    fq = event.get('request_data', {}).get('fq', {})
    position_skills = [x['name'] for x in fq.get('position_skills', []) if x['name']]
    skill_goals = [x['name'] for x in fq.get('skill_goals', []) if x['name']]
    profile_skills = [x['name'] for x in fq.get('profile_skills', []) if x['name']]
    return position_skills or skill_goals or profile_skills or []

def extract_secrets(app_settings):
    CLIENT_ID = app_settings.get('hackerearth-client-id')
    CLIENT_SECRET =  app_settings.get('hackerearth-client-secret')
    return CLIENT_ID, CLIENT_SECRET

def fetch_tests_map(app_settings):
    global all_test_map
    CLIENT_ID, CLIENT_SECRET = extract_secrets(app_settings)
    PAGE_SIZE = 49  
    if len(all_test_map) == 0:
        raw_events = []
        has_more = True
        curr_page = 1
        while has_more:
            payload = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'page_number': curr_page,
                'page_size': PAGE_SIZE
            }
            resp = requests.post("https://api.hackerearth.com/partner/hackerearth/events-list/", data=json.dumps(payload))
            if resp.status_code != 200:
                error_msg = 'HackerEarth API call failed with '+ str(resp.json().get('emessage', ''))
                raise Exception(error_msg) 
            resp = resp.json()
            if resp['mcode'] != 'success':
                error_msg = 'HackerEarth API call failed with '+ str(resp.json().get('emessage', ''))
                raise Exception(error_msg) 
            curr_page = curr_page + 1
            has_more = resp['has_more']
            raw_events.extend(resp['events'])
            event_map = {}
            for r in raw_events:
                event_map[r.get('id', 0)] = r
            all_test_map = event_map
    return all_test_map

def handle_careerhub_entity_search_results(event): 
    result = {}
    try:
      tests = fetch_tests_map(event.get('app_settings', {})).values()
      skills = get_skills(event)
      source = event.get('request_data', {}).get('trigger_source')
      result['entities'] = []
      for test in tests or []:
        entity_obj = get_entity_if_skill_match(test, skills)
        if entity_obj:
          entity_obj['trigger_app_on_click'] = source != 'ch_search'
          result['entities'].append(entity_obj)
      result['entities'] = list(filter(lambda x : x['metadata'][0]['value'] != 0, result['entities']))
      result['entities'].sort(key=lambda x : x['metadata'][0]['value'], reverse=True)
      result['num_results'] = len(result['entities'])        
      return {"statusCode": 200, "body": json.dumps({"data": result})}
    except Exception as e:
       return {"statusCode": 200, "body": json.dumps({"data": str(e)})}

def handle_careerhub_get_entity_details(event):
    try:
      tests_map = fetch_tests_map(event.get('app_settings', {}))
      id = int(event.get('request_data', {}).get('entity_id'))
      entity_obj = {}
      if id and id in tests_map:
        entity_obj = transform_test_to_entity_obj(tests_map[id])
      return {"statusCode": 200, "body": json.dumps({"data": entity_obj})}
    except Exception as e:
      return {"statusCode": 200, "body": json.dumps({"data": str(e)})}

def handle_careerhub_app_platform_card_click(event):
    CLIENT_ID, CLIENT_SECRET = extract_secrets(event.get('app_settings', {}))
    test_id = event.get("request_data", {}).get('entity_id')
    email = event.get("request_data", {}).get('current_user_email')
    profile_id = event.get("request_data", {}).get('profile_id')
    result = {}
    group_id = event.get('group_id')
    app_id = event.get('app_id')
    payload = {
      'client_id': CLIENT_ID,
      'client_secret': CLIENT_SECRET,
      'test_id': test_id,
      'emails': [email],
      'extra_parameters': {
        'report_callback_urls': {
          email: f'https://notifications.eightfold.ai/event/vendor_event/{group_id}/{app_id}?profile_id={profile_id}'
        }
      }
    }
    try:
      resp = requests.post("https://api.hackerearth.com/partner/hackerearth/invite/", data=json.dumps(payload))
      if resp.status_code != 200:
        error_msg = 'HackerEarth API call failed with '+ str(resp.json().get('emessage', ''))
        raise Exception(error_msg) 
      resp = resp.json()
      invite_link = resp.get("extra_parameters", {}).get('invite_urls', {}).get(email)
      result['redirect_url'] = invite_link
      result['hackerearth_resp'] = resp
      return {"statusCode": 200, "body": json.dumps({"data": result})}
    except Exception as e:
       return {"statusCode": 200, "body": json.dumps({"data": {'error_msg': str(e)}})}
  
def handle_webhook_receive_event(event):    
    result = {}
    hackerearth_resp = event.get('request_data', {}).get('request_payload', {})
    request_url = event.get('request_data', {}).get('request_url')
    url = parse.urlparse(request_url)
    profile_id_param = parse.parse_qs(url.query).get('profile_id')
    if not profile_id_param:
      return  {"statusCode": 200, "body": json.dumps({"data": {}})}
    profile_id = profile_id_param[0]
    group_id = event.get('group_id')
    app_id = event.get('app_id')
    assessment_name = hackerearth_resp.get('test_info', {}).get('title')
    score = hackerearth_resp.get('candidate_report', {}).get('score')
    max_score = hackerearth_resp.get('test_info', {}).get('max_score')
    test_id = str(hackerearth_resp.get('test_info', {}).get('test_id'))
    result['actions'] = [
        {
          "action_name": "save_practice_assessment_result_to_profile_data",
          "request_data": {
            "profile_id": str(profile_id),
            "assessment_report": {
              "assessment_name": assessment_name,
              "test_id": test_id,
              "status": "completed",
              "score": f'{score}/{max_score}',
              "report_url": hackerearth_resp.get('candidate_report', {}).get('full_report_url'),
              "vendor_display_name": "Hackerearth Practice"
            }
          }
        },
        {
            'action_name': 'send_email',
            'request_data': {
                'email_from': f'import@{group_id}',
                'email_to': hackerearth_resp.get('candidate_report', {}).get('email'),
                'subject': f'Your HackerEarth scores for {assessment_name} are ready!',
                'body': f"""
                            <div style="margin:0;padding:0;background-color:#f3f3f3;">
                              <div style="padding: 16px;">
                                <table style=" table-layout:fixed;vertical-align:top;max-width:550px;Margin:0 auto;border-spacing:0;border-collapse:collapse;background-color:#ffffff;width:100%;border: 1px solid #DFDFDF; border-radius: 4px;" cellpadding="0" cellspacing="0" width="100%" bgcolor="#FFFFFF" valign="top">
                                  <tbody>
                                    <tr style="vertical-align:top" valign="top">
                                      <td style="word-break:break-word;vertical-align:top;padding-bottom: 44px;" valign="top">
                                        <div>
                                          <div style="Margin:0 auto">
                                            <div style="border-collapse:collapse;display:table;width:100%">
                                              <div style="display:table-cell;vertical-align:top;">
                                                <div align="center" style="padding-right:0px;padding-left:0px;padding-top:36px;"></div>
                                                <div align="center" style="padding-right:0px;padding-left:0px;padding-top:36px;"></div>
                                                <div style="font-size: 22px; font-weight: 500;letter-spacing: 0;line-height: 31px;text-align: center;font-family:Open Sans,Helvetica Neue,Helvetica,Arial,sans-serif;padding-top: 36px;padding-left:24px; padding-right:24px;"> Thank you for taking the {assessment_name}! </div>
                                                <div style="font-size: 16px; letter-spacing: 0;line-height: 23px;text-align: left; font-family:Open Sans,Helvetica Neue,Helvetica,Arial,sans-serif;padding: 24px">
                                                  <p>You have scored <b>{score}/{max_score}</b> in the test.
                                                  <p>You can choose to share score with the Hiring Team by clicking on the following button</p>
                                                  <div>
                                                    <table>
                                                      <tr>
                                                        <td style="width: 149px;"></td>
                                                        <td align="center" style="font-family: 'Source Sans Pro'; font-size: 18px; background-color: #2C8CC9; padding: 10px 0 10px 0;
                                                    border-color: #2C8CC9; border-radius: 4px; width: 250px; text-align: center; vertical-align: middle;">
                                                          <a target="_blank" href="https://app.eightfold.ai/careerhub/assessment/publish/{app_id}/{test_id}?domain={group_id}" style="display:block; color: #ffffff; font-weight:400; text-decoration: none; font-family: 'Source Sans Pro', Helvetica;">Add Score to Profile</a>
                                                        </td>
                                                      </tr>
                                                    </table>
                                                  </div>
                                                </div>
                                              </div>
                                            </div>
                                          </div>
                                        </div>
                                      </td>
                                    </tr>
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          """
            }
        }
    ]
    result['is_success'] = True
    return {"statusCode": 200, "body": json.dumps({"data": result})}
   

TRIGGER_TO_FUNCTION_MAP = {
   'careerhub_get_entity_details': handle_careerhub_get_entity_details,
    'careerhub_entity_search_results': handle_careerhub_entity_search_results,
    'careerhub_app_platform_card_click': handle_careerhub_app_platform_card_click,
    'webhook_receive_event': handle_webhook_receive_event,

}

def app_handler(event = None, context= None):
    # Extract request_data -> this is the dynamic, per-invocation data for your app. E.g. profile info, message to be sent, etc.
    # request_data = event.get("request_data", {})

    # Extract app_settings -> this are the static params for your app configured for each unique installation. E.g. API keys, allow/deny lists, etc.
    # app_settings = event.get("app_settings", {})
    app_sdk = EFAppSDK(context)
    trigger_name = event.get("trigger_name")
    func = TRIGGER_TO_FUNCTION_MAP.get(trigger_name)
    if func:
       return func(event)
    else:
        app_sdk.log('Trigger not implemented')
        return {"statusCode": 500, "body": json.dumps({"data": {}})}
