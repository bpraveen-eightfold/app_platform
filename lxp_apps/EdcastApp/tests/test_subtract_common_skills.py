import unittest
from parameterized import parameterized
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa

# set other skills
skills_sample = [
    {"name": "Business Strategy"},
    {"name": "Management"},
    {"name": "Software Development"},
    {"name": "Project Management"},
    {"name": "Frameworks"},
    {"name": "Design Analysis"},
]

expected_sample_1 = [
    {"name": "Business Strategy"},
    {"name": "Software Development"},
    {"name": "Project Management"},
    {"name": "Design Analysis"},
]

expected_sample_2 = [
    {"name": "Business Strategy"},
    {"name": "Management"},
    {"name": "Software Development"},
    {"name": "Project Management"},
    {"name": "Frameworks"},
    {"name": "Design Analysis"},
]


class SubtractCommonSkillsTest(unittest.TestCase):
    """
    Given profile skills and other skills set
    test that a returning skills set by subtract_common_skills function should not have any profile skill
    """

    @parameterized.expand(
        [
            [
                [{"name": "Management"}, {"name": "Frameworks"}],
                skills_sample,
                expected_sample_1,
            ],
            [[{"name": "Management"}], [], []],
            [[], skills_sample, expected_sample_2],
            [[], [], ""],
        ]
    )
    def test_subtract_common_skills_uncommon(self, profile_skills, skills, expected):
        # set profile skills
        profile_skills = profile_skills
        # set other skills
        other_skills = skills
        # calling the function which will return skills set
        uncommon_skills = lambda_function.subtract_common_skills(
            profile_skills, other_skills
        )

        # check length of expected skills and length of un common skills
        self.assertEqual(len(expected), len(uncommon_skills))
