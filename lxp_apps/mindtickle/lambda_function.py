# pylint: disable=ef-restricted-imports, unused-variable, unused-import
"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import gevent.monkey
gevent.monkey.patch_all()
import time
import random
import json
import traceback

import concurrent.futures
import response_objects
import mindtickle_utils
import inverted_index
from requests.auth import HTTPBasicAuth

LEARNER_MODULE_URL = 'https://admin.mindtickle.com/Odata.svc/LearnerModulePerformances'
CONTENT_API_BASE_URL = 'https://api.mindtickle.com'
CONTENT_API_SERIES_LIST_URL = '{base_url}/api/v2/series/list'
CONTENT_API_MODULE_LIST_URL = '{base_url}/api/v2/series/{series_id}/list'
CONTENT_API_MODULE_DETAILS_URL = '{base_url}/api/v2/jit/series/{series_id}/entity/{module_id}'
SECONDS_IN_A_DAY = 86400
modules_inv_index_g = None
series_data_map_g = {}
idx_to_entity_id_map_g = {}
idx_create_time_secs_g = 0

def _get_entity_from_module_details(data_dict, entity_id):
    entity_obj = response_objects.CareerhubEntityDetailsResponseType()
    entity_obj.entity_id = entity_id
    entity_obj.title = data_dict.get('name')
    entity_obj.description = data_dict.get('description')
    entity_obj.image_url = data_dict.get('thumbnailUrl')
    entity_obj.tags = [item.get('tagName') for item in data_dict.get('tags', {}).get('values', []) if item.get('tagName')]
    module_url = data_dict.get('url')
    entity_obj.cta_url = module_url
    entity_obj.description = data_dict.get('description') or ""
    entity_obj.source_name = 'MindTickle'
    entity_obj.cta_label = 'View Module'
    entity_obj.card_label = 'Module'
    entity_obj.fields = []
    return entity_obj

class ModuleIterator:
    def __init__(self, headers, cursor):
        self.headers = headers
        self.cursor = cursor
        self.series_id = None
        self.module_id = None
        self._series_idx = None
        self._module_idx = None
        self.series_modules_data = None
        url = CONTENT_API_SERIES_LIST_URL.format(base_url=CONTENT_API_BASE_URL)
        self.series_list_data = self._fetch_content(url)
        self.max_series_idx = self.series_list_data.get('totalHits')
        if self.cursor:
            self.series_id, self.module_id = mindtickle_utils.get_series_id_module_id_from_entity_id(cursor)
            self._series_idx = self._find_element_idx(self.series_list_data, self.series_id)
        else:
            self.series_id = self._get_next_series_id()
        self.series_modules_data = self._fetch_series_modules(self.series_id) if self.series_id else None
        self.max_module_idx  = self.series_modules_data.get('totalHits') if self.series_modules_data else 0
        self._module_idx = self._find_element_idx(self.series_modules_data, self.module_id) if self.module_id else 0

    def _get_element(self, data, idx):
        if not idx:
            idx = 0
        if not data:
            return None
        return data.get('hits')[idx] if data.get('totalHits') > idx else None

    def _get_next_series_id(self):
        self._series_idx = 0 if self._series_idx is None else self._series_idx + 1
        series_data = self._get_element(self.series_list_data, self._series_idx)
        return series_data.get('id') if series_data else None

    def _get_next_module_data(self):
        if not self.series_modules_data:
            self.series_modules_data = self._fetch_series_modules(self.series_id)
            self.max_module_idx  = self.series_modules_data.get('totalHits')
        if self._module_idx is None:
            self._module_idx = 0
        return self._get_element(self.series_modules_data, self._module_idx)

    def _get_next_module_id(self):
        module_data = self._get_next_module_data()
        return module_data.get('id') if module_data else None

    def _increment_module_idx(self):
        # increment the mdoule_idx
        self._module_idx = self._module_idx + 1
        if self._module_idx >= self.max_module_idx:
            self.series_id = self._get_next_series_id()
            self.series_modules_data = self._fetch_series_modules(self.series_id) if self.series_id else None
            self._module_idx = 0

    def _find_element_idx(self, data, elem_id):
        for idx, elem in enumerate(data.get('hits', [])):
            if elem.get('id') == elem_id:
                return idx
        return None

    def _fetch_content(self, url):
        resp = mindtickle_utils.get_resp('GET', url=url, headers=self.headers)
        if resp.status_code != 200:
            raise ValueError(resp.content or 'Failure to fetch assigned modules')
        return json.loads(resp.content.decode('utf-8'))

    def _fetch_series_modules(self, series_id):
        url = CONTENT_API_MODULE_LIST_URL.format(
            base_url=CONTENT_API_BASE_URL,
            series_id=series_id
        )
        return self._fetch_content(url)

    def __next__(self):
        while True:
            if not self.series_id:
                raise StopIteration
            module_data = self._get_next_module_data()
            if not module_data:
                self._increment_module_idx()
                continue
            self.module_id = module_data.get('id')
            entity = _get_entity_from_module_details(module_data, f'{self.series_id}:{self.module_id}')
            self._increment_module_idx()
            return entity

    def get_cursor(self):
        return None if not self.series_id else f'{self.series_id}:{self._get_next_module_id() or ""}'

class MindTickleAdapter:
    def __init__(self, app_settings):
        self.app_settings = app_settings
        self.auth_token = mindtickle_utils.generate_authtoken(
            secret_key=app_settings.get('content_api_secret_key'),
            api_key=app_settings.get('content_api_api_key'),
            company_id=app_settings.get('content_api_company_id')
        )
        self.headers = {'Authorization': f'Bearer {self.auth_token}'}

    def _get_field_value(self, data, field_name_to_idx, field_name):
        return data[field_name_to_idx[field_name]] if field_name_to_idx.get(field_name) is not None else None

    def _setup_entity_obj_from_row(self, data, field_name_to_idx):
        start_time = time.perf_counter()
        module_id = self._get_field_value(data, field_name_to_idx, 'ModuleId')
        series_id = self._get_field_value(data, field_name_to_idx, 'SeriesId')
        entity_id = f'{series_id}:{module_id}'
        entity_obj = self.get_module_details_int(entity_id)
        for field_name in ['ModuleName', 'SeriesName', 'StartTime', 'EndTime', 'PercentCompleted', 'Score', 'MaxScore', 'HasStarted', 'IsOverdue', 'HasFailed']:
            entity_obj.fields.append({'name': field_name, 'value': self._get_field_value(data, field_name_to_idx, field_name)})

        end_time = time.perf_counter()
        print(f"fetch entity details time: {end_time - start_time:0.4f} seconds")
        return entity_obj

    def _process_assigned_modules_resp_content(self, data, req_data):
        search_results = response_objects.CareerhubEntitySearchResultsResponseType()
        search_results.entities = []
        num_entities = req_data.get('limit')
        row_list = data.split('\n')
        csv_row = []
        for row in row_list:
            if not row:
                continue
            csv_row.append(row.split(','))
        if not csv_row or len(csv_row) <= 1:
            search_results.num_results = 0
            return search_results.to_dict()

        field_name_to_idx = {}
        for idx, field_name in enumerate(csv_row[0]):
            field_name_to_idx[field_name] = idx

        data = csv_row[1:]
        # sort based on invitedOn
        dt_fmt = '%Y-%m-%dT%H:%M:%SZ'
        sort_key_idx = field_name_to_idx['InvitedOn']
        sorted_data = sorted(
            data,
            key=(lambda x: mindtickle_utils.to_timestamp(x[sort_key_idx], dt_fmt)),
            reverse=True
        )
        # process fetching details of requested number of entites in parallel
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=int(num_entities)
        ) as executor:
            futures = [
                executor.submit(self._setup_entity_obj_from_row, row, field_name_to_idx)
                for row in sorted_data[:num_entities]
            ]
        entities_map = {}
        for future in concurrent.futures.as_completed(futures):
            entity = future.result()
            entities_map[entity.entity_id] = entity

        module_id_idx = field_name_to_idx['ModuleId']
        series_id_idx = field_name_to_idx['SeriesId']
        for row in sorted_data[:num_entities]:
            entity_id = f'{row[series_id_idx]}:{row[module_id_idx]}'
            search_results.entities.append(entities_map[entity_id])

        search_results.num_results = len(search_results.entities)
        search_results.offset = 0
        search_results.limit = search_results.num_results
        return search_results.to_dict()

    def get_assigned_modules(self, req_data):
        email = req_data.get('current_user_email')
        if not email:
            raise ValueError('Email cannot be None')

        email = self.app_settings.get('email_swap_map', {}).get(email) or email
        url = LEARNER_MODULE_URL + f"?$filter=LearnerEmailId eq '{email}'&$format=csv"
        username = self.app_settings.get('reporting_api_username')
        password = self.app_settings.get('reporting_api_password')
        start_time = time.perf_counter()
        resp = mindtickle_utils.get_resp('GET', url=url, auth=HTTPBasicAuth(username, password))
        if resp.status_code != 200:
            raise ValueError(resp.content or 'Failure to fetch assigned modules')
        end_time = time.perf_counter()
        print(f'assigned module fetch time: {end_time - start_time:0.4f} seconds')
        data = resp.content.decode('utf-8')
        return self._process_assigned_modules_resp_content(data, req_data)

    def _fetch_url_content(self, url):
        resp = mindtickle_utils.get_resp('GET', url=url, headers=self.headers)
        if resp.status_code != 200:
            raise ValueError(resp.content or f'Failure to fetch url: {url} content.')
        return json.loads(resp.content.decode('utf-8'))

    def _fetch_series_data(self, series_id):
        start_time = time.perf_counter()
        url = CONTENT_API_MODULE_LIST_URL.format(
            base_url=CONTENT_API_BASE_URL,
            series_id=series_id
        )
        series_data = self._fetch_url_content(url)
        end_time = time.perf_counter()
        print(f"fetch series_data for {series_id} time: {end_time - start_time:0.4f} seconds")
        return series_id, series_data

    def _get_search_index_obj(self):
        global modules_inv_index_g
        return modules_inv_index_g

    def _get_search_index_creation_time(self):
        global idx_create_time_secs_g
        return idx_create_time_secs_g

    def is_search_index_build_needed(self):
        time_sec = time.perf_counter()
        if not self._get_search_index_obj() or (time_sec - self._get_search_index_creation_time()) >= SECONDS_IN_A_DAY:
            return True
        return False

    def _initialize_modules_inverted_index(self):
        if not self.is_search_index_build_needed():
            return
        inv_index = inverted_index.InvertedIndex(
            index_name='Modules Index'
        )
        t0 = time.perf_counter()
        url = CONTENT_API_SERIES_LIST_URL.format(base_url=CONTENT_API_BASE_URL)
        series_list_data = self._fetch_url_content(url)
        end_time = time.perf_counter()
        print(f"fetch series_list time: {end_time - t0:0.4f} seconds")
        num_series = series_list_data.get('totalHits')
        print(f'num_series: {num_series}')
        start_time = time.perf_counter()
        # XXX limit number of series to 100 once we have a way to fetch most recent content
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=int(num_series)
        ) as executor:
            futures = [
                executor.submit(self._fetch_series_data, series.get('id'))
                for series in series_list_data.get('hits', [])
            ]
        series_data_map = {}
        for future in concurrent.futures.as_completed(futures):
            series_id, series_data = future.result()
            series_data_map[series_id] = series_data

        end_time = time.perf_counter()
        print(f"fetch all series_data time: {end_time - start_time:0.4f} seconds")
        start_time = time.perf_counter()
        num_modules = 0
        idx = 0
        idx_to_entity_id_map = {}
        module_id_set = set()
        module_name_description_set = set()
        for series_id, series_data in series_data_map.items():
            for module_data in series_data.get('hits', []):
                if module_data['id'] in module_id_set:
                    continue
                if not module_data.get('name'):
                    continue
                name_description_str = module_data.get('name') +  (module_data.get('description') or '')
                if name_description_str in module_name_description_set:
                    continue
                module_id_set.add(module_data['id'])
                module_name_description_set.add(name_description_str)
                inv_index.add_doc_to_index(
                    token_or_list=module_data.get('name'),
                    doc_id=idx
                )
                idx_to_entity_id_map[idx] = f'{series_id}:{module_data["id"]}'
                idx = idx + 1
                num_modules = num_modules + 1
        end_time = time.perf_counter()
        print(f"Add all modules to index time: {end_time - start_time:0.4f} seconds")
        print(f'num_modules: {num_modules}')
        print(f"Total index time: {end_time - t0:0.4f} seconds")
        global modules_inv_index_g
        modules_inv_index_g = inv_index
        global series_data_map_g
        series_data_map_g = series_data_map
        global idx_to_entity_id_map_g
        idx_to_entity_id_map_g = idx_to_entity_id_map
        global idx_create_time_secs_g
        idx_create_time_secs_g = time.perf_counter()

    def _find_idx_of_cursor(self, res, cursor):
        if not cursor:
            return 0
        global idx_to_entity_id_map_g
        for idx, ent in enumerate(res):
            if idx_to_entity_id_map_g.get(ent[0]) == cursor:
                return idx
        return None

    def _get_query_search_results(self, term, req_data):
        modules = response_objects.CareerhubEntitySearchResultsResponseType()
        modules.entities = []
        cursor = req_data.get('cursor')
        global modules_inv_index_g
        global series_data_map_g
        global idx_to_entity_id_map_g
        res = modules_inv_index_g.query(term, limit=30)
        idx = self._find_idx_of_cursor(res, cursor)
        if idx is None:
            modules.num_results = len(modules.entities)
            return modules.to_dict()

        num_results = req_data['limit']
        for ent in res[idx:idx+num_results]:
            # skip the entry if it is None, first entry can be None
            # when there is no search results
            if not ent[0]:
                continue
            entity_id = idx_to_entity_id_map_g[ent[0]]
            series_id, module_id = mindtickle_utils.get_series_id_module_id_from_entity_id(entity_id)
            series_data = series_data_map_g[series_id]
            module_data = next((row for row in series_data.get('hits', []) if row['id'] == module_id), None)
            entity = _get_entity_from_module_details(module_data, entity_id)
            modules.entities.append(entity)
        # To support pagination, return length of search results if there are entities being returned; if there is no entity found, return zero
        modules.num_results = len(res) if len(modules.entities) else 0
        if len(res) <= (idx + num_results):
            cursor = None
        else:
            cursor = idx_to_entity_id_map_g[res[idx + num_results][0]]
        modules.cursor = cursor
        return modules.to_dict()

    def _get_module_search_results_int(self, req_data):
        self._initialize_modules_inverted_index()
        modules = response_objects.CareerhubEntitySearchResultsResponseType()
        modules.entities = []
        cursor = req_data.get('cursor')
        if not cursor and req_data.get('start') != 0:
            # no more modules, return empty list
            modules.num_results = len(modules.entities)
            return modules.to_dict()

        if req_data.get('term'):
            return self._get_query_search_results(req_data['term'], req_data)

        max_entities = req_data['limit']
        num_entities = 0
        module_iter = ModuleIterator(self.headers, cursor)
        cursor = None
        while True:
            if num_entities >= max_entities:
                cursor = module_iter.get_cursor()
                break
            try:
                entity = next(module_iter)
                modules.entities.append(entity)
                num_entities = num_entities + 1
            except StopIteration:
                break

        # return approx. result based on number of modules on average in a series
        # for now, we will use 5 modules per series
        modules.num_results = module_iter.max_series_idx * 5
        modules.cursor = cursor
        return modules.to_dict()

    def get_module_search_results(self, req_data):
        if req_data['trigger_source'] in ['ch_homepage']:
            return self.get_assigned_modules(req_data)
        return self._get_module_search_results_int(req_data)

    def get_module_details_int(self, entity_id):
        series_id, module_id = mindtickle_utils.get_series_id_module_id_from_entity_id(entity_id)

        url = CONTENT_API_MODULE_DETAILS_URL.format(
            base_url=CONTENT_API_BASE_URL,
            series_id=series_id,
            module_id=module_id
        )
        resp = mindtickle_utils.get_resp('GET', url=url, headers=self.headers)
        if resp.status_code != 200:
            raise ValueError(resp.content or 'Failure to fetch assigned modules')
        data_dict = json.loads(resp.content.decode('utf-8'))
        return _get_entity_from_module_details(data_dict, entity_id)

    def get_module_details(self, req_data):
        entity_id = req_data['entity_id']
        entity_obj = self.get_module_details_int(entity_id)
        return entity_obj.to_dict()

"""
    - The entry point function for the app.
    - The context arg can be ignored completely
    - The event arg will contain all needed params to properly invoke your app
"""
def app_handler(event, context):
    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    print(f'Call recived for trigger_name: {trigger_name}')
    data = None

    try:
        mta = MindTickleAdapter(app_settings)
        if trigger_name == 'careerhub_entity_search_results':
            print(f'req_data: {req_data}')
            data = mta.get_module_search_results(req_data)
        elif trigger_name == 'careerhub_get_entity_details':
            data = mta.get_module_details(req_data)
    except Exception as ex:
        err_str = f'Handler for trigger_name: {trigger_name} failed with error: {str(ex)}, traceback: {traceback.format_exc()}'
        print(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data })
    }
