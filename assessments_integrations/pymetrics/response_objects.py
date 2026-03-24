import six
import json
import datetime

class EFBaseReponse(object):
    def __init__(self):
        pass

    @staticmethod
    def _json_serialize(obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return {k: v for k, v in six.iteritems(obj.__dict__)}

    def to_json(self):
        return json.dumps(self, default=EFBaseReponse._json_serialize)

    def from_json(self, json_dict):
        assert isinstance(json_dict, dict), json_dict
        for k, v in six.iteritems(json_dict):
            if v is not None and hasattr(self, k):
                setattr(self, k, v)
        return self

    def to_dict(self):
        return json.loads(self.to_json())

    # pylint: disable=unused-argument
    def validate(self, strict=True):
        return True

class EFListAssessmentsResponse(EFBaseReponse):
    """ Object to represent assessment test information on vendor system. """
    def __init__(self, assessment_id=None, name=None, duration_minutes=None, published=None):
        super(EFListAssessmentsResponse, self).__init__()
        self.id = assessment_id # unique test id in vendor system
        self.name = name # name of the test
        self.duration_minutes = duration_minutes # duration of test in minutes
        self.published = published # denotes if the test is published

class EFAssessmentInviteResponse(EFBaseReponse):
    """ Object to represent response of the invite candidate call to vendor system. """
    def __init__(self, email, vendor_candidate_id=None, test_url=None, invite_already_sent=None,
                 assessment_id=None):
        super(EFAssessmentInviteResponse, self).__init__()
        self.email = email
        self.vendor_candidate_id = vendor_candidate_id
        self.test_url = test_url
        self.invite_already_sent = invite_already_sent
        self.assessment_id = assessment_id

class EFAssessmentReportResponse(EFBaseReponse):
    """ This represents the assessment data for an application """
    def __init__(self):
        super(EFAssessmentReportResponse, self).__init__()
        self.assessment_id = None # string, identifier denoting the assessment test
        self.test_id = None # test_id for which the data is being returned
        self.email = None # string, email of the candidate
        self.status = None # string, such as outcome was satisfactory or not
        self.assigned_ts = None # unix ts, timestamp, at which assessment was sent to candidate
        self.start_ts = None # timestamp, at which test was started by candidate
        self.completed_ts = None # timestamp, the date test was taken or completed
        self.num_tests_completed = None # int, number of tests completed
        self.num_tests_total = None # int, total number of tests
        self.score = None # float
        self.score_unit = None # Unit for score value
        self.rating = None # string
        self.comments = None # string, comment or recommendation evaluation
        self.plagiarism_status = None # plagiarism status
        self.report_url = None # string
        self.last_modified_ts = None # unit ts
        self.response_json = None # stores the json response from AtsAssessment Vendor

