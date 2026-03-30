import json
import re
from lambda_function import app_handler

req_data = {
}
app_settings = {
}

event = {
    'trigger_name': 'ta_profile_view',
    'request_data': req_data,
    'app_settings': app_settings
}

print(app_handler(event, {}))
import os, psutil; print(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2)
