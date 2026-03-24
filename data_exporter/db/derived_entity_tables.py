"""
Derived entity tables: data stored inside parent DB tables.
Registry is in table_registry.py. Export logic is in derived_entity_exporter.py.
"""

from abc import ABC
from abc import abstractmethod


class DerivedTable(ABC):
    """
    Defines a derived table via methods (like DBEntityTable).
    Parent must be from existing tables (profiles, positions, etc).
    """

    @abstractmethod
    def tablename(self):
        """Output identifier (e.g. 'jtn-form-submissions')."""
        raise NotImplementedError('Must have a tablename')

    @abstractmethod
    def parent_table(self):
        """Parent table from registry (e.g. 'profiles')."""
        raise NotImplementedError('Must have a parent_table')

    def include_fields(self):
        """
        Extra field names to request when batch-fetching parent entities.
        Derived data often lives in nested JSON fields on the parent (e.g. profiles
        have jtnSubmissions). These must be included in the API's include param
        so extract() receives them via parent_item. Override to return a list of
        field names; default is empty.
        """
        return []

    def id_col(self):
        """Field name to key the record in json format file."""
        raise NotImplementedError('Must have an id_col')

    @abstractmethod
    def extract(self, parent_item, start_time, end_time):
        """
        Extract derived records from one parent item.
        :return: List of dicts (one per derived record)
        """
        raise NotImplementedError('Must have an extract method')


class JtnFormSubmissionsTable(DerivedTable):
    """JTN submissions derived from profiles."""

    def tablename(self):
        return 'jtn-form-submissions'

    def parent_table(self):
        return 'profiles'

    def include_fields(self):
        return ['jtnSubmissions']

    def id_col(self):
        return 'jtnSubmissionId'

    def extract(self, parent_item, start_time, end_time):
        records = []
        profile_id = parent_item.get('profileId')
        if not profile_id:
            return records

        jtn = parent_item.get('jtnSubmissions')
        if not jtn or not isinstance(jtn, dict):
            return records

        for form_id, submissions in jtn.items():
            if not isinstance(submissions, list):
                continue
            for sub in submissions:
                if not isinstance(sub, dict):
                    continue
                ts = sub.get('timestamp')
                if ts is None or not (start_time <= ts < end_time):
                    continue
                answers = self._extract_answers(sub.get('responses'))
                profile_id_str = str(profile_id)
                records.append({
                    'answersByQuestionId': answers,
                    'jtnFormId': form_id,
                    'profileId': profile_id_str,
                    'submittedAt': ts,
                    'jtnSubmissionId': f'{profile_id_str}:{form_id}:{ts}',
                })
        return records

    @staticmethod
    def _extract_answers(responses):
        result = {}
        if not responses or not isinstance(responses, list):
            return result
        for response in responses:
            qid = response.get('questionId')
            if not qid:
                continue
            result[qid] = response.get('label', '') if response.get('type') == 'instruction' else response.get('values')
        return result
