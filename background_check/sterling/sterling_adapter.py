import json
from typing import Optional

import glog as log
import sterling_utils
from sterling_data_classes import SterlingCandidate, SterlingCallback
from sterling_constants import SterlingConstants

LIST_PACKAGES_URL_FORMAT = '{base_url}/packages'
GET_CANDIDATE_BY_CLIENT_REFERENCE_ID_URL_FORMAT = '{base_url}/candidates?clientReferenceId={client_reference_id}'
CREATE_CANDIDATE_URL_FORMAT = '{base_url}/candidates'
GET_SCREENINGS_URL = '{base_url}/screenings'
CALLBACK_URL_FORMAT = '{base_url}/{group_id}/sterling'


class SterlingAdapter:
    """ Adapter class for Sterling API. """

    def __init__(self, app_settings):
        client_id = app_settings.get('client_id')
        client_secret = app_settings.get('client_secret')
        if not client_id or not client_secret:
            raise ValueError('Client ID and Client Secret are required for Sterling API')

        self.app_settings = app_settings
        self.auth_key = sterling_utils.generate_auth_credentials(
            client_id=app_settings.get('client_id'),
            client_secret=app_settings.get('client_secret')
        )
        self.auth_token = sterling_utils.generate_auth_token(self.auth_key)
        self.headers = {
            'Authorization': f'Bearer {self.auth_token}'
        }

    def get_packages(self, req_data):
        """ Get list of packages from Sterling API. """
        url = LIST_PACKAGES_URL_FORMAT.format(base_url=SterlingConstants.BASE_URL)
        params = {
            'accountId': req_data['account_id']
        } if req_data.get('account_id') else {}

        resp = sterling_utils.get_resp('GET',
                                       url=url,
                                       headers=self.headers,
                                       timeout=SterlingConstants.TIMEOUT,
                                       params=params)
        if resp.status_code != 200:
            raise ValueError(resp.content or 'Failure to fetch packages')

        print(f'Packages request: {url}, {params}, response: {resp}')
        log.info(f'Packages request: {url}, {params}, response: {resp}')
        packages_data = json.loads(resp.content.decode('utf-8'))
        return packages_data

    def get_candidate_by_client_reference_id(self, client_reference_id):
        """ Get candidate details by client reference ID from Sterling API. """
        if not client_reference_id:
            raise ValueError('Client Reference ID is required for fetching candidate details')

        url = GET_CANDIDATE_BY_CLIENT_REFERENCE_ID_URL_FORMAT.format(
            base_url=SterlingConstants.BASE_URL,
            client_reference_id=client_reference_id
        )
        resp = sterling_utils.get_resp('GET',
                                       url=url,
                                       headers=self.headers,
                                       timeout=SterlingConstants.TIMEOUT)
        if resp.status_code != 200:
            raise ValueError(resp.content or 'Failure to fetch candidate details')
        print(f'Candidate request: {url}, response: {resp}')
        log.info(f'Candidate request: {url}, response: {resp}')
        candidate_data = json.loads(resp.content.decode('utf-8'))
        return [SterlingCandidate(**candidate) for candidate in candidate_data]

    @staticmethod
    def _generate_client_reference_id(group_id, profile_id):
        return sterling_utils.base64_str(f'{group_id}_{profile_id}')


    @staticmethod
    def _get_callback_basic_auth_token(group_id, profile_id):
        return sterling_utils.base64_str(f'{group_id}_{profile_id}')

    def create_candidate(self, candidate: SterlingCandidate) -> SterlingCandidate:
        """
        Creates a candidate in the Sterling system.

        Args:
            candidate (SterlingCandidate): The candidate to create in the Sterling system.

        Returns:
            SterlingCandidate: The candidate object representing the created candidate.
        """
        if not candidate.givenName or not candidate.familyName or not candidate.email or not candidate.clientReferenceId:
            raise Exception("givenName, familyName, email and clientReferenceId are required to create a candidate in Sterling.")

        url = CREATE_CANDIDATE_URL_FORMAT.format(base_url=SterlingConstants.BASE_URL)
        resp = sterling_utils.get_resp('POST',
                                       url=url,
                                       headers=self.headers,
                                       json=candidate.__dict__)
        if resp.status_code != 201:
            raise Exception(f"Failed to create candidate: {resp.content}")

        return SterlingCandidate(**json.loads(resp.content.decode('utf-8')))

    def get_or_create_candidate(self, candidate: SterlingCandidate, group_id, profile_id) -> SterlingCandidate:
        """
        Retrieves an existing candidate by client reference ID if available,
        otherwise creates a new candidate using the provided candidate object.

        Args:
            candidate (SterlingCandidate): The candidate object to create if no existing candidate is found.
            group_id (str): The group ID of the candidate.
            profile_id (str): The profile ID of the candidate.
        Returns:
            SterlingCandidate: The retrieved or created candidate object.
        """
        client_reference_id = self._generate_client_reference_id(group_id, profile_id)
        try:
            return self.get_candidate_by_client_reference_id(client_reference_id)[0]
        except Exception as e:
            log.info(f"Failed to get candidate by client reference ID: {e}")
            candidate.clientReferenceId = client_reference_id
            return self.create_candidate(candidate)

    def _start_verification(self, candidate_id: str,
                            profile_id: str,
                            group_id: str,
                            package_id: str = None,
                            invite_method: str = SterlingConstants.SCREENING_METHOD_LINK,
                            account_id: Optional[str] = None,
                            callback_uri: Optional[str] = None,
                            callback_auth_token: Optional[str] = None):

        req_data = {
            "candidateId": candidate_id,
            "invite": {
                "method": invite_method
            }
        }
        if package_id:
            req_data["packageId"] = package_id
        if account_id:
            req_data["accountId"] = account_id
        if callback_uri:
            req_data['callback'] = SterlingCallback(
                uri=callback_uri,
                credentials={'basic-auth': callback_auth_token or self._get_callback_basic_auth_token(group_id, profile_id)}
            ).to_dict()
        resp = sterling_utils.get_resp('POST',
                                       url=GET_SCREENINGS_URL.format(base_url=SterlingConstants.BASE_URL),
                                       headers=self.headers,
                                       json=req_data)
        if resp.status_code != 201:
            raise Exception(f"Failed to start verification: {resp.content}")
        print(f'Screening request: {req_data}, response: {resp}')
        return json.loads(resp.content.decode('utf-8'))

    def initiate_background_verification(self, req_data):
        """ Initiates background verification for a candidate in Sterling API. """
        sterling_candidate = SterlingCandidate(
            email=req_data['email'],
            givenName=req_data['first_name'],
            familyName=req_data['last_name'],
            clientReferenceId=self._generate_client_reference_id(req_data['group_id'], req_data['profile_id'])
        )
        profile_id = req_data['profile_id']
        group_id = req_data['group_id']
        sterling_candidate = self.get_or_create_candidate(sterling_candidate, group_id=group_id, profile_id=profile_id)
        print(f'Candidate created: {sterling_candidate}')
        log.info(f'Candidate created: {sterling_candidate}')
        callback_base_url = req_data.get('callback_base_url', {}) or None
        callback_url = None
        if callback_base_url:
            callback_url = CALLBACK_URL_FORMAT.format(base_url=callback_base_url, group_id=group_id)
        screening = self._start_verification(candidate_id=sterling_candidate.id,
                                             profile_id=profile_id,
                                             group_id=group_id,
                                             package_id=req_data.get('package_id'),
                                             account_id=req_data.get('account_id'),
                                             callback_uri=callback_url)
        print(f'Screening initiated: {screening}')
        log.info(f'Screening initiated: {screening}')
        return {
            'screening': screening,
            'candidate': sterling_candidate.to_dict()
        }


