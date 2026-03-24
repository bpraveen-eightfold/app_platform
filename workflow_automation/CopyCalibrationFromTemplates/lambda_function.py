import traceback

from position_copy_calibration import PositionCopyCalibration


def app_handler(event, context):
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    print({'request_data': request_data, 'app_settings': app_settings})

    should_confirm_calibration = app_settings.get('should_confirm_calibration')
    if should_confirm_calibration is None:
        return {
            'statusCode': 400,
            'body': {'error': 'should_confirm_calibration not provided in app_settings'}
        }

    ef_api_key = app_settings.get('ef_api_key')
    if not ef_api_key:
        raise ValueError('Please provide ef_api_key in app_settings')

    copy_from_role_cali_template = app_settings.get('copy_from_role_calibration_template', False)

    reference_name_suffix = None
    calibration_templates = []
    if copy_from_role_cali_template:
        role = request_data.get('role') or {}
        calibration_templates = role.get('templates') or []
    else:
        reference_name_suffix = app_settings.get('reference_name_suffix', '').strip()
        if not reference_name_suffix:
            raise ValueError('Please provide reference_name_suffix in app_settings')

    aws_region = app_settings.get('aws_region', 'US')

    pid = request_data.get('positionId')
    if not pid:
        return {
            'statusCode': 400,
            'body': {'error': 'id not found in request_data'}
        }

    position_name = request_data.get('name')
    if not position_name:
        return {
            'statusCode': 400,
            'body': {'error': 'name not found in request_data'}
        }

    countries = request_data.get('locations', [])

    actions = []
    try:
        position_copy_calibration = PositionCopyCalibration(position_id=pid, position_name=position_name, aws_region=aws_region, ef_api_key=ef_api_key,
                                                            reference_name_suffix=reference_name_suffix, calibration_templates=calibration_templates,
                                                            countries=countries)
        if copy_from_role_cali_template:
            calibration_template_id = position_copy_calibration.get_best_matched_template_id()
        else:
            calibration_template_id = position_copy_calibration.get_exact_matched_template_id()
        actions.append({
            'action_name': 'entity_update_action',
            'request_data': {
                'entity_type': 'position',
                'entity_id': pid,
                'confirm_calibration': should_confirm_calibration,
                'update_payload': {
                    'custom_info.calibration_template_id': calibration_template_id
                },
            }
        })
    except Exception:
        print(traceback.format_exc())

    data = {'actions': actions}
    response = {
        'statusCode': 200,
        'body': {'data': data}
    }
    print({'app_response': response})
    return response
