import unittest
from parameterized import parameterized
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa


class RecommendationTriggerLimitationsTest(unittest.TestCase):
    """
    Given valid term
    test that a response returning by recommendation_trigger_limitations function is equal to expected value
    """
    @parameterized.expand([
        ["Microsoft Office", "", "", False],
        ["", "ch_jobs", "", False],
        ["", "ch_projects", "", False],
        ["", "ch_homepage", "", True],
        ["", "ch_career_planner", "", True],
        ["", "", "", True],
        ["", "", 10, False],
    ])
    def test_recommendation_trigger_limitations_valid_term(self, term, triggerSrc, cursor, expected):
        # set term
        request_data = {"term": term, "trigger_source": triggerSrc, "cursor": cursor}
        # calling the function which should return true
        response = lambda_function.recommendation_trigger_limitations(request_data)
        # to check expected is equal to response
        self.assertEqual(expected, response)
