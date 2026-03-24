import json
import jinja2
import requests

from googleapiclient.discovery import build
from google.oauth2 import service_account

class GoogleDriveConnector():
    def __init__(self, google_drive_account_info, admin_email):
        SCOPES = ['https://www.googleapis.com/auth/drive']

        credentials = service_account.Credentials.from_service_account_info(google_drive_account_info, scopes=SCOPES)
        credentials = credentials.with_subject(admin_email)
        drive_v3_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)

        self.drive_v3_service = drive_v3_service
        self.admin_email = admin_email

    def _get_existing_docs(self, doc_title):
        existing_docs = self.drive_v3_service.files().list(
            spaces='drive',
            fields='files(id, name)',
            q='name = "{}"'.format(doc_title),
        ).execute().get('files', [])

        return existing_docs

    def _copy_doc_to_folders(self, doc_to_copy_id, new_doc_title, folder_ids):
        print('Creating new doc: {}'.format(new_doc_title))
        new_doc = self.drive_v3_service.files().copy(
            fileId=doc_to_copy_id,
            body={
                'name': new_doc_title,
                'parents': folder_ids,
                'copyRequiresWriterPermission': True,
            },
        ).execute()

        return new_doc

    def _share_doc(self, file_id, email_address, email_message):
        print('Adding {} to new doc: {}'.format(email_address, file_id))
        self.drive_v3_service.permissions().create(
            fileId=file_id,
            sendNotificationEmail=True,
            emailMessage=email_message,
            body={
                'type': 'user',
                'role': 'writer',
                'emailAddress': email_address,
            },
        ).execute()

    def get_performance_review_doc_url(self, doc_title_template, folder_ids, template_doc_id, reportee_profile, manager_profile):
        performance_review_doc_title = doc_title_template.format(
            reportee_fullname=reportee_profile.get('fullname'),
            manager_fullname=manager_profile.get('fullname'),
        )

        existing_docs = self._get_existing_docs(performance_review_doc_title)
        if existing_docs:
            print('Found and using existing doc: {}'.format(performance_review_doc_title))
            file_id = existing_docs[0].get('id')
        else:
            new_doc = self._copy_doc_to_folders(template_doc_id, performance_review_doc_title, folder_ids)
            file_id = new_doc.get('id')

            self._share_doc(
                file_id=file_id,
                email_address=reportee_profile.get('employee_email'),
                email_message='Hey {}, please add your self-assessment here. Thanks!'.format(reportee_profile.get('fullname')),
            )

            self._share_doc(
                file_id=file_id,
                email_address=manager_profile.get('employee_email'),
                email_message='Hey {}, please add your manager evaluation for {} here. Thanks!'.format(manager_profile.get('fullname'), reportee_profile.get('fullname')),
            )

        doc_url = 'https://docs.google.com/document/d/{file_id}/'.format(file_id=file_id)
        return doc_url

def app_handler(event, context):
    if event.get('trigger_name') == 'career_hub_profile_view':
        req_data = event.get('request_data', {})
        app_settings = event.get('app_settings')

        profile_email = req_data.get('employee_email', '')
        current_user_email = req_data.get('current_user_email', '')
        manager_profile = req_data.get('manager_profile', {})

        if not manager_profile:
            data = {
                'error': 'Manager is unknown.',
                'title': 'Annual Review (FY \'21)',
                'logo_url': 'https://static.vscdn.net/images/logos/eightfold_logo_no_text.svg',
            }

            html = jinja2.Template(open('template.html').read()).render(data=data)

            return {
                'statusCode': 200,
                'body': json.dumps({'html': html, 'cache_ttl_seconds': 600}),
            }

        secrets = app_settings.get('secrets', {})
        GOOGLE_DRIVE_ACCOUNT_INFO = secrets.get('google_drive_account_info')
        FOLDER_IDS = app_settings.get('folder_ids')
        ADMIN_EMAIL = app_settings.get('admin_email')
        TEMPLATE_DOC_ID = app_settings.get('template_doc_id')
        DOC_TITLE_TEMPLATE = app_settings.get('doc_title_template')

        google_drive = GoogleDriveConnector(google_drive_account_info=GOOGLE_DRIVE_ACCOUNT_INFO, admin_email=ADMIN_EMAIL)
        performance_review_doc_url = google_drive.get_performance_review_doc_url(
            doc_title_template=DOC_TITLE_TEMPLATE,
            folder_ids=FOLDER_IDS,
            template_doc_id=TEMPLATE_DOC_ID,
            reportee_profile=req_data,
            manager_profile=manager_profile,
        )

        is_viewing_own_profile = profile_email == current_user_email
        is_viewing_reportee_profile = manager_profile.get('employee_email') == current_user_email
        is_viewing_peer_profile = not is_viewing_own_profile and not is_viewing_reportee_profile

        action_buttons = []
        title = 'Annual Review (FY \'21)'
        footer = None
        if is_viewing_own_profile:
            title = 'Self Assessment (FY \'21)'
            footer = 'Please enter your self assessment. {} will review it and add feedback.'.format(manager_profile.get('firstname'))
            action_buttons.append({
                'label': 'Add/Edit Feedback',
                'onClick': 'window.open("{}")'.format(performance_review_doc_url),
            })
        if is_viewing_reportee_profile:
            title = 'Manager Feedback (FY \'21)'
            reportee_firstname = req_data.get('firstname', '')
            reportee_firstname_with_apos = reportee_firstname + ('\'' if reportee_firstname[-1] == 's' else '\'s')
            footer = """
                        Please review {} self assessment and enter your feedback.
                        Feedback is visible only to you, {}, and the People team.
                     """.format(reportee_firstname_with_apos, reportee_firstname)
            action_buttons.append({
                'label': 'Add/Edit Feedback',
                'onClick': 'window.open("{}")'.format(performance_review_doc_url),
            })
        if is_viewing_peer_profile:
            footer = 'Note: Individual inputs will be kept confidential, but aggregated where necessary.'
            action_buttons.append({
                'label': 'Provide Peer Feedback',
                'onClick': 'window.open("{}")'.format('https://docs.google.com/forms/d/e/1FAIpQLScYrkG8B9j8G3vQ1xQdgJkpS-6mH6rqWDwXcG-0Q8kDeYMXnw/viewform'),
            })

        data = {
            'title': title,
            'footer': footer,
            'action_buttons': action_buttons,
            'logo_url': 'https://static.vscdn.net/images/logos/eightfold_logo_no_text.svg',
        }

        html = jinja2.Template(open('template.html').read()).render(data=data)

        return {
            'statusCode': 200,
            'body': json.dumps({'html': html, 'cache_ttl_seconds': 1800}),
        }
