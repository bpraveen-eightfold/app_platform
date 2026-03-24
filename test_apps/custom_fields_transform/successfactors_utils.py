from __future__ import absolute_import

import dict_utils
import regex_utils

BLACKLISTED_TOKENS = set(['UNSPECIFIED'])


def extract_seconds(ats_date_str, default=0):
    """Returns the time in seconds from the string of this format "/Date(1397433600000)/"""
    if not ats_date_str:
        return default
    # In some rare cases, the date could begin with '-' sign, that is bad data which should
    # be ignored.
    match = regex_utils.search('(-*)([0-9]+)', ats_date_str)
    if not match or match.group(1):
        return default
    return int(match.group(2)) // 1000


def extract_experience_dict(experience, company_key, title_key, description_key, location_key, start_date_key='startDate', end_date_key='endDate'):
    expr_dict = {}
    company = dict_utils.safe_get(experience, company_key)
    expr_dict['company'] = company if company and company not in BLACKLISTED_TOKENS else None
    title = dict_utils.safe_get(experience, title_key)
    # In certain cases, titles are incorrectly parsed as parts of the resume. We want to instead set the description.
    if title and title not in BLACKLISTED_TOKENS:
        if len(title) < 200:
            expr_dict['title'] = title
        else:
            expr_dict['description'] = title

    if not expr_dict['company'] and not (expr_dict['title'] or expr_dict['description']):
        return None
    description = dict_utils.safe_get(experience, description_key)
    if description and description not in BLACKLISTED_TOKENS:
        expr_dict['description'] = description
    location = dict_utils.safe_get(experience, location_key)
    expr_dict['location'] = location if location and location not in BLACKLISTED_TOKENS else None
    expr_dict['start_ts'] = extract_seconds(dict_utils.safe_get(experience, start_date_key))
    expr_dict['end_ts'] = extract_seconds(dict_utils.safe_get(experience, end_date_key))
    return expr_dict
