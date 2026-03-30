import unittest
from parameterized import parameterized
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa


class CheckWithFqSkillsTest(unittest.TestCase):
    """
    Given skills and fq skills set
    test that a any skill id should be matched with any fq skill
    """

    @parameterized.expand([
        ["Business Strategy", True],
        ["Software Development", False]
    ])
    def test_check_with_fq_skills_matched_skill(self, arg1, expected):
        # set skills set
        skills = [
            {"type": "skills", "id": "Project Manager"},
            {"type": "skills", "id": "Business Strategy"},
        ]
        # set fq_skills set
        fq_skills = [{"name": arg1}, {"name": "Management"}]
        # calling the function which will return true
        matched = lambda_function.check_with_fq_skills(skills, fq_skills)
        # check matched true
        self.assertEqual(expected, matched)
