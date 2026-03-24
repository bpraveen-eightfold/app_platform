import pycountry
import requests
from thefuzz import process

POSITION_QUERY_LIMIT = 100


class PositionCopyCalibration:
    def __init__(self, position_id, position_name, aws_region, ef_api_key, countries=None, reference_name_suffix=None, calibration_templates=None):
        self.aws_region = aws_region
        self.ef_api_key = ef_api_key
        self.reference_name_suffix = reference_name_suffix
        self.calibration_templates = calibration_templates
        self.position_id = position_id
        self.position_name = position_name
        self.countries = countries

    def search_positions(self, position_name):
        host_name = 'api.eightfold.ai'
        if self.aws_region == 'EU':
            host_name = 'api-eu.eightfold.ai'
        POSITION_SEARCH_URL = "https://{}/v1/position/search".format(host_name)


        headers = {
            "Accept": "application/json",
            "Authorization": self.ef_api_key
        }

        filter_query = 'atsTitle:"{0}" OR hiringTitle:"{0}"'.format(position_name)
        querystring = {"limit": POSITION_QUERY_LIMIT,
                       "filterQuery": filter_query}

        response = requests.request('GET', POSITION_SEARCH_URL, headers=headers, params=querystring)
        if response.status_code != 200:
            raise Exception('Position search api returned an error: {} {}'.format(response.status_code, response.text))

        json_response = response.json()
        positions = json_response.get('results', [])
        return positions

    def get_best_match_using_fuzzywuzzy(self):
        best_match_template = process.extractOne(self.position_name, [template['name'] for template in self.calibration_templates])
        return best_match_template[0]

    def filter_templates_on_country(self):
        filtered_templates = []
        default_english_templates = []

        for template in self.calibration_templates:
            template_countries = get_countries_from_text(template['name'])
            if not template_countries:
                default_english_templates.append(template)

            common_countries = list_intersect(template_countries, self.countries, ignore_case=True)
            if common_countries:
                template['name'] = remove_substrings_from_text(template['name'], template_countries).strip()
                filtered_templates.append(template)

        return filtered_templates or default_english_templates

    def get_best_matched_template_id(self):
        if not self.calibration_templates:
            raise ValueError('No calibration template found in request_data->roles->templates')

        self.calibration_templates = self.filter_templates_on_country()
        print("filtered calibration_templates: " + ', '.join([template['name'] for template in self.calibration_templates]))
        if len(self.calibration_templates) == 1:
            return self.calibration_templates[0]['id']

        max_score_template_name = self.get_best_match_using_fuzzywuzzy()
        template_ids = [template['id'] for template in self.calibration_templates if template['name'] == max_score_template_name]
        return template_ids[0]

    def get_exact_matched_template_id(self):
        reference_name = self.position_name + ' ' + self.reference_name_suffix
        reference_positions = self.search_positions(reference_name)
        for pos in reference_positions:
            if pos.get('name') == reference_name:
                return pos['positionId']
        raise ValueError('Position not found with name as {}'.format(reference_name))


def get_countries_from_text(text):
    countries = []
    for country in pycountry.countries:
        country_attr_list = []

        try:
            country_attr_list.append(country.official_name)
        except AttributeError:
            pass

        country_attr_list.append(country.name)

        for country_attr in country_attr_list:
            if ' '+country_attr.lower()+' ' in ' '+text.lower()+' ':
                countries.extend(country_attr_list)
                break
    return countries


def remove_substrings_from_text(text, substrings):
    if not substrings:
        return text

    text = text.lower()
    for substring in substrings:
        text = text.replace(substring.lower(), '')

    return text


def list_intersect(l1, l2, ignore_case=False):
    if not l1 or not l2:
        return []
    if ignore_case:
        l1 = [_f for _f in [l.lower().strip() for l in l1 if l] if _f]
        l2 = [_f for _f in [l.lower().strip() for l in l2 if l] if _f]
    l2_s = set(l2) if not isinstance(l2, set) else l2
    return [l1_i for l1_i in l1 if l1_i in l2_s]

