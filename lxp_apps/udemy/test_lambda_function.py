from lambda_function import *
import pprint


event_file = open("event.json")
event_json = json.load(event_file)

response_data = app_handler(event_json, "")
pprint.pprint(response_data)
