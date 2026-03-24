from __future__ import absolute_import

from unittest import mock

from lambda_function import SFDCAdapter
from mock import patch

@mock.patch('lambda_function.SFDCAdapter.get_opportunities')
@mock.patch('requests.post')
def test_get_entity_search_results(mock_post, mock_get_opportunities):
    class MockResponse:
        def __init__(self, json_data):
            self.json_data = json_data
        def json(self):
            return self.json_data
    mock_post.return_value = MockResponse({'instance_url': 'http://None', 'access_token': ''})
    mock_get_opportunities.return_value = []
    app_settings = {
     'token_url': '',
     'client_id': '',
     'client_secret': '',
     'username': '',
     'password': ''
    }
    req_data = {
        "start": 0,
        "limit": 0
    }
    adapter = SFDCAdapter.get_adapter(app_settings)
    res = SFDCAdapter.get_entity_search_results(adapter, req_data)
    assert res.get("num_results") == 0
    assert res.get("entities") == []

    req_data = {
        "start": 0,
        "limit": 10
    }
    adapter = SFDCAdapter.get_adapter(app_settings)
    res = SFDCAdapter.get_entity_search_results(adapter, req_data)
    assert res.get("num_results") == 0
    assert res.get("entities") == []

    req_data = {
        "start": 10,
        "limit": 20
    }
    adapter = SFDCAdapter.get_adapter(app_settings)
    res = SFDCAdapter.get_entity_search_results(adapter, req_data)
    assert res.get("num_results") == 0
    assert res.get("entities") == []

    dummy_opportunities = [
        {
            'id': 0,
            'name': 'name0',
            'description': 'desc0',
            'fields': 'fields0'
        },
        {
            'id': 1,
            'name': 'name1',
            'description': 'desc1',
            'fields': 'fields1'
        },
        {
            'id': 2,
            'name': 'name2',
            'description': 'desc2',
            'fields': 'fields2'
        },
        {
            'id': 3,
            'name': 'name3',
            'description': 'desc3',
            'fields': 'fields3'
        },
        {
            'id': 4,
            'name': 'name4',
            'description': 'desc4',
            'fields': 'fields4'
        },
        {
            'id': 5,
            'name': 'name5',
            'description': 'desc5',
            'fields': 'fields5'
        },
    ]
    mock_get_opportunities.return_value = dummy_opportunities
    req_data = {
        "start": 0,
        "limit": 2
    }
    res = SFDCAdapter.get_entity_search_results(adapter, req_data)
    assert res.get("num_results") == 6
    assert res.get("entities") == [
        {'entity_id': 0, 'title': 'name0', 'description': 'desc0', 'source_name': 'desc0', 'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/220px-Salesforce.com_logo.svg.png', 'cta_url': 'http://None/0', 'cta_label': 'Opportunity', 'fields': 'fields0', 'last_modified_ts': None, 'metadata': None, 'tags': None, 'custom_sections': None}, 
        {'entity_id': 1, 'title': 'name1', 'description': 'desc1', 'source_name': 'desc1', 'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/220px-Salesforce.com_logo.svg.png', 'cta_url': 'http://None/1', 'cta_label': 'Opportunity', 'fields': 'fields1', 'last_modified_ts': None, 'metadata': None, 'tags': None, 'custom_sections': None}
    ]

    req_data = {
        "start": 2,
        "limit": 10
    }
    res = SFDCAdapter.get_entity_search_results(adapter, req_data)
    assert res.get("num_results") == 6
    assert res.get("entities") == [
        {'entity_id': 2, 'title': 'name2', 'description': 'desc2', 'source_name': 'desc2', 'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/220px-Salesforce.com_logo.svg.png', 'cta_url': 'http://None/2', 'cta_label': 'Opportunity', 'fields': 'fields2', 'last_modified_ts': None, 'metadata': None, 'tags': None, 'custom_sections': None}, 
        {'entity_id': 3, 'title': 'name3', 'description': 'desc3', 'source_name': 'desc3', 'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/220px-Salesforce.com_logo.svg.png', 'cta_url': 'http://None/3', 'cta_label': 'Opportunity', 'fields': 'fields3', 'last_modified_ts': None, 'metadata': None, 'tags': None, 'custom_sections': None}, 
        {'entity_id': 4, 'title': 'name4', 'description': 'desc4', 'source_name': 'desc4', 'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/220px-Salesforce.com_logo.svg.png', 'cta_url': 'http://None/4', 'cta_label': 'Opportunity', 'fields': 'fields4', 'last_modified_ts': None, 'metadata': None, 'tags': None, 'custom_sections': None}, 
        {'entity_id': 5, 'title': 'name5', 'description': 'desc5', 'source_name': 'desc5', 'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Salesforce.com_logo.svg/220px-Salesforce.com_logo.svg.png', 'cta_url': 'http://None/5', 'cta_label': 'Opportunity', 'fields': 'fields5', 'last_modified_ts': None, 'metadata': None, 'tags': None, 'custom_sections': None}
    ]
