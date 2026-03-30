import six
import json
import datetime

class EFBaseResponse(object):
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


class ProfileCourseAttendanceResponseType(EFBaseResponse):
    def __init__(self):
        super(ProfileCourseAttendanceResponseType, self).__init__()
        self.group_id = None
        self.title = None
        self.description = None
        self.course_type = None
        self.language = None
        self.difficulty = None
        self.start_date = None
        self.completion_date = None
        self.course_url = None
        self.provider = None
        self.is_internal = None
        self.status = None
        self.points_earned = None
        self.verified = None
        self.medium = None
        self.data_json = None

class RecommendedCourseResponseType(EFBaseResponse):
    def __init__(self):
        super(RecommendedCourseResponseType, self).__init__()
        self.group_id = None
        self.lms_course_id = None
        self.title = None
        self.description = None
        self.course_type = None
        self.language = None
        self.difficulty = None
        self.duration_hours = None
        self.published_date = None # unix timestamp
        self.course_url = None
        self.status = None
        self.category = None
        self.image_url = None
        self.provider = None
        self.skills = None
        self.lms_data = None

class CourseDetailsResponseType(RecommendedCourseResponseType):
    def __init__(self):
        super(CourseDetailsResponseType, self).__init__()
