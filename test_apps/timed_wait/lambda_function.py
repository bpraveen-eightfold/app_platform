# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
This app sleeps for a given amount of time
"""

from __future__ import absolute_import
import time

def app_handler(event, context):

    req_data = event.get('request_data', {})
    trigger_name = event.get('trigger_name')
    app_settings = event.get('app_settings', {})

    print(f'Call received for trigger_name: {trigger_name}')

    wait_time = int(app_settings.get('wait_time') or 0)
    print(f'Planning to sleep for {wait_time} secs')

    if wait_time > 0:
        start = time.time()
        time.sleep(wait_time)
        elapsed = time.time() - start
        print('Done sleeping - ' + str(elapsed))
    else:
        print('No sleep required - ' + str(wait_time))

    return {'wait_time': wait_time}
