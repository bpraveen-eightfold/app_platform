from enum import Enum


class SupportedExporters(Enum):
    SFTP = 'sftp'
    EMAIL = 'email'
    FILE = 'file'


class ConfiguredFrequecy(Enum):
    HOURLY = 'HOURLY'
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'


class FieldSeps(Enum):
    COMMA = ','
    PIPE = '|'
    CTRL_A = '\001'


RESULT_FIELD_DEFAULT_DELIMITER = FieldSeps.COMMA.value
field_separators = {'CTRL-A': FieldSeps.CTRL_A.value, '|': FieldSeps.PIPE.value, ',': FieldSeps.COMMA.value}


class MetaExtension(Enum):
    META = 'meta'


URLS = {
    'profile_gov': 'https://apiv2.eightfold-gov.ai/api/v2/core/profiles',
    'employee_gov': 'https://apiv2.eightfold-gov.ai/api/v2/core/employees',
    'user_gov': 'https://apiv2.eightfold-gov.ai/api/v2/core/users',
    'profile_eu': 'https://apiv2.eightfold-eu.ai/api/v2/core/profiles',
    'employee_eu': 'https://apiv2.eightfold-eu.ai/api/v2/core/profiles?limit=100&filterQuery=candidateInsights:employee',
    'profile_us': 'https://apiv2.eightfold.ai/api/v2/core/profiles',
    'employee_us': 'https://apiv2.eightfold.ai/api/v2/core/employees'
}

ACCESS_TOKEN_URLS = {
    'gov': 'https://apiv2.eightfold-gov.ai/oauth/v1/authenticate',
    'us': 'https://apiv2.eightfold.ai/oauth/v1/authenticate',
    'eu': 'https://apiv2.eightfold-eu.ai/oauth/v1/authenticate'
}

ACCESS_BASIC_TOKEN = {
    'gov': 'Basic UnRRM2NPa1doMlVtVHBHSFlobnl6YnhSOjU1UXcxYXZKclI3VjNRdUMxN2VwSWFadDFEd2hmaG5xempieFE4QlVRMUtFZzFzRg==',
    'us': 'Basic MU92YTg4T1JyMlFBVktEZG8wc1dycTdEOnBOY1NoMno1RlFBMTZ6V2QwN3cyeUFvc3QwTU05MmZmaXFFRDM4ZzJ4SFVyMGRDaw==',
    'eu': 'Basic Vmd6RlF4YklLUnI2d0tNZWRpdVZTOFhJOmdiM1pjYzUyUzNIRmhsNzd5c2VmNTgyOG5jVk05djl1dGVtQ2tmNVEyMnRpV1VJVQ=='
}

QUESTION_LISTS = [
    "What_type_of_phone_number_is_the_number_listed_above",
    "Are_you_legally_authorized_to_work_for_our_company_in_the_location_which_you_applied_",
    "Do_you_now__or_will_you_in_the_future__require_sponsorship_for_work_authorization_permit_or_permanent_residency_",
    "Preferred_name",
    "Physical_address",
    "Are_you_willing_to_relocate_",
    "Please_select_one_of_the_gender_options",
    'Please_select_one_of_the_race_ethnicity_options',
    'Please_select_one_of_the_veteran_status_options',
    'Please_select_one_of_the_disability_options',
    "Do_you_have_a_non_compete_",
    "In_order_to_assist_the_company_in_complying_with_export_control_and_sanctions_laws_and_regulations__please_indicate_in_which_countries_you_hold_citizenship_or_have_held_citizenship__please_select_all_that_apply____Please_select__Not_Applicable__if_this_does_not_apply_"
]


QUESTION_LISTSS = [
    "What type of phone number is the number listed above",
    "Are you legally authorized to work for our company in the location which you applied?",
    "Do you now, or will you in the future, require sponsorship for work authorization/permit or permanent residency?",
    "Preferred name",
    "Physical address",
    "Are_you_willing_to_relocate_",
    "Please select one of the gender options",
    'Please select one of the race/ethnicity options',
    'Please select one of the veteran status options',
    'Please select one of the disability options',
    "Do_you_have_a_non_compete_",
    "In_order_to_assist_the_company_in_complying_with_export_control_and_sanctions_laws_and_regulations__please_indicate_in_which_countries_you_hold_citizenship_or_have_held_citizenship__please_select_all_that_apply____Please_select__Not_Applicable__if_this_does_not_apply_"
]
a = ["glog", "requests", "pysftp"]