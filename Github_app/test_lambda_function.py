import argparse

from lambda_function import app_handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', default='gauravg@eightfold.ai', help='email of profile user')
    parser.add_argument('--app_user', default='satyajeet-eightfold', help='user name of app authentication user')
    parser.add_argument('--app_gh_token', default='e56ba019c29f5b941729624c9a0496211aa1d9b8', help='Github API token for user')
    args = parser.parse_args()

    event = {
        'request_data':  {
            'email': args.email
        },
        'app_settings': {
            'username': args.app_user,
            'token': args.app_gh_token,
            'email_to_github_user': {
                'gauravg@eightfold.ai': 'gaurav-ef2',
                'skumar@eightfold.ai': 'satyajeet-eightfold',
                'anuragn@eightfold.ai': 'Anurag-Nilesh',
            },
            'user_name_format': '{email_user_name}-eightfold'
        },
        'trigger_name': 'career_hub_profile_view'
    }
    resp = app_handler(event=event, context=None)
    print(resp['body'])

##
# test commands
# python career_hub/profile/EightfoldGithubApp/test_lambda_function.py
##
if __name__ == "__main__":
    main()
