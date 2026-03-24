import six
import json
import datetime

"""
Create assessment response objects that hold assessment data in your system or another system that you might be using. 
The file here contains all the possible objects that you can create. The ones that you will include in your app will depend on the triggers that your app will be using.
Next, provide this data to Eightfold through event handlers in lambda_function.py.

Note that in addition to these response objects, you can also respond to Eightfold with any of the actions listed here: https://docs.eightfold.ai/app-platform-basics/actions 
"""
class EFBaseResponse:
    def __init__(self):
        pass

    @staticmethod
    def _json_serialize(obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return {k: v for k, v in six.iteritems(obj.__dict__)}

    def to_json(self):
        return json.dumps(self, default=EFBaseResponse._json_serialize)

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

class AssessmentTestType(EFBaseResponse):
    """ 
        Object that represents response data for assessment_list_tests trigger.  
    """
    def __init__(self, test_id=None, name=None, duration_minutes=None, published=None):
        super().__init__()
        self.id = test_id # unique test id in vendor system
        self.name = name # name of the test
        self.duration_minutes = duration_minutes # duration of test in minutes
        self.published = published # denotes if the test is published(EFBaseResponse):

class AssessmentInviteCandidateResponseType(EFBaseResponse):
     # Response object for the assessment_invite_candidate trigger.
    def __init__(self, email, vendor_candidate_id=None, test_url=None, invite_already_sent=None,
                 assessment_id=None):
        super().__init__()
        self.email = email
        self.vendor_candidate_id = vendor_candidate_id
        self.test_url = test_url
        self.invite_already_sent = invite_already_sent
        self.assessment_id = assessment_id

class ApplicationAssessmentData(EFBaseResponse):
    # Response object for assessment_fetch_candidate_report trigger
    def __init__(self):
        super().__init__()
        self.assessment_id = None # string, identifier denoting the assessment test
        self.test_id = None # test_id for which the data is being returned
        self.email = None # string, email of the candidate
        self.status = None # string, where you can denote whether the assessment outcome was satisfactory or not
        self.assigned_ts = None # unix ts, timestamp, at which assessment was sent to candidate
        self.start_ts = None # timestamp, at which test was started by candidate
        self.completed_ts = None # timestamp, the date test was taken or completed
        self.num_tests_completed = None # int, number of tests completed
        self.num_tests_total = None # int, total number of tests
        self.score = None # float, score of the candidate
        self.score_unit = None # Unit used for score value
        self.rating = None # string, rating for the assessment
        self.comments = None # string, comment or recommendation evaluation
        self.plagiarism_status = None # plagiarism status
        self.report_url = None # string, URL for the assessment report
        self.last_modified_ts = None # unit ts To-do: Clarify description
        self.response_json = None # stores the json response from AtsAssessment Vendor

class AssessmentTestStatus:
    INVITED = 'invited' # candidate has been invited for the test
    NOT_INVITED = 'not_invited' # assessment has been created in the system, but no email
                                # invitation has been sent to candidate yet
    COMPLETED = 'completed' # candidate has completed the test
    REMINDER_SENT = 'reminder_sent' # reminder has been sent to the candidate
    EXPIRED = 'expired' # the test sent to the candidate has expired

class AssessmentGetLogoUrlResponseType(EFBaseResponse):
    def __init__(self):
        super().__init__()
        self.logo_url = None

class AssessmentIsWebhookSupportedResponseType(EFBaseResponse):
    def __init__(self):
        super().__init__()
        self.is_webhook_supported = None
