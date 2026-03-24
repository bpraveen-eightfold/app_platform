from lambda_function import TestAdapter

import glog as log

app_settings = {}

ta = TestAdapter(app_settings)
req_data = {
    'current_user_email': 'demo@eightfolddemo-skumar.com',
}
resp = ta.get_current_courses(req_data, {})
log.info(resp)

try:
    resp = ta.get_current_courses(req_data, {'error_cases': {'course_attendance_user_not_found': True}})
except Exception as ex:
    log.info(ex)

req_data = {
    'current_user_email': 'demo@eightfolddemo-skumar.com',
    'fq': {'skills': ["python", "Machine Learning", "hadoop", "Database"]},
    'limit': 5,
    'start': 0,
    'cursor': None
}

resp = ta.get_courses_search_results(req_data, {})
log.info(resp)
req_data['term'] = '10'

app_settings = {'use_cursor_based_pagination': True}
resp = ta.get_courses_search_results(req_data, app_settings)
log.info(resp)
assert resp['cursor'] is not None

start = ta._get_start_idx_using_term('Business')
print(f'start: {start}')
assert start == 856

req_data['term'] = 'Accounting'
resp = ta.get_courses_search_results(req_data, {})
log.info(resp)

resp = ta.get_courses_search_results(req_data, {})
log.info(resp)
assert resp['cursor'] is None

req_data = {'entity_id': '1'}
resp = ta.get_course_details(req_data, {})
log.info(resp)
resp = ta.get_courses_for_career_planner(req_data, {})
log.info(resp)
