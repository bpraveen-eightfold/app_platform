import unittest
from parameterized import parameterized
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa


class CheckWithTermTest(unittest.TestCase):
    """
    Given term and skills set
    test that a term should be matched with any one skill id
    """
    @parameterized.expand([
        ["Microsoft Office", True],
        ["Software Development", False],
        ["Project Manager", False]
    ])
    def test_check_with_term_matched(self, arg1, expected):
        # set term
        term = "Microsoft Office"
        # set skills set for match term
        skills = [
            {"type": "skills", "id": arg1},
            {"type": "skills", "id": "Business Strategy"},
        ]
        # calling the function which will return true
        matched = lambda_function.check_with_term(skills, term)
        # check matched true
        self.assertEqual(expected, matched)
