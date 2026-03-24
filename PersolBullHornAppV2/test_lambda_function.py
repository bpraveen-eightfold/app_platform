import json
import mock
import pytest
import unittest
from lambda_function import SynchronizeAdapter
from lambda_function import NonRetryableException
from ef_app_sdk import EFAppSDK
import mock_context
import test_jsons_for_pytests



ctxt = mock_context.get_context("Test Mock", "1.2.0")
app_sdk = EFAppSDK(ctxt)
req_data = {}
app_settings = {
    "Authorization": "Test Auth",  # PK SANDBOX
    "Content-Type": "application/json",
    "client_id": "test_client_id",
    "client_secret": "test_client_secret",
    "username": "test_username",
    "password": "test_password",
    "redirect_uri": "test_redirect_url",
    "system_id": "test_system_id",
    "auth_domain": "auth-west9"
}

@mock.patch('bullhorn_adapter.BullHorn.setup')
class TestSynchronizeAdapter(unittest.TestCase):

    @mock.patch('bullhorn_adapter.BullHorn.get_entity_data')
    def test_is_candidate_in_bh(self, mock_get_entity_data, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        mock_get_entity_data.return_value = {
            "data": {
                "id": 123
            }
        }
        resp = sync_adapter.is_candidate_in_bh('123')
        assert resp == True

    @mock.patch('bullhorn_adapter.BullHorn.update_entity')
    @mock.patch('lambda_function.SynchronizeAdapter.delete_and_create_resume_in_bullhorn')
    @mock.patch('lambda_function.SynchronizeAdapter.delete_and_create_experience_in_bullhorn')
    @mock.patch('lambda_function.SynchronizeAdapter.delete_and_create_education_in_bullhorn')
    @mock.patch('lambda_function.SynchronizeAdapter.process_skills_object')
    def test_handle_update_candidate(self, mock_process_skills_object,
                                    mock_delete_and_create_education_in_bullhorn,
                                    mock_delete_and_create_experience_in_bullhorn,
                                    mock_delete_and_create_resume_in_bullhorn,
                                    mock_update_entity,
                                    mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        event_context = test_jsons_for_pytests.get_update_candidate_event_context()
        mock_process_skills_object.return_value = None
        expected_bh_request = {
            'id': 756,
            'occupation': 'test_title'
        }
        resp = sync_adapter.handle_update_candidate(event_context)
        mock_delete_and_create_experience_in_bullhorn.assert_called_once_with(event_context['update_spec'][1]['all_section_items'], 756)
        mock_update_entity.assert_called_once_with('Candidate', expected_bh_request, use_retry_with_exception=True)

    @mock.patch('bullhorn_adapter.BullHorn.update_entity')
    def test_handle_change_application_stage(self, mock_update_entity, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        event_context = test_jsons_for_pytests.get_change_app_stage_event_context()
        resp = sync_adapter.handle_change_application_stage(event_context)
        expected_bh_application_payload = {
            'id': 1674993612,
            'comments': 'test_comment',
            'status': 'Onsite Interview',
            'dateLastModified': 1234567890000,

        }
        mock_update_entity.assert_called_once_with('JobSubmission', expected_bh_application_payload, use_retry_with_exception=True)

    @mock.patch('bullhorn_adapter.BullHorn.search_entity')
    @mock.patch('bullhorn_adapter.BullHorn.create_notes_data')
    def test_handle_add_candidate_note(self, mock_create_notes_data, mock_search_entity, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        event_context = test_jsons_for_pytests.get_add_candidate_note_event_context()
        mock_search_entity.return_value = {
            'data': [
                {
                    'id': 123
                }
            ]
        }
        resp = sync_adapter.handle_add_candidate_note(event_context)
        expected_bh_note = {'dateAdded': 1674817800047, 'comments': 'Test Note', 'action': 'note', 'personReference': {'id': 446842466743}, 'candidates': [{'id': 446842466743}], 'commentingPerson': {'id': 123}}
        mock_create_notes_data.assert_called_once_with([expected_bh_note])

    def test_check_existing_candidate_in_bh_using_ef_customInfo(self, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        data_from_ef_api = {
            "customInfo": {
                "efcustom_text_bullhorn_id": 123
            }
        }
        resp = sync_adapter.check_existing_candidate_in_bh_using_ef_customInfo(data_from_ef_api)
        assert resp == True
        data_from_ef_api["customInfo"] = {}
        resp = sync_adapter.check_existing_candidate_in_bh_using_ef_customInfo(data_from_ef_api)
        assert resp == False

    @mock.patch('lambda_function.SynchronizeAdapter.is_candidate_in_bh')
    def test_check_existing_candidate_in_bh_using_candidate_id(self, mock_is_candidate_in_bh, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        candidate_id = 123
        mock_is_candidate_in_bh.return_value = True
        resp = sync_adapter.check_existing_candidate_in_bh_using_candidate_id(123)
        assert resp == True
        mock_is_candidate_in_bh.return_value = False
        resp = sync_adapter.check_existing_candidate_in_bh_using_candidate_id(123)
        assert resp == False

    @mock.patch('bullhorn_adapter.BullHorn.search_entity_post')
    def test_existing_candidate_in_bh_using_bh_customText1_and_ef_email(self, mock_search_entity_post, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        data_from_ef_api = {
            'email': 'demo@demo.com, test@test.com',
            'id': 'xyz123'
        }
        mock_search_entity_post.return_value = {
            'data': [
                {
                    'id': 1234,
                    'customText1': 'xyz123'
                }
            ]
        }
        resp = sync_adapter.existing_candidate_in_bh_using_bh_customText1_and_ef_email(data_from_ef_api)
        assert resp == {
            'id': 1234,
            'customText1': 'xyz123'
        }
        data_from_ef_api['id'] = 'abc123'
        resp = sync_adapter.existing_candidate_in_bh_using_bh_customText1_and_ef_email(data_from_ef_api)
        assert resp == False

    @mock.patch('lambda_function.SynchronizeAdapter.process_bh_event')
    @mock.patch('bullhorn_adapter.BullHorn.update_entity')
    @mock.patch('bullhorn_adapter.BullHorn.create_entity')
    @mock.patch('bullhorn_adapter.BullHorn.search_entity')
    @mock.patch('bullhorn_adapter.BullHorn.get_entity_data')
    def test_handle_add_application(self, mock_get_entity_data, mock_search_entity, mock_create_entity, mock_update_entity, mock_process_bh_event, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        event_context = {
            "operation": "add_application",
            "group_id": "persolkelly-sandbox.com",
            "system_id": "PK-BullHorn-EntitySync",
            "candidate_id": None,
            "application": None,
            "ats_action_user": {
                "name": "Persol User",
                "first_name": "Persol",
                "last_name": "User",
                "email": "demo@persolkelly-sandbox.com",
                "workflow_recipe_id": None,
                "ats_roles": [],
                "userid": None,
                "emp_id": None
            }
        }
        with pytest.raises(NonRetryableException):
            sync_adapter.handle_add_application(event_context)
        event_context['application'] = test_jsons_for_pytests.get_application_for_handle_add_application()
        with pytest.raises(NonRetryableException):
            sync_adapter.handle_add_application(event_context)
        event_context['candidate_id'] = 12345
        mock_get_entity_data.return_value = {
            'data': {
                'customTextBlock1': json.dumps({554248: 789})
            }
        }
        resp = sync_adapter.handle_add_application(event_context)
        assert resp == None
        mock_get_entity_data.return_value = {
            'data': {
                'customTextBlock1': json.dumps({554249: 789})
            }
        }
        mock_search_entity.return_value = {
            'data': []
        }
        mock_create_entity.return_value = {
            'changedEntityId': 456
        }
        resp = sync_adapter.handle_add_application(event_context)
        expected_bh_application_payload = {'candidate': {'id': 12345}, 'dateAdded': 1675056231000, 'dateLastModified': 1675056231000, 'status': 'Under Consideration', 'source': 'Eightfold API user', 'jobOrder': {'id': 554248}}
        mock_create_entity.assert_called_once_with('JobSubmission', expected_bh_application_payload, use_retry_with_exception=True)
        mock_update_entity.assert_called_once_with('Candidate', {'id': 12345, 'customTextBlock1': '{"554249": 789, "554248": 456}'})
        mock_process_bh_event.assert_called_once_with(["Candidate",12345,"UPDATED",[]], {"event":["Candidate",12345,"UPDATED",[]],"trigger_name":"app_notify"})

    @mock.patch('eightfold_adapter.Eightfold.create_ef')
    @mock.patch('lambda_function.SynchronizeAdapter.map_candidate_all_fields')
    @mock.patch('bullhorn_adapter.BullHorn.get_entity_data')
    @mock.patch('eightfold_adapter.Eightfold.get_ats_candidate')
    @mock.patch('bullhorn_adapter.BullHorn.create_experience_data')
    @mock.patch('bullhorn_adapter.BullHorn.create_education_data')
    @mock.patch('eightfold_adapter.Eightfold.get_ef_data_candidate_profile')
    @mock.patch('eightfold_adapter.Eightfold.update_ef_profile')
    @mock.patch('bullhorn_adapter.BullHorn.create_entity')
    @mock.patch('lambda_function.SynchronizeAdapter.process_skills_object')
    @mock.patch('bullhorn_adapter.BullHorn.create_bh_request_dict')
    @mock.patch('lambda_function.SynchronizeAdapter.existing_candidate_in_bh_using_bh_customText1_and_ef_email')
    def test_handle_create_candidate(self, mock_check_existing_using_customText1, 
                                    mock_bh_request_dict,
                                    mock_process_skills_object,
                                    mock_create_entity,
                                    mock_update_ef_profile,
                                    mock_get_ef_candidate_profile,
                                    mock_create_education_data,
                                    mock_create_experience_data,
                                    mock_get_ats_candidate, 
                                    mock_get_entity_data, 
                                    mock_candidate_all_fields, 
                                    mock_create_ef, 
                                    mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, {}, app_sdk)
        mock_check_existing_using_customText1.return_value = False
        req_data = test_jsons_for_pytests.get_create_candidate_req_data()
        mock_bh_request_dict.return_value = {'id': None, 'firstName': 'Alina', 'lastName': 'To', 'name': 'Alina To', 'email': 'alina.to@gmail.com', 'mobile': '', 'occupation': 'Web Developer', 'gender': 'F', 'address': {'countryID': ''}}
        mock_process_skills_object.return_value = {'replaceAll': [1002183, 1002180]}
        mock_get_ef_candidate_profile.return_value = req_data
        mock_create_entity.return_value = {
            "changedEntityId": 1234
        }
        mock_update_ef_profile.return_value = True
        mock_get_entity_data.return_value = test_jsons_for_pytests.get_candidate_entity_from_bh()
        mock_get_ats_candidate.return_value = False
        mock_candidate_all_fields.return_value = test_jsons_for_pytests.get_candidate_mapped_data()
        resp = sync_adapter.handle_create_candidate('candidate_create', req_data)
        assert resp == {"id": 1234}

    @mock.patch('eightfold_adapter.Eightfold.create_ef')
    @mock.patch('lambda_function.SynchronizeAdapter.map_candidate_all_fields')
    @mock.patch('bullhorn_adapter.BullHorn.get_entity_data')
    @mock.patch('eightfold_adapter.Eightfold.get_ats_candidate')
    @mock.patch('bullhorn_adapter.BullHorn.create_experience_data')
    @mock.patch('bullhorn_adapter.BullHorn.create_education_data')
    @mock.patch('eightfold_adapter.Eightfold.update_ef_profile')
    @mock.patch('bullhorn_adapter.BullHorn.create_entity')
    @mock.patch('lambda_function.SynchronizeAdapter.process_skills_object')
    @mock.patch('bullhorn_adapter.BullHorn.create_bh_request_dict')
    @mock.patch('lambda_function.SynchronizeAdapter.handle_add_application')
    @mock.patch('lambda_function.SynchronizeAdapter.check_existing_candidate_in_bh')
    @mock.patch('eightfold_adapter.Eightfold.get_ef_data_candidate_profile')
    def test_handle_add_candidate(self, mock_get_ef_candidate_profile, 
                                  mock_check_existing_candidate_in_bh, 
                                  mock_handle_add_application, 
                                  mock_bh_request_dict, 
                                  mock_process_skills_object,
                                  mock_create_entity, 
                                  mock_update_ef_profile, 
                                  mock_create_education_data, 
                                  mock_create_experience_data, 
                                  mock_get_ats_candidate, 
                                  mock_get_entity_data,
                                  mock_candidate_all_fields, 
                                  mock_create_ef, 
                                  mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        mock_get_ef_candidate_profile.return_value = test_jsons_for_pytests.get_create_candidate_req_data()
        mock_check_existing_candidate_in_bh.return_value = True
        event_context = test_jsons_for_pytests.get_add_candidate_event_context()
        sync_adapter.handle_add_candidate(event_context)
        mock_handle_add_application.assert_called_once_with(event_context)

        mock_check_existing_candidate_in_bh.return_value = False
        mock_bh_request_dict.return_value = {'id': None, 'firstName': 'Alina', 'lastName': 'To', 'name': 'Alina To', 'email': 'alina.to@gmail.com', 'mobile': '', 'occupation': 'Web Developer', 'gender': 'F', 'address': {'countryID': ''}}
        mock_process_skills_object.return_value = {'replaceAll': [1002183, 1002180]}
        mock_create_entity.return_value = {
            "changedEntityId": 1234
        }
        mock_update_ef_profile.return_value = True
        mock_get_entity_data.return_value = test_jsons_for_pytests.get_candidate_entity_from_bh()
        mock_get_ats_candidate.return_value = False
        mock_candidate_all_fields.return_value = test_jsons_for_pytests.get_candidate_mapped_data()
        resp = sync_adapter.handle_add_candidate(event_context)
        assert resp == {"changedEntityId": 1234}

    @mock.patch('eightfold_adapter.Eightfold.create_ef')
    @mock.patch('eightfold_adapter.Eightfold.update_ef')
    @mock.patch('lambda_function.SynchronizeAdapter.map_candidate_all_fields')
    @mock.patch('eightfold_adapter.Eightfold.get_ats_candidate')
    @mock.patch('diff_checker.DiffChecker.has_difference')
    @mock.patch('bullhorn_adapter.BullHorn.get_entity_data')
    def test_process_bh_event_candidate(self, mock_get_entity_data, mock_has_difference, mock_get_ats_candidate, mock_map_candidate_all_fields, mock_update_ef, mock_create_ef, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        # Update a Candidate in EF from sync back
        request_data = {"event":["Candidate",1234,"UPDATED",[]],"trigger_name":"app_notify"}
        mock_get_entity_data.return_value = test_jsons_for_pytests.get_candidate_entity_from_bh()
        mapped_data = test_jsons_for_pytests.get_candidate_mapped_data()
        mock_has_difference.return_value = mapped_data
        mock_get_ats_candidate.return_value = {}
        mock_map_candidate_all_fields.return_value = mapped_data
        sync_adapter.process_bh_event(request_data["event"], request_data)
    
        mapped_data['lastActivityTs'] = round(mapped_data['lastActivityTs']/1000)
        mock_update_ef.assert_called_once_with(mapped_data, 'Candidate', 1234)

        # Create a Candidate in EF from sync back
        request_data = {"event":["Candidate",1234,"INSERTED",[]],"trigger_name":"app_notify"}
        mock_get_entity_data.return_value = test_jsons_for_pytests.get_candidate_entity_from_bh()
        mapped_data['lastActivityTs'] = 1000 * mapped_data['lastActivityTs']
        mock_get_ats_candidate.return_value = None
        sync_adapter.process_bh_event(request_data["event"], request_data)
        mapped_data['lastActivityTs'] = round(mapped_data['lastActivityTs']/1000)
        mock_create_ef.assert_called_once_with(mapped_data, 'Candidate')

    @mock.patch('eightfold_adapter.Eightfold.create_ef')
    @mock.patch('eightfold_adapter.Eightfold.update_ef')
    @mock.patch('bullhorn_adapter.BullHorn.map_fields')
    @mock.patch('bullhorn_adapter.BullHorn.get_entity_data')
    def test_process_bh_event_joborder(self, mock_get_entity_data, mock_fields, mock_update_ef, mock_create_ef, mock_bullhorn_setup):
        sync_adapter = SynchronizeAdapter(app_settings, req_data, app_sdk)
        mock_get_entity_data.return_value = test_jsons_for_pytests.get_joborder_entity_from_bh()
        mapped_data = test_jsons_for_pytests.get_joborder_mapped_data()
        mock_fields.return_value = mapped_data
        # Create a position in EF from sync back
        request_data = {"event":["JobOrder",1234,"INSERTED",[]],"trigger_name":"app_notify"}
        sync_adapter.process_bh_event(request_data["event"], request_data)
        mock_create_ef.assert_called_once_with(mapped_data, 'Position')
        # Update a position in EF from sync back
        request_data = {"event":["JobOrder",1234,"UPDATED",[]],"trigger_name":"app_notify"}
        sync_adapter.process_bh_event(request_data["event"], request_data)
        mock_update_ef.assert_called_once_with(mapped_data, 'Position', '1234')

