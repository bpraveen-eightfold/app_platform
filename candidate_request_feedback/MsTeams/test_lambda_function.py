from __future__ import absolute_import

import json
import mock
from lambda_function import app_handler


@mock.patch('ms_teams_utils.send_message_from_bot')
def test_app_handler(mocked_send_messsage_from_bot):
    request_data = {
        'viewFeedbackUrl': 'https://app.eightfold.ai/profile/EKJ2R45K?activeTab=interviewnote_hm_feedback&pid=1405913&feedbackId=RnpXoQLn',
        'requester': {
            'fullName': 'Karan Bajaj',
            'email': 'demo@eightfolddemo-kb2.com',
            'domain': 'app.eightfold.ai',
            'msToken': {
                'bot': {'id': '28:dd25dde6-4468-4d6c-8114-a1d8f56ee6e0', 'name': 'Test EF BOT'},
                'conversation': {'conversationType': 'personal', 'id': 'a:1cmbKBLdkNFrFSNpDzLvvDEQeR8Jcb239kKs4rPzJQL7hqyMTIV_tXMQVz-pcKWa4x8qUjwuAjoDw1liWP86RsKP-QvFkNRRTWLZ3CTNi4mvsdB8fCFUJQoF6trskut0t', 'tenantId': '5a83a52a-9b10-4117-8efd-69077eae0247'},
                'activityId': '1627535959509',
                'user': {'aadObjectId': '26f355bf-4233-4a57-b5f2-55fe42d9931f', 'id': '29:1IK1yMaA_xr4gtfDN6tmc-zb4ZAYDfW8VMcTmF39xdM1pHIrKX4xyPbLFy2ssjnvAaQvjko1wTKGug03vlBWwkA', 'name': 'Thrivikram Karur'},
                'serviceUrl': 'https://smba.trafficmanager.net/in/',
                'bot_token': {'token_type': 'Bearer', 'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Im5PbzNaRHJPRFhFSzFqS1doWHNsSFJfS1hFZyIsImtpZCI6Im5PbzNaRHJPRFhFSzFqS1doWHNsSFJfS1hFZyJ9.eyJhdWQiOiJodHRwczovL2FwaS5ib3RmcmFtZXdvcmsuY29tIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvZDZkNDk0MjAtZjM5Yi00ZGY3LWExZGMtZDU5YTkzNTg3MWRiLyIsImlhdCI6MTYyNzUzNTY2MSwibmJmIjoxNjI3NTM1NjYxLCJleHAiOjE2Mjc2MjIzNjEsImFpbyI6IkUyWmdZUGhwOG5pWE5mdjlHMkszVzJMVXkxNW5BQUE9IiwiYXBwaWQiOiJkYzI1ZGRlNi00NDY4LTRkNmMtODExNC1hMWQ4ZjU2ZWE2ZTAiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9kNmQ0OTQyMC1mMzliLTRkZjctYTFkYy1kNTlhOTM1ODcxZGIvIiwicmgiOiIwLkFXNEFJSlRVMXB2ejkwMmgzTldhazFoeDItYmRKZHhvUkd4TmdSU2gyUFZ1cHVCdUFBQS4iLCJ0aWQiOiJkNmQ0OTQyMC1mMzliLTRkZjctYTFkYy1kNTlhOTM1ODcxZGIiLCJ1dGkiOiJ4WEo5M2d2UzJFU1RyZG5ZdC1JRkFBIiwidmVyIjoiMS4wIn0.inre5Vh4KjICht7kF0dLSFkvP9KMbzCNFZyfgeGsNu6z1UsgBBAzjBKDWpLZNxfwQWMqzonabdzh7h87veXFbWjEbClUIHmmvriSro5Lde-tJE-wmhyygYupscfgTkngNH5saQN9rhg7s5n1xBsXfkJ5w2Nh00tuvRGws7eo4GAXwE60wjVdeCmK4XXe9XP_2X5K-Sj_rSmzb8ay1q36fRHpiXXIebvmEbOf-hmlA8eE0hgsVjZkDvfM5bi4_Nv_UpSznaHZwKZNb1Tir9vSF7iqiDlgO7V7Zctt4CmlSuGbPcJ8fA4790gWfJOePqtK-xw50f2vGzdfzeaE2uQIrA', 'ext_expires_in': 86399, 'expires_in': 86399},
                'channelData': {'tenant': {'id': '5a83a52a-9b10-4117-8efd-69077eae0247'}}
            }
        },
        'feedbackUrl': 'https://app.eightfold.ai/v2/interview_feedback/RnpXoQLn',
        'position': {
            'positionId': 1405913,
            'name': 'Software Engineer'
        },
        'candidateProfileRequester': {
            'workExperienceYears': 18.0,
            'location': 'Bengaluru Area, India',
            'title': 'Built DailyHunt with passion',
            'skills': ['Java, Hadoop, MongoDB, Redis, AWS', 'Python', 'Java', 'Distributed Systems', 'JUnit', 'C++', 'Agile Methodologies', 'Hadoop', 'Shell Scripting', 'Mobile Applications', 'Design Patterns', 'OOP', 'Testing', 'Algorithms', 'Android', 'Multithreading'],
            'profileId': 630093,
            'encId': 'EKJ2R45K',
            'fullName': 'Shreyas Desai',
            'experience': [
                {'durationMonths': 40, 'work': 'Amazon Web Services', 'title': 'Software Development Manager'},
                {'durationMonths': 98, 'work': 'Vauntz', 'title': 'Co-founder'},
                {'durationMonths': 14, 'work': 'Newshunt', 'title': 'Director of Engineering'}
            ]
        },
        'reviewer': {
            'fullName': 'Hiring Manager',
            'email': 'hiringmanager@eightfolddemo-kb2.com',
            'domain': 'app.eightfold.ai',
            'msToken': {
                'bot': {'id': '28:dd25dde6-4468-4d6c-8114-a1d8f56ee6e0', 'name': 'Test EF BOT'},
                'conversation': {'conversationType': 'personal', 'id': 'a:1XhXPnKUOhnCX_aZp07SisrX5WosvDah2xzPFGMj6fT7gnXLkyE2ed2ngEt_ZoKzZrG9DocajypVumC5oljwW6fC-EpTrmATj6fN8OKoKdbwDeJmImuMurM8lLzhqrz1a', 'tenantId': '5a83a52a-9b10-4117-8efd-69077eae0247'},
                'activityId': '1627535229644',
                'user': {
                    'aadObjectId': '26475236-6748-44b4-a0a7-5cbc5fc8a150',
                    'id': '29:1yc9fGkdDAdoGfkXtqNSqgCDgDTwE_9F1oHBY9ojZ-bl3OuRyw49umAVxyWviTBXwM-qeM5yiCFSUbKSUbIn3AA',
                    'name': 'Patti Fernandez'
                },
                'serviceUrl': 'https://smba.trafficmanager.net/in/',
                'bot_token': {
                    'token_type': 'Bearer', 'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Im5PbzNaRHJPRFhFSzFqS1doWHNsSFJfS1hFZyIsImtpZCI6Im5PbzNaRHJPRFhFSzFqS1doWHNsSFJfS1hFZyJ9.eyJhdWQiOiJodHRwczovL2FwaS5ib3RmcmFtZXdvcmsuY29tIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvZDZkNDk0MjAtZjM5Yi00ZGY3LWExZGMtZDU5YTkzNTg3MWRiLyIsImlhdCI6MTYyNzUzNDkzMSwibmJmIjoxNjI3NTM0OTMxLCJleHAiOjE2Mjc2MjE2MzEsImFpbyI6IkUyWmdZTWpZV0NuUFVIcU1SNnJQYW9LUWs0Z3pBQT09IiwiYXBwaWQiOiJkYzI1ZGRlNi00NDY4LTRkNmMtODExNC1hMWQ4ZjU2ZWE2ZTAiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9kNmQ0OTQyMC1mMzliLTRkZjctYTFkYy1kNTlhOTM1ODcxZGIvIiwicmgiOiIwLkFXNEFJSlRVMXB2ejkwMmgzTldhazFoeDItYmRKZHhvUkd4TmdSU2gyUFZ1cHVCdUFBQS4iLCJ0aWQiOiJkNmQ0OTQyMC1mMzliLTRkZjctYTFkYy1kNTlhOTM1ODcxZGIiLCJ1dGkiOiI4aU5vc3o0MGZrV2Yxb3REc1I4TUFBIiwidmVyIjoiMS4wIn0.Qz37fYMhbJMEzCTSO9B3cEkyNCAG2SdjaTGqmuSDmROwmkMJ3EFwvxJ4E6qoZ-C9syyMtDNZeaJBLbYgHHk6dWHtOJEXMJNLl2BeKLPL3wit4q6NSx6tfvydXKX8YDu-oFytpc-FOW-9TOjAM4IxbY_BombQITv_walcw0NNsTL-YpsghPhKQBc4QO7wfnh1ko5WhA2Mq2scPxetVsiASy6Gxph-T_bL3XXG-Ni2VUi1OTm-6nresHyYCW4WNYiX2rZvilDTR47GfDf6ybId0YmDNqhlZ6ImYlu5RfjJVxDYoYDgWf2rX-D4JBwLco_m2WoLRMkFIwVEsSF7NzT9Fg', 'ext_expires_in': 86398, 'expires_in': 86398
                },
                'channelData': {'tenant': {'id': '5a83a52a-9b10-4117-8efd-69077eae0247'}}
            }
        },
        'candidateProfileReviewer': {
            'workExperienceYears': 18.0,
            'location': 'Bengaluru Area, India',
            'title': 'Built DailyHunt with passion',
            'skills': ['Java, Hadoop, MongoDB, Redis, AWS', 'Python', 'Java', 'Distributed Systems', 'JUnit', 'C++', 'Agile Methodologies', 'Hadoop', 'Shell Scripting', 'Mobile Applications', 'Design Patterns', 'OOP', 'Testing', 'Algorithms', 'Android', 'Multithreading'],
            'profileId': 630093,
            'encId': 'EKJ2R45K',
            'fullName': 'S. D.',
            'experience': [
                {'durationMonths': 40, 'work': 'Amazon Web Services', 'title': 'Software Development Manager'},
                {'durationMonths': 98, 'work': 'Vauntz', 'title': 'Co-founder'},
                {'durationMonths': 14, 'work': 'Newshunt', 'title': 'Director of Engineering'}
            ]
        }
    }
    app_handler({
        'request_data': request_data,
        'trigger_name': 'feedback_requested',
        'app_settings': {}
    }, {})
    adaptive_card_expected = json.load(open('test_ms_teams_requested_adaptive_card_output.json'))
    assert mocked_send_messsage_from_bot.call_args.kwargs.get('adaptive_card') == adaptive_card_expected
    assert mocked_send_messsage_from_bot.call_args.args == (
        {'bot': {'id': '28:dd25dde6-4468-4d6c-8114-a1d8f56ee6e0', 'name': 'Test EF BOT'}, 'bot_token': {'token_type': 'Bearer', 'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Im5PbzNaRHJPRFhFSzFqS1doWHNsSFJfS1hFZyIsImtpZCI6Im5PbzNaRHJPRFhFSzFqS1doWHNsSFJfS1hFZyJ9.eyJhdWQiOiJodHRwczovL2FwaS5ib3RmcmFtZXdvcmsuY29tIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvZDZkNDk0MjAtZjM5Yi00ZGY3LWExZGMtZDU5YTkzNTg3MWRiLyIsImlhdCI6MTYyNzUzNDkzMSwibmJmIjoxNjI3NTM0OTMxLCJleHAiOjE2Mjc2MjE2MzEsImFpbyI6IkUyWmdZTWpZV0NuUFVIcU1SNnJQYW9LUWs0Z3pBQT09IiwiYXBwaWQiOiJkYzI1ZGRlNi00NDY4LTRkNmMtODExNC1hMWQ4ZjU2ZWE2ZTAiLCJhcHBpZGFjciI6IjEiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9kNmQ0OTQyMC1mMzliLTRkZjctYTFkYy1kNTlhOTM1ODcxZGIvIiwicmgiOiIwLkFXNEFJSlRVMXB2ejkwMmgzTldhazFoeDItYmRKZHhvUkd4TmdSU2gyUFZ1cHVCdUFBQS4iLCJ0aWQiOiJkNmQ0OTQyMC1mMzliLTRkZjctYTFkYy1kNTlhOTM1ODcxZGIiLCJ1dGkiOiI4aU5vc3o0MGZrV2Yxb3REc1I4TUFBIiwidmVyIjoiMS4wIn0.Qz37fYMhbJMEzCTSO9B3cEkyNCAG2SdjaTGqmuSDmROwmkMJ3EFwvxJ4E6qoZ-C9syyMtDNZeaJBLbYgHHk6dWHtOJEXMJNLl2BeKLPL3wit4q6NSx6tfvydXKX8YDu-oFytpc-FOW-9TOjAM4IxbY_BombQITv_walcw0NNsTL-YpsghPhKQBc4QO7wfnh1ko5WhA2Mq2scPxetVsiASy6Gxph-T_bL3XXG-Ni2VUi1OTm-6nresHyYCW4WNYiX2rZvilDTR47GfDf6ybId0YmDNqhlZ6ImYlu5RfjJVxDYoYDgWf2rX-D4JBwLco_m2WoLRMkFIwVEsSF7NzT9Fg', 'ext_expires_in': 86398, 'expires_in': 86398}},
        {'serviceUrl': 'https://smba.trafficmanager.net/in/', 'conversation': {'conversationType': 'personal', 'id': 'a:1XhXPnKUOhnCX_aZp07SisrX5WosvDah2xzPFGMj6fT7gnXLkyE2ed2ngEt_ZoKzZrG9DocajypVumC5oljwW6fC-EpTrmATj6fN8OKoKdbwDeJmImuMurM8lLzhqrz1a', 'tenantId': '5a83a52a-9b10-4117-8efd-69077eae0247'}, 'activityId': '1627535229644', 'recipient': {'aadObjectId': '26475236-6748-44b4-a0a7-5cbc5fc8a150', 'id': '29:1yc9fGkdDAdoGfkXtqNSqgCDgDTwE_9F1oHBY9ojZ-bl3OuRyw49umAVxyWviTBXwM-qeM5yiCFSUbKSUbIn3AA', 'name': 'Patti Fernandez'}}
    )
