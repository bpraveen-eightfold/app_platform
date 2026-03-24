import json
import traceback
import glog as log

from sterling_adapter import SterlingAdapter

"""
    - Provide an entry point function for your app.
    - The context arg can be ignored completely
    - The event arg will contain all needed params to properly invoke your app
"""
def app_handler(event, context):
    app_settings = event.get('app_settings', {})
    request_data = event.get('request_data', {})
    trigger_name = request_data.get('trigger_name')

    print('Call received for trigger_name: {}'.format(trigger_name))
    print('Request data is {}'.format(json.dumps(request_data)))
    data = None
    try:
        sterling_adapter = SterlingAdapter(app_settings)
        if trigger_name == 'bgv_list_packages':
            print('Calling get_packages from trigger')
            log.info('Calling get_packages from trigger')
            data = sterling_adapter.get_packages(request_data)
        elif trigger_name == 'bgv_initiate_background_verification':
            data = sterling_adapter.initiate_background_verification(request_data)
    except Exception as ex:
        err_str = 'Handler for trigger_name: {} failed with error: {}, traceback: {}'.format(
            trigger_name, str(ex), traceback.format_exc())
        print(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }
    print('Response is {}'.format(json.dumps(data)))
    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }

