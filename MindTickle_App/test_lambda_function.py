from lambda_function import MindTickleAdapter
from lambda_function import app_handler

import json
import glog as log
import unittest
import time

# To run a test, use below command (for ex: for first test):
# Change to test directory
# python -m unittest test_lambda_function.TestLambdaFunction.test_ingeration_with_real_credentials
class TestLambdaFunction(unittest.TestCase):
    # To execute this, provide real values in app_settings dict
    def setUp(self):
        pass
        #import sys
        #sys.setrecursionlimit(1500)

    def test_ingeration_with_real_credentials(self):
        app_settings = {
            'reporting_api_username': 'integration@eightfold.ai',
            'reporting_api_password': 'User@123',
            'content_api_api_key': '9aa7716d8890f1f0159c824e775f8d33a74d1d25',
            'content_api_secret_key': '29d4dc63b8694c81d9ce230b54216000472a6c84f7a709ac0f8fa8bcbadedcbcf046f29e9f53f8db9048610282899e25',
            'content_api_company_id': '1158638238264268256'
        }

        mta = MindTickleAdapter(app_settings)
        req_data = {
            'current_user_email': 'skumar@eightfold.ai',
            'limit': 10,
            'start': 0
        }

        #start_ts = int(time.time())
        #resp = mta.get_assigned_modules(req_data)
        #log.info(f'total_time: {int(time.time()) - start_ts}')
        #log.info(resp)

        event = {}
        req_data['trigger_name'] = 'careerhub_entity_search_results'
        req_data['trigger_source'] = 'app_platform_search'
        req_data['term'] = 'talent management'
        event['trigger_name'] = req_data['trigger_name']
        event['request_data'] = req_data
        event['app_settings'] = app_settings

        import pdb
        pdb.set_trace()
        #inv_idx = mta._initialize_modules_inverted_index()
        #print(inv_idx.query("talent management"))

        resp = app_handler(event, {})
        log.info(resp)

        data = json.loads(resp['body']).get('data')
        entity_id_set = set()
        for module in data['entities']:
            print(module['entity_id'])
            entity_id_set.add(module['entity_id'])
        log.info(f'num_entities: {len(data["entities"])}, num_unique_entities: {len(entity_id_set)}')
        self.assertEqual(len(data['entities']), len(entity_id_set))
        # validate that all the entities return are unique
        cursor = data['cursor']
        last_entity_id = data["entities"][-1]["entity_id"]
        log.info(f'cursor == last_entity_id: {cursor == last_entity_id}, cursor: {cursor}, last_entity_id: {last_entity_id}')
        self.assertTrue(cursor != last_entity_id)
        req_data['cursor'] = cursor
        req_data['start'] = 10

        resp = app_handler(event, {})
        log.info(resp)
        data = json.loads(resp['body']).get('data')
        for module in data['entities']:
            print(module['entity_id'])
            entity_id_set.add(module['entity_id'])
        log.info(f'num_entities: {len(data["entities"])}, num_unique_entities: {len(entity_id_set)}')

        req_data['trigger_source'] = 'ch_homepage'
        req_data['start'] = 0
        event['request_data'] = req_data
        resp = app_handler(event, {})
        log.info(resp)


        req_data = {
            'entity_id': '1484589036786812158:1496713050474480969',
            'current_user_email': 'skumar@eightfold.ai',
        }
        mta = MindTickleAdapter(app_settings)
        resp = mta.get_module_details(req_data)
        log.info(resp)

    def test_process_assigned_modules_resp_content(self):
        req_data = {
            'current_user_email': 'skumar@eightfold.ai',
            'limit': 10,
            'start': 0
        }
        data = 'UserId,SeriesId,ModuleId,Version,LearnerModuleState,InvitedOn,EntityType,ReattemptNo,MaxScore,DueDate,Score,IsCertified,PercentScore,PercentCompleted,HasCompleted,HasStarted,IsOnTarget,IsLikelyToMiss,HasDroppedOff,IsOverdue,ModuleName,SeriesName,HasFailed,SeriesInviteTime,CompletionStatus,StartTime,EndTime,LearnerName,LearnerEmailId,ModuleRelevance\n'
        mta = MindTickleAdapter(
            {'content_api_secret_key': '1234',
             'content_api_api_key': 'dummy',
             'content_api_company_id': 'companyId'
            }
        )
        search_results = mta._process_assigned_modules_resp_content(data, req_data)
        self.assertEqual(search_results['num_results'], 0)
        self.assertEqual(search_results['entities'], [])
        self.assertEqual(search_results['cursor'], None)
