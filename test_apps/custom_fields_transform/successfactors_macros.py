''' SuccessFactorsAtsAdapter macros for write back, and extract and transform'''
from __future__ import absolute_import

from collections import OrderedDict

import six
import dict_utils
import list_utils
import adapter_macros
import str_utils
import time
import time_utils
import datetime

APPL_ASSESSMENT_SCORE_COMPONENTS = {
    'Score': 'score',
    'Recommendation Details': 'recommendation_details',
    'Completed Evaluations': 'completed_evaluations',
    'Candidate Report': 'candidate_report',
    'Last Updated': 'last_updated'
}

MAX_DATE_THRESHOLD_IN_YEARS = 100

def extract_recruiting_team_followers(entity_json, recruiting_teams, ats_role='recruiter'):
    """---
    description: >
        Function to extract recruiting team followers and assign role to team members
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        recruiting_teams:
            anyOf:
                    - type: list
                    title: List of teams
                    type: string
                    - type: dict
                    title: Map of team name to role
                    map_fields:
                        key_title: Team Name
                        value_title: Role
        role:
            type: string
            description: (Optional) This role will be applied if the recruiting teams is a list
            examples:
                    - recruiter
                    - hiring_manager
    """
    if not entity_json or not recruiting_teams:
        raise ValueError('Missing entity_json or recruiting_teams kwarg')
    if not isinstance(recruiting_teams, (list, dict, OrderedDict)):
        raise Exception('recruiting_teams must be a list or dict')

    if isinstance(recruiting_teams, list):
        recruiting_teams_map = {t: ats_role for t in recruiting_teams}
    else:
        recruiting_teams_map = recruiting_teams
    followers = []
    for team, role in six.iteritems(recruiting_teams_map):
        if entity_json.get(team) and entity_json[team].get('results'):
            for t in entity_json[team]['results']:
                followers.append({
                    'name': '{} {}'.format(t['firstName'], t['lastName']),
                    'email': t['email'].strip() if t['email'] else None,
                    'ats_roles': [role]
                })
    return followers

def extract_picklist_field(entity_json, picklist_field, lowercase=False):
    """---
    description: >
        Extract the value of picklist field. We look for the specific picklist field (input) inside the entity_json.
        We fetch results inside it. Then, we iterate over this and look for "results" key inside "picklistLabels".
        We return the first "value" where the "locale" starts with "en_"
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        picklist_field:
            type: string
            description: Picklist Field Name.
            examples:
                    - "city"
                    - "state"
        lowercase:
            type: boolean
            description: Will convert to lowercase if set to true.
            default: false
    """
    if not entity_json or picklist_field is None:
        raise ValueError('Missing entity_json or picklist_field')

    val = None
    results = (entity_json.get(picklist_field) or {}).get('results') or [entity_json.get(picklist_field) or {}]
    for s in results:
        for label in s.get('picklistLabels', {}).get('results') or []:
            if label['locale'].startswith('en_'):
                val = label['label'] if not lowercase else label['label'].lower()
                break
    return val

def extract_inside_work_experience(entity_json, inside_exp_key, company_key, title_key, description_key, location_key):
    """---
    description: >
        This macro is used to extract inside work experience value, given 5 required inputs     - inside_exp_key, company_key, title_key,
        description_key and location_key. Returns a list of AtsExperience objects dictionaries.
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        inside_exp_key:
            type: string
            description: Inside experience key
        company_key:
            type: string
            description: Company key
        title_key:
            type: string
            description: Title key
        description_key:
            type: string
            description: Description key
        location_key:
            type: string
            description: Location key
    """
    import successfactors_utils

    if not entity_json:
        raise ValueError('Missing entity_json')

    candidate_json = entity_json
    results = candidate_json.get(inside_exp_key, {}).get('results', [])
    experience = []
    for e in results:
        expr_dict = successfactors_utils.extract_experience(experience=e,
                                                            company_key=company_key,
                                                            title_key=title_key,
                                                            description_key=description_key,
                                                            location_key=location_key)
        if not expr_dict or (not expr_dict.get('company') and not (expr_dict.get('title') or expr_dict.get('description'))):
            continue
        experience.append(expr_dict)
    return experience

def extract_parent_picklist_field(entity_json, picklist_field, parent_levels, lowercase=False, separator=','):
    """---
    description: >
        Extract the value of picklist field at a parent level
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        picklist_field:
            type: string
            description: Picklist Field Name.
            examples:
                - "city"
                - "state"
        parent_levels:
            type: integer
            description: Parent Level.
            examples:
                - "city"
                - "state"
        lowercase:
            type: boolean
            description: Will convert to lowercase if set to true.
            default: false
        separator:
            type: string
            description: separator used to join the multiple values.
            default: ','
    """
    if not entity_json:
        raise ValueError('Missing entity_json')
    if not picklist_field or not parent_levels:
        raise ValueError('picklist_field or parent_levels cannot be None')

    picklist_values = []
    for s in entity_json.get(picklist_field, {}).get('results') or []:
        field_values = []
        for _ in range(0, parent_levels + 1):
            for label in s.get('picklistLabels', {}).get('results') or []:
                if label['locale'].startswith('en_'):
                    val = label['label'] if not lowercase else label['label'].lower()
                    field_values.append(val)
                    break
            s = s.get('parentPicklistOption') or {}
        picklist_values.append(list_utils.join(field_values, join_char=separator))
    return picklist_values


def extract_and_match(entity_json, expected_result, picklist_field=None, field=None, data_path=None, lowercase=False):
    """---
    description: >
        Return True if value matches expected_result.
        Only one of picklist_field or field or data_path should be specified to extract the value.
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        picklist_field:
            type: string
            description: Picklist Field Name. We use the macro "extract_picklist_field" to find the value if this input is specified.
            examples:
                - "confidencial"
        field:
            type: string
            description: Field Name. If field name is specified, we look for the field recursively inside the entity object until we find it.
        data_path:
            type: string
            description: Data path in entity json data.
        expected_result:
            type: string
            description: Expected Result.
            examples:
                - "yes"
        lowercase:
            type: boolean
            description: Will convert to lowercase if set to true.
            default: False
    """
    if not entity_json or not expected_result:
        raise ValueError('Missing entity_json or expected_result')
    if not (picklist_field or field or data_path):
        raise ValueError('One of field, picklist_field, or data_path must be not be None')

    expected_result = expected_result
    if field:
        return expected_result == list_utils.finditem(entity_json, field)
    if picklist_field:
        return expected_result == extract_picklist_field(entity_json, picklist_field)
    if data_path:
        return expected_result == dict_utils.lookup_jsonpath(entity_json, data_path)

    return False

def extract_and_remap(entity_json, value_map, picklist_field=None, field=None, data_path=None):
    """---
    description: >
        value can be extracted using picklist_field or field or data_path.
        extracted value will be remapped using value_map
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        picklist_field:
            type: string
            description: Picklist Field Name.
            examples:
                - "confidencial"
        field:
            type: string
            description: Field Name.
            lowercase:
            type: boolean
            description: Will convert to lowercase if set to true.
            default: false
        data_path:
            type: string
            description: Data path in entity json data.
        value_map:
            type: object
            map_fields:
                key_title: Map (From)
                value_title: Map (To)
            description: It will be a map of key: value pairs.
            examples:
                - "{'m': 'Male', 'f': 'Female'}"
    """
    if not entity_json or not value_map:
        raise ValueError('Missing entity_json or value_map kwarg')
    if not (picklist_field or field or data_path):
        raise ValueError('One of field, picklist_field, or data_path must be a kwarg')

    field_val = None
    if field:
        field_val = list_utils.finditem(entity_json, field)
    elif picklist_field:
        field_val = extract_picklist_field(entity_json, picklist_field)
    elif data_path:
        field_val = dict_utils.lookup_jsonpath(entity_json, data_path)

    if not field_val:
        return None

    return adapter_macros.remap_value({'arg': field_val}, field_name='arg', value_map=value_map)

def extract_from_field_list(entity_json, field_list):
    """---
    description: >
        value can be extracted using picklist_field or data_path.
        first non empty field value will be returned.
        if field ends with '/picklistLabels' it will be treated as picklist field else it is data_path.
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        field_list:
            type: list
            description: >
                List of Fields.
                if field ends with '/picklistLabels' it will be treated as picklist field else it is data_path.
            list_items:
                type: string
                examples:
                    - 'hiringBand/picklistLabels'
                    - 'subbands/picklistLabels'
                    - 'filter13/picklistLabels'
    """
    if not entity_json or not field_list:
        raise ValueError('Missing entity_json or field_list kwarg')

    for field in field_list:
        if field.endswith('/picklistLabels'):
            field_val = extract_picklist_field(
                entity_json, **{'picklist_field': str_utils.rchop(field, '/picklistLabels')})
        else:
            field_val = dict_utils.lookup_jsonpath(entity_json, field)
        if field_val:
            return field_val

    return None

def extract_and_map_contact_consent(entity_json, contact_consent_mapping):
    """---
    description: >
        Extract and map contact consent. We look for "shareProfile" inside the raw value passed to this macro.
        Then, we use the extracted value for "shareProfile" and look for it inside the map you have created for Contact Consent.
        We return None if the entity is not found inside this mapping.
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        contact_consent_mapping:
            type: object
            map_items:
                key_title: Share Profile
                value_title: Contact Consent
            description: it will be a map of key: value pairs.
    """
    if not entity_json or not isinstance(contact_consent_mapping, (dict, OrderedDict)):
        raise ValueError('Missing entity_json or incorrect contact_consent_mapping')

    raw_share_profile = entity_json.get('shareProfile')
    return (contact_consent_mapping or {}).get(raw_share_profile, None)

def _get_location_from_resp(resp, location_attrs):
    if location_attrs:
        return list_utils.join([list_utils.finditem(resp, attr) for attr in location_attrs], join_char=', ')

    location_name = list_utils.finditem(resp, 'name')
    location_code = list_utils.finditem(resp, 'externalCode')
    if location_name and location_code:
        return '{} ({})'.format(location_name, location_code)
    return location_name

def _get_locations(location_objlist, obj_type, location_attrs, primary_first=None):
    location_list = dict_utils.lookup_jsonpath(location_objlist, '{}.results'.format(obj_type), default=[])
    locations = []
    # We sort only if primary_first is True, otherwise we return locations in the order they are returned by successfactors
    if primary_first is True:
        primary_locations = []
        non_primary_locations = []
        for obj in location_list:
            loc_obj = _get_location_from_resp(obj, location_attrs)
            if loc_obj:
                if obj.get('isPrimary'):
                    primary_locations.append(loc_obj)
                else:
                    non_primary_locations.append(loc_obj)
        locations.extend(primary_locations)
        locations.extend(non_primary_locations)
    else:
        for obj in location_list:
            loc_obj = _get_location_from_resp(obj, location_attrs)
            if loc_obj:
                locations.append(loc_obj)
    return list_utils.unique_list(locations)

def get_disclaim_date():
    """---
    description: >
        Get disclaim date. returns '/Date({}000+0000)/'.format(int(time.time()))
    """
    return '/Date({}000+0000)/'.format(int(time.time()))

def get_disclaim_sign(entity_json):
    """---
    description: >
        Returns true if any application source or source_type is employee or applied
        expected entity_json is candidate json entity
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
    """
    # If application is being created on behalf of the applicant, set the disclaimer date.
    candidate = entity_json
    sources = ['employee', 'applied']
    return bool(any(1 for a in candidate['applications'] or [] if a['source'] in sources or a['source_type'] in sources))

def extract_app_assessment_details(entity_json, expr):
    """---
    description: >
        extract application assessment details. it will output the list of value of vendor_code,
        score, recommendation_details, completed_evaluations, last_updated
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        expr:
            type: string
            description: >
                expression to find job application assessment order
            examples:
                - jobApplicationAssessmentOrder
    """
    assessment_details_list = []
    job_appl_assessment_order = entity_json[expr]
    if dict_utils.safe_get(job_appl_assessment_order, 'results'):
        for assessment_order in job_appl_assessment_order['results']:
            assessment_details_dict = {'vendor_code': assessment_order['vendorCode']}
            if dict_utils.safe_get(dict_utils.safe_get(assessment_order, 'assessmentReport'), 'results'):
                max_assessment_report = max(assessment_order['assessmentReport']['results'],
                                            key=lambda x: int(dict_utils.safe_get(x, 'id')))
                if dict_utils.safe_get(dict_utils.safe_get(max_assessment_report, 'assessmentReportDetail'), 'results'):
                    for item in max_assessment_report['assessmentReportDetail']['results']:
                        if item['scoreComponent'] in APPL_ASSESSMENT_SCORE_COMPONENTS:
                            assessment_details_dict[APPL_ASSESSMENT_SCORE_COMPONENTS[item['scoreComponent']]] = item['scoreValue']
            assessment_details_list.append(assessment_details_dict)
    return assessment_details_list


def extract_date_field(entity_json, field_name, date_format='%d-%b-%Y'):
    """---
    description: >
        Macro to fetch any custom date for any string date field. It converts
        the specified date field into date object using the date format given.
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        field_name:
            description: >
                The jsonpath of the specified field in the entity_json object.
            type: string
        date_format:
            description: >
                The date format of the field specified.
            type: string
    type: object
    """
    if not entity_json or not field_name:
        raise ValueError('Missing entity_json or field_name')
    field_value = dict_utils.lookup_jsonpath(entity_json, field_name)
    return time_utils.date_obj_from_str(field_value, [date_format])

def extract_standard_date_field(entity_json, field_name, date_format):
    """---
    description: >
        Macro to fetch any custom date field in STANDARD successfactors date
        format for any date field in eightfold "/Date(1397433600000)/"
    parameters:
        entity_json:
            type: dict
            description: the 'object' a value will be extracted from
        field_name:
            description: >
                The jsonpath of the specified field in the entity_json object.
            type: string
        date_format:
            description: >
                Configure this if you need the date in a specific format. Else
                it return the date object.
            type: string
    """
    if not entity_json or not field_name:
        raise ValueError('Missing entity_json or field_name kwarg')
    field_value_str = dict_utils.lookup_jsonpath(entity_json, field_name)
    if field_value_str and 'Date' in field_value_str:
        from ats import successfactors_utils
        field_value_dt = successfactors_utils.extract_seconds(field_value_str)
        max_ts_threshold = time_utils.to_timestamp(datetime.datetime.now() + datetime.timedelta(days=365 * MAX_DATE_THRESHOLD_IN_YEARS))
        if max_ts_threshold and field_value_dt > int(max_ts_threshold):
            return None
        if date_format:
            return field_value_dt if date_format == 'epoch' else time_utils.timestamp_to_str(field_value_dt, date_fmt=date_format) # return formatted date
        return time_utils.date_obj_from_seconds(field_value_dt)
    return None
