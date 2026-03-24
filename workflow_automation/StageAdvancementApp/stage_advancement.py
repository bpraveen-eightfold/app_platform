import traceback

from jinja2 import TemplateError, nativetypes


class StageAdvancement:
    def __init__(self, request_data):
        self.request_data = request_data

    def substitute_template(self, template_str):
        env = nativetypes.NativeEnvironment()
        subst_string = template_str
        try:
            filter_template = env.from_string(template_str)
            subst_string = filter_template.render(**self.request_data)
        except TemplateError:
            print('Unable to substitute template: {}'.format(template_str), traceback.format_exc())
        return subst_string

    def substitute_values_in_dict(self, template_dict):
        result_dict = {}
        for key, value in template_dict.items():
            if isinstance(value, dict):
                value = self.substitute_values_in_dict(value)
            elif isinstance(value, str):
                value = self.substitute_template(value)
            result_dict[key] = value
        return result_dict

    def evaluate_rule(self, rule_dict):
        current_stage = self.request_data.get('stage')
        previous_stage = self.request_data.get('previous', {}).get('stage')
        allowed_current_stages = rule_dict.get('current_stages', [])
        allowed_previous_stages = rule_dict.get('previous_stages', [])
        if allowed_current_stages and current_stage not in allowed_current_stages:
            return False
        if allowed_previous_stages and previous_stage not in allowed_previous_stages:
            return False
        return True
