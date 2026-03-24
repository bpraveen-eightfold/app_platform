import unittest

from stage_advancement import StageAdvancement


class TestStageAdvancement(unittest.TestCase):

    def setUp(self):
        request_data = {
            'variable': 'testing',
            'parent': {
                'child_1': 101,
                'child_2': {
                    'g_child_1': '202'
                }

            }
        }
        self.stage_advancement = StageAdvancement(request_data)

    def test_no_substitution(self):
        template_str = 'something'
        subst_string = self.stage_advancement.substitute_template(template_str)
        assert subst_string == 'something'

    def test_successful_substitution(self):
        template_str = "{{'something'}}"
        subst_string = self.stage_advancement.substitute_template(template_str)
        assert subst_string == 'something'

        template_str = "{{variable == 'testing'}}"
        subst_string = self.stage_advancement.substitute_template(template_str)
        assert subst_string is True

        template_str = "{{parent.child_1 == 101}}"
        subst_string = self.stage_advancement.substitute_template(template_str)
        assert subst_string is True

        template_str = "{{parent.child_2.g_child_1 == '202'}}"
        subst_string = self.stage_advancement.substitute_template(template_str)
        assert subst_string is True

    def test_unsuccessful_substitution(self):
        template_str = "{variable == 'testing'}"
        subst_string = self.stage_advancement.substitute_template(template_str)
        assert subst_string is not True

        template_str = "{variable == 'testing'"
        subst_string = self.stage_advancement.substitute_template(template_str)
        assert subst_string is not True


def test_substitute_values_in_dict():
    template_dict = {
        "template_name": "some_name",
        "email_to": "{{profile_email_id}}",
        "email_from": "{{hm_email_id}}",
        "template_type": "whatsapp",
        "reply_to": "",
        'cc': "[{{interviewer_email_id}}, {{recruiter_email_id}}]",
        'job_details': {
            'location': '{{job_location}}',
            'skills': {
                'required_skills': '{{job_required_skills}}',
                'preferred_skills': '{{job_preferred_skills}}'
            }
        }

    }
    request_data = {
        'profile_email_id': 'abs@test.com',
        'hm_email_id': 'hm@test.com',
        'recruiter_email_id': 'recruiter@test.com',
        'interviewer_email_id': 'interviewer@test.com',
        'job_location': 'Noida',
        'job_required_skills': ['python', 'git'],
        'job_preferred_skills': ['react', 'HTML']
    }
    stage_advancement = StageAdvancement(request_data)
    result_dict = stage_advancement.substitute_values_in_dict(template_dict)
    assert result_dict['email_to'] == request_data['profile_email_id']
    assert result_dict['email_from'] == request_data['hm_email_id']
    assert all(x in result_dict['cc'] for x in [request_data['recruiter_email_id'], request_data['interviewer_email_id']])

    job_details = result_dict['job_details']
    assert job_details['location'] == request_data['job_location']
    assert job_details['skills']['required_skills'] == request_data['job_required_skills']
    assert job_details['skills']['preferred_skills'] == request_data['job_preferred_skills']
