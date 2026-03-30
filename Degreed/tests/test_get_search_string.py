import unittest
from parameterized import parameterized
from fake_data import inputs
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa

inputData = inputs.app()
request_data = inputData.get("request_data", {})
# skills sample
skills = [
    {"name": "Business Strategy"},
    {"name": "Management"},
    {"name": "Software Development"},
    {"name": "AWS"},
    {"name": "Proofing"}
]
# Profile skills
profile_skills = [{"name": "Management"}]


class SearchStringTest(unittest.TestCase):
    """
    Given matched term and fq skills with course skill
    test that a skill matched by calling get_search_string "check_with_fq_skills" skills
    """
    sample_fq = {"required_skills": skills, "profile_skills": profile_skills}
    sample_fq_2 = {"required_skills": [{"name": "Microsoft Office"}],
                   "profile_skills": profile_skills}

    @parameterized.expand([
        ["Microsoft Office", sample_fq, True],
        ["Software Development", sample_fq, False],
        ["", sample_fq, False],
        ["", sample_fq_2, True]
    ])
    def test_get_search_string_skill_matched(self, term, fq, expected):
        # set term with request data
        request_data.update({"term": term, "fq": fq})
        # set skills set for match term
        skills = [{"type": "skills", "id": "Microsoft Office"}]
        # calling the function which will return true
        skill_matched = lambda_function.get_search_string(
            request_data, lambda_function.check_with_fq_skills, skills
        )
        # assert skill matched true
        self.assertEqual(skill_matched, expected)

    """
    Given matched term and fq skills with course skill
    test that a skill matched by calling get_search_string "concate_skills" term skills
    """
    sample_fq = {"required_skills": skills, "profile_skills": profile_skills}
    sample_fq_2 = {"project_skills": [{"name": "Management"}, {"name": "AWS"}, {"name": "Proofing"}],
                   "profile_skills": profile_skills}
    sample_fq_3 = {
        "project_skills": [{"name": "AWS"}, {"name": "Proofing"}],
        "profile_skills": profile_skills}
    sample_fq_4 = {
        "position_skills": [{"name": "Management"}, {"name": "AWS"},
                            {"name": "Proofing"}, {"name": "Project Management"}],
        "profile_skills": profile_skills}
    sample_fq_5 = {"profile_skills": [{"name": "Management"}, {"name": "Business Strategy"}]}

    @parameterized.expand([
        ["Microsoft Office", sample_fq, "Microsoft Office"],
        ["", sample_fq, "Business Strategy,Proofing,Software Development,AWS"],
        ["", sample_fq_2, "Proofing,AWS"],
        ["", sample_fq_3, "Proofing,AWS"],
        ["", sample_fq_4, "Proofing,AWS,Project Management"],
        ["", sample_fq_5, "Management,Business Strategy"],
    ])
    def test_get_search_string_concate_skills(self, term, fq, expected):
        # set term with request data
        request_data.update({"fq": fq, "term": term})
        # calling the function which will return true or false
        skill = lambda_function.get_search_string(
            request_data, lambda_function.concate_skills, term
        )
        if term and term is not None:
            # assert skill matched or not
            self.assertEqual(expected, skill)
        else:
            print(skill)
            # assert skill matched length or not
            self.assertEqual(len(expected), len(skill))
