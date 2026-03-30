from lambda_function import EdcastAdapter

import glog as log

app_settings = {
   'base_url': 'https://poc.edcastpreview.com/',
   'api_key': '',
   'access_token': '',
   'email_swap_map': {'skumar@eightfold.ai': 'admin@edcast.com',
                      'gauravg@eightfold.ai': 'ankit@edcast.com',
                      'demo@eightfolddemo-skumar.com': 'ankit@edcast.com'}
}

ea = EdcastAdapter(app_settings)
req_data = {}
req_data['email'] = 'demo@eightfolddemo-skumar.com'
#import pdb
#pdb.set_trace()
resp = ea.get_current_courses(req_data)
log.info(resp)
req_data['skills'] = ["python", "Machine Learning", "hadoop", "Database"]
req_data['skills'] = ["Marketing Strategy", "Machine Learning", "hadoop", "Database"]
resp = ea.get_recommended_courses(req_data)
log.info(resp)
req_data = {'course_id': 'ECL-c67c345f-f76e-45d6-b748-014ab19472a5'}
resp = ea.get_course_details(req_data)
log.info(resp)
