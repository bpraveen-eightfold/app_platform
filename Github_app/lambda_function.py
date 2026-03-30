import json

import timeago

from constants import GITHUB_LOGO_URL
from github_connector import GithubConnector
from errors import RequestValidationError
from errors import GitHubUsernameError


REQUIRED_FIELDS = ['username', 'token', 'email_to_github_user']
NUM_RECORDS = 3

def _validate_career_hub_profile_view_request(event):
    req_data = event.get('request_data', {})
    email = req_data.get('employee_email') or req_data.get('email')
    if not email:
        raise RequestValidationError(
            message='Please provide email in request_data', status_code=400
        )

    app_settings = event.get('app_settings')
    if not app_settings:
        raise RequestValidationError(
            message='App settings cannot be empty', status_code=400
        )

    for field in REQUIRED_FIELDS:
        if not app_settings.get(field):
            raise RequestValidationError(
                message='field: {} cannot be none'.format(field), status_code=400
            )

    return app_settings, email


def _get_github_user_name(app_settings, email):
    # 1. look for explicit mapping and use that if available
    email_to_github_user = app_settings.get('email_to_github_user', {})
    user_name = email_to_github_user.get(email)
    if user_name:
        return user_name

    # 2. check if a user_name_format is provided and then try to construct the username
    # with format from email, currently email_user_name is the only variable supported in format
    # e.g. user_name_format='{email_user_name}-suffix'
    user_name_format = app_settings.get('user_name_format')
    if not user_name_format:
        raise GitHubUsernameError(message='github user not found for email {}'.format(email), status_code=200)
    email_user_name = email[:email.index('@')]
    return user_name_format.format(email_user_name=email_user_name)


def _career_hub_profile_view_handler(event, context):
    app_settings, email = _validate_career_hub_profile_view_request(event)
    user_name = _get_github_user_name(app_settings, email)
    gc = GithubConnector(app_settings)
    try:
        print('Fetching data for email: {} and github username: {}'.format(email, user_name))
        num_prs, pr_list = gc.get_prs(user_name, 'author', 'Created')
        num_reviews, reviews_list = gc.get_prs(user_name, 'reviewed-by', 'Reviewed')
        num_comments, commented_list = gc.get_prs(user_name, 'commenter', 'Commented')
        pr_list.extend(reviews_list)
        pr_list.extend(commented_list)
        # remove duplicate prs
        link_to_record = {}
        for pr in pr_list:
            if not link_to_record.get(pr.get('link')):
                link_to_record[pr['link']] = pr
        pr_list = link_to_record.values()
        pr_list = sorted(pr_list, key=lambda i:i['timestamp'], reverse=True)
        pr_list = pr_list[0:NUM_RECORDS] # pick top 3
        one_month_ago_str = gc.one_month_ago.strftime('%Y-%m-%d')
        now_str = gc.now.strftime('%Y-%m-%d')
        count = 0
        rows = []
        for pr in pr_list:
            modified_at = pr.get('timestamp')
            rows.append([{'value': pr.get('title'),
                            'link': pr.get('link')},
                            {'value': '{} {}'.format(pr.get('activity_type'), timeago.format(modified_at, gc.now) if modified_at else None)}])
            count += 1
            if count >= 3:
                break

        data = {
            'title': 'Github',
            'subtitle': '@{}'.format(user_name),
            'logo_url': GITHUB_LOGO_URL,
            'action_button': {
                'label': 'View',
                'onClick': 'window.open("https://github.com/pulls?q=is%3Apr+author%3A{user_name}+archived%3Afalse+created:{from_date}..{to_date}");'.format(
                    user_name=user_name, from_date=one_month_ago_str, to_date=now_str),
            },
            'tiles': [
                {'header': 'Pull Requests', 'value': num_prs},
                {'header': 'Reviews', 'value': num_reviews},
                {'header': 'Comments', 'value': num_comments},
            ],
            'table': {
                'headers': ['Title', 'Last Activity'],
                'rows': rows
            },
            'footer': '* over last 30 days'
        }

        print(data)

    except Exception as ex:
        print(str(ex))
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(ex) or 'Internal Error'}),
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
    }


def _default_trigger_handler(event, context):
    trigger_name = event.get('trigger_name')
    return {
        'statusCode': 400,
        'body': json.dumps({'error': 'Unsupported trigger {} specified in request'.format(trigger_name)}),
    }


TRIGGER_HANDLERS = {
    'career_hub_profile_view': _career_hub_profile_view_handler
}


def app_handler(event, context):
    '''App entry point'''
    try:
        trigger_name = event.get('trigger_name')
        handler = TRIGGER_HANDLERS.get(trigger_name, _default_trigger_handler)
        return handler(event=event, context=context)
    except (RequestValidationError, GitHubUsernameError) as ex:
        return ex.to_error_response()
