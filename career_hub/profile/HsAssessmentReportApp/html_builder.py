from dataclasses import dataclass, asdict
from datetime import datetime
import urllib.parse

EF_DOWNLOAD_HS_ATTACHMENT_ENDPOINT = '/api/career_hub/v1/download_hs_attachment'


@dataclass
class AssessmentData:
    """
    Class for assessment data used for building app widget HTML
    """
    title: str
    date: str
    attachment_id: str
    content_type: str
    filename: str

    def __init__(self, assessment_data):
        self.title = self._get_title(assessment_data)
        self.date = self._get_date(assessment_data)
        self.attachment_id = assessment_data.get('id', '')
        self.content_type = assessment_data.get('contentType', '')
        self.filename = assessment_data.get('name', '')

    def _get_attachment_fallback_title(self, assessment_data):
        report_type = assessment_data.get('reportType')
        name = assessment_data.get('name')
        if report_type and name:
            return f'{report_type} - {name}'
        return name

    def _get_title(self, assessment_data):
        return assessment_data.get('reportName') or self._get_attachment_fallback_title(assessment_data)

    def _get_date(self, assessment_data):
        raw_date = assessment_data.get('reportDate') or assessment_data.get('addedTs')
        if not raw_date:
            return ''
        raw_date = raw_date.split('T')[0]   # only take the date and strip time string
        return datetime.strptime(raw_date, '%Y-%m-%d').strftime('%b %-d, %Y')


class TableHeader:
    def __init__(self, title, attrs=None):
        self.value = title
        self.attrs = attrs or {}


class HtmlBuilder:
    def __init__(self, resp_data, username):
        self.resp_data = resp_data
        self.username = username

    def get_table_row_items(self):
        return [asdict(AssessmentData(data)) for data in self.resp_data if data]

    def get_table_header_item_html(self, header: TableHeader):
        attributes = [f'{attr}="{val}"' for attr, val in header.attrs.items()]
        attributes = ' '.join(attributes)
        return f'''
        <th {attributes}>
            {header.value}
        </th>
        '''

    def get_table_header_html(self):
        html = '<thead>'
        table_header_items = [
            TableHeader(title='Assessment', attrs={'class': 'assessment-col'}),
            TableHeader(title='Date'),
            TableHeader(title='', attrs={'class': 'action-col'}),
        ]
        for header in table_header_items:
            html += self.get_table_header_item_html(header)
        html += '</thead>'
        return html

    def get_download_hs_attachment_url(self, row_item):
        params = {key: value for key, value in row_item.items() if value}
        if self.username:
            params['profile_email'] = self.username
        return f'{EF_DOWNLOAD_HS_ATTACHMENT_ENDPOINT}?{urllib.parse.urlencode(params)}'

    def get_download_anchor_html(self, row_item):
        return f'''
        <a href={self.get_download_hs_attachment_url(row_item)} target="_blank">
            <i class="fal fa-download field-icon"></i>
        </a>
        '''

    def get_table_row_item_html(self, row_item):
        return f'''
        <tr>
            <td class="assessment-col">
                {row_item.get("title") or ""}
            </td>
            <td>
                {row_item.get("date") or ""}
            </td>
            <td class="action-col">
                {self.get_download_anchor_html(row_item)}
            </td>
        </tr>
        '''

    def get_table_row_html(self):
        html = ''
        table_row_items = self.get_table_row_items()
        for item in table_row_items:
            html += self.get_table_row_item_html(item)
        return html

    @staticmethod
    def construct_style_tag():
        return '''
        <style>
            .hs-tbl {
                text-align: left;
                width: 100%;
            }

            .hs-tbl td {
                font-weight: normal;
            }

            .hs-tbl tr {
                display: block;
                border-bottom: 1px solid lightgray;
                padding: 10px 0;
            }

            .hs-tbl .assessment-col {
                width: 250px;
            }

            .hs-tbl .action-col {
                width: 25px;
            }

            .hs-tbl .action-col a {
                display: block;
                margin-left: 10px;
            }
        </style>
        '''

    def construct_widget_html(self):
        return f'''
        <div class="title" style="padding-bottom:16px;">
            <div class="title-container">
                <h3>Assessment Reports</h3>
            </div>
        </div>
        <table class="hs-tbl">
            {self.get_table_header_html()}
            <tbody>
                {self.get_table_row_html()}
            </tbody>
        </table>
        {HtmlBuilder.construct_style_tag()}
        '''
    @staticmethod
    def construct_empty_widget_html():
        return f'''
        <div class="title" style="padding-bottom:16px;">
            <div class="title-container">
                <h3>Assessment Reports</h3>
            </div>
        </div>
        <span> Could not find assessment reports for this user. </span>
        {HtmlBuilder.construct_style_tag()}
        '''
