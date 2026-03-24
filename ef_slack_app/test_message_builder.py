from __future__ import absolute_import

import unittest
import message_builder


class TestMessageBuilder(unittest.TestCase):
    def test_add_tracking_query_parameter(self):
        url = "https://app.eightfold.ai/v2/interview_feedback/RnpOMr5g"
        params = {'messenger': 'slack'}
        tracked_url = message_builder.add_tracking_query_parameter(url, params)
        assert tracked_url == "https://app.eightfold.ai/v2/interview_feedback/RnpOMr5g?messenger=slack"

        url = "https://app.eightfold.ai/v2/interview_feedback/RnpOMr5g?random=xyz"
        params = {'messenger': 'slack'}
        tracked_url = message_builder.add_tracking_query_parameter(url, params)
        assert tracked_url == "https://app.eightfold.ai/v2/interview_feedback/RnpOMr5g?random=xyz&messenger=slack"
