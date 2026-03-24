import unittest
from parameterized import parameterized
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa


class ConcateSkillsTest(unittest.TestCase):
    """
    Given empty str and array of skills
    test that a returning string by get_email function should be matched with expected string
    """

    @parameterized.expand(
        [
            [
                "",
                "Business Strategy,Management,Software Development,Project Management,Frameworks",
            ],
            [
                "Soft Skills",
                "Soft Skills,Business Strategy,Management,Software Development,Project Management,Frameworks",
            ],
        ]
    )
    def test_concate_skills_str(self, arg1, expected):
        # set empty str
        str = arg1
        # set array of skills
        skills = [
            {"name": "Business Strategy"},
            {"name": "Management"},
            {"name": "Software Development"},
            {"name": "Project Management"},
            {"name": "Frameworks"},
        ]
        # calling the function which will return concat string
        concat_str = lambda_function.concate_skills(str, skills)
        # to check concat str is equal to expected
        self.assertEqual(expected, concat_str)
