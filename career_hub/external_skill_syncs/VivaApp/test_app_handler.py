from lambda_function import app_handler

if __name__ == "__main__":
    # eventually the format should be 'data'
    request_data = {
        'data': [
            {"skillName": "C#", "skillTags": ["UserConfirmed"]}, {"skillName": "NodeJS", "skillTags": ["Learning"]}
        ]
    }
    trigger_name = 'sync_external_skills'
    app_settings = {
        'base_url': 'https://apim-tc-viva-integrations-v3.azure-api.net',
        'test_employee_id': 111115,
        'subscription_key': '12345',
        'endpoint': 'skills-dev/v2'
    }

    event = {
        'request_data': request_data,
        'trigger_name': trigger_name,
        'app_settings': app_settings
    }

    resp = app_handler(event, None)
    print(resp)