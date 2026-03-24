import json
import jinja2
from requests import PreparedRequest


SLACK_NOTIF_TEMPLATE_FILE_NAME='feedback_notifs_text'


def _json_str(s):
    return json.dumps(s)[1:-1]


def json_str(s):
    if isinstance(s, list):
        return list(map(_json_str, s))
    return _json_str(s)


def add_tracking_query_parameter(url, params={}):
    req = PreparedRequest()
    req.prepare_url(url, params)
    return req.url


def build_message(trigger_name, request_data):
    template_args = {
        'trigger_name': trigger_name,
        'position': request_data.get('position'),
        'requester': request_data.get('requester'),
        'reviewer': request_data.get('reviewer'),
        'candidate': request_data.get('candidateProfileRequester') if trigger_name == 'feedback_submitted' else request_data.get('candidateProfileReviewer'),
        'feedback_url': add_tracking_query_parameter(request_data.get('feedbackUrl'), {'messenger': 'slack'}) if request_data.get('feedbackUrl') else None,
        'view_feedback_url': request_data.get('viewFeedbackUrl'),
        'json_str': json_str
    }

    file = open('./templates/'+trigger_name+'.txt', 'r')
    template_str = file.read()
    file.close()
    blocks_str = jinja2.Template(template_str).render(**template_args)
    blocks = json.loads(blocks_str.replace('\t', ''), strict=False).get('blocks')

    file = open('./templates/'+SLACK_NOTIF_TEMPLATE_FILE_NAME+'.txt', 'r')
    notif_template_str = file.read()
    file.close()
    notif_text = jinja2.Template(notif_template_str).render(**template_args)
    return blocks, notif_text
