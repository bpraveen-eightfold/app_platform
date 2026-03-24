import json

from constants import AppSettingsAttributes, RequestDataAttributes
from exceptions import AvailabilityAppException
from mera_adapter import MeraAvailabilityAdapter


def _validate_fetch_employee_availability_request(event):
    app_settings = event.get('app_settings', {})
    req_data = event.get('request_data', {})

    for attribute in AppSettingsAttributes.get_required_attrs():
        if not app_settings.get(attribute):
            raise AvailabilityAppException(message=f'app_settings attribute: {attribute} cannot be none', status_code=400)

    for attribute in RequestDataAttributes.get_required_attrs():
        if not req_data.get(attribute):
            raise AvailabilityAppException(message=f'request_data attribute: {attribute} cannot be none', status_code=400)

    return app_settings, req_data

def _fetch_employee_availability_handler(event, context):
    app_settings, req_data = _validate_fetch_employee_availability_request(event)
    employees_availability = MeraAvailabilityAdapter.fetch_availability(app_settings, req_data)

    data = {
        'actions': [{
            'action_name': 'store_employee_availability_data',
            'request_data': { 'employees_availability': employees_availability }
        }]
    }
    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }


def _default_trigger_handler(event, context):
    trigger_name = event.get('trigger_name')
    return {
        'statusCode': 400,
        'body': json.dumps({'error': f'Unsupported trigger {trigger_name} specified in request'}),
    }


TRIGGER_HANDLERS = {
    'fetch_employee_availability': _fetch_employee_availability_handler
}

def app_handler(event, context):
    """ App entry point """
    try:
        trigger_name = event.get('trigger_name')
        handler = TRIGGER_HANDLERS.get(trigger_name, _default_trigger_handler)
        return handler(event=event, context=context)
    except AvailabilityAppException as ex:
        return ex.to_error_response()
    except Exception as ex:
        return AvailabilityAppException(message=repr(ex), status_code=500).to_error_response()
