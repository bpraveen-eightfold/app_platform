import unittest
from parameterized import parameterized
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa


class RecommendedCourseCursorListTest(unittest.TestCase):
    """
    Given endlimit, next_batch, offset, course_limit, course_len, recomm_list, con_list
    test that a response returning by recommended_course_cursor_list function is equal as expected
    """
    @parameterized.expand([
        [0, 8, 8, 25, 8],
        [0, 12, 12, 25, 0],
        [10, 12, 12, 25, 12],
        [5, 6, 6, 10, 6]
    ])
    def test_recommended_course_cursor_list(self, start, recomm_course_len, recomm_num, con_num,
                                            expect_next_batch):
        # set fake input data
        offset = start
        endlimit = offset + 10
        next_batch = 0
        course_limit = 10
        recomm_list = [{"type": "required-learning"}] * recomm_num
        con_list = [{"type": "content"}] * con_num

        # calling the function which will return recommended_list and cursor
        recommended_list_cursor = lambda_function.recommended_course_cursor_list(
            recomm_course_len, endlimit, course_limit, offset, next_batch, recomm_list, con_list
        )

        # assert statement to check expected and response values
        response_next_batch = recommended_list_cursor.get("next_batch")
        self.assertEqual(expect_next_batch, response_next_batch)
