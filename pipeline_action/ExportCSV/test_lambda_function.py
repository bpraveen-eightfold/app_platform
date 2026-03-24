import json
from lambda_function import current_micro_time
from lambda_function import _extract_notes
from lambda_function import app_handler


class TestLambdaFunction:
    def test_app_handler(self):
        request_data = {'profile_json_list': [
                            {'name': 'Garuav',
                             'phone': '650-887-998',
                             'employee_info': {'dept': 'engineering'},
                             'notes': '"demo@activision-sandbox.com added note on 2021-04-20: This is a t4st notes","demo@activision-sandbox.com added note on 2021-04-19:  test notes ","demo@activision-sandbox.com added note on 2021-04-19: Happy notes "'
                            },
                            {'name': 'Satyajeet',
                             'phone': '650-887-999',
                             'employee_info': {'dept': 'engineering'}
                            },
                           ],
                        'user_email': 'demo@eightfolddemo-skumar.com'
                       }
        app_settings = {'profile_fields': ['name', 'phone', 'employee_info.dept', 'notes'],
                        'bucket_name': 'ef-app-platform',
                        'app_name': 'ExportCSV',
                        'num_notes': 1
                       }
        event = {'trigger_name': 'pipeline_app_action'}
        event['request_data'] = request_data
        event['app_settings'] = app_settings
        start_time_us = current_micro_time()
        resp = app_handler(event, {})
        end_time_us = current_micro_time()
        print(resp)
        print('Total us: {}'.format(end_time_us - start_time_us))
        assert resp['statusCode'] == 200
        data = json.loads(resp['body']).get('data')
        assert len(data['actions']) == 1
        action = data['actions'][0]
        assert action['action_name'] == 'convert_data_to_csv'
        action_req_data = action['request_data']
        assert len(action_req_data['headers']) == 4
        assert len(action_req_data['row_list']) == 2
        assert action_req_data['row_list'][0][-1] == '"demo@activision-sandbox.com added note on 2021-04-20: This is a t4st notes"'

    def test_extract_notes(self):
        notes = '"demo@activision-sandbox.com added note on 2021-04-20: This is a t4st notes","demo@activision-sandbox.com added note on 2021-04-19:  test notes ","demo@activision-sandbox.com added note on 2021-04-19: Happy notes "'
        en = _extract_notes(notes, 1)
        assert en == '"demo@activision-sandbox.com added note on 2021-04-20: This is a t4st notes"'
        en = _extract_notes(notes, 2)
        assert en == '"demo@activision-sandbox.com added note on 2021-04-20: This is a t4st notes","demo@activision-sandbox.com added note on 2021-04-19:  test notes "'
        en = _extract_notes(notes, 3)
        assert en == notes
        en = _extract_notes(notes, 4)
        assert en == notes
        en = _extract_notes(notes, 0)
        assert en == ''
