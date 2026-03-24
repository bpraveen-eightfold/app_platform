"""
Adapter for First Advantage API integration.
"""

import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from fadv_constants import FADVConstants
from fadv_data_classes import FADVCandidate, FADVInviteRequest, FADVPackage
from fadv_utils import map_order_status_to_assessment_status, convert_date_to_timestamp


class FirstAdvantageAdapter:
    """Adapter for First Advantage API."""
    
    def __init__(self, app_settings: Dict[str, Any], app_sdk):
        """
        Initialize the First Advantage adapter.
        
        Args:
            app_settings: Application settings including API key and URLs
            app_sdk: Instance of EFAppSDK for making HTTP requests
            
        Raises:
            ValueError: If required settings are missing
        """
        self.app_settings = app_settings
        self.app_sdk = app_sdk
        self.api_key = app_settings.get('api_key', '')
        self.base_url = app_settings.get('first_advantage_base_url', '')
        self.account_id = app_settings.get('account_id', '')
        self.comments_enabled = app_settings.get('comment_flag', True)
        
        if not self.api_key:
            raise ValueError("API key is missing from app_settings")
        
        if not self.base_url:
            raise ValueError("First Advantage base URL is missing from app_settings")
        
        if not self.account_id:
            raise ValueError("Account ID is missing from app_settings")
        
        if not self.app_sdk:
            raise ValueError("app_sdk is required for API requests")
        
        # Set up authorization headers
        self.headers = {
            'Authorization': f'{self.api_key}'
        }
        
        self.app_sdk.log(f"FirstAdvantageAdapter initialized with base URL: {self.base_url}")
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all accounts associated with the parent account.
        
        Returns:
            List of account objects with account_id and name
            
        Raises:
            ValueError: If the API request fails
        """
        url = f"{self.base_url}{FADVConstants.ACCOUNTS_ENDPOINT}/{self.account_id}/details"
        self.app_sdk.log(f"Getting accounts from parent account ID: {self.account_id}")
        
        response = self.app_sdk.call_http_method(
            'GET',
            system_id='FirstAdvantage',
            url=url,
            headers=self.headers,
            timeout=FADVConstants.TIMEOUT_SECS
        )
        
        if response.status_code != 200:
            self.app_sdk.log(f"Failed to get accounts: {response.text}")
            raise ValueError(f"Could not get accounts: {response.text}")
        
        accounts = response.json()
        self.app_sdk.log(f"Found {len(accounts)} accounts under parent account")
        return accounts
    
    def get_packages(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get all packages for a specific account.
        
        Args:
            account_id: The account ID to get packages for
            
        Returns:
            List of package objects
            
        Raises:
            ValueError: If the API request fails
        """
        url = f"{self.base_url}{FADVConstants.ACCOUNTS_ENDPOINT}/{account_id}{FADVConstants.PACKAGES_ENDPOINT}"
        self.app_sdk.log(f"Getting packages for account ID: {account_id}")
        
        response = self.app_sdk.call_http_method(
            'GET',
            system_id='FirstAdvantage',
            url=url,
            headers=self.headers,
            timeout=FADVConstants.TIMEOUT_SECS
        )
        
        if response.status_code != 200:
            self.app_sdk.log(f"Failed to get packages for account {account_id}: {response.text}")
            raise ValueError(f"Could not get packages: {response.text}")
        
        packages_data = response.json()
        packages = packages_data.get('package_details', [])
        self.app_sdk.log(f"Found {len(packages)} packages for account {account_id}")
        return packages
    
    def list_all_packages(self) -> List[Dict[str, str]]:
        """
        List all packages from all accounts.
        
        Returns:
            List of formatted package objects with id, name, duration_minutes, and published fields
            
        Raises:
            Exception: If there's an error getting accounts or packages
        """
        try:
            # Get all accounts
            accounts = self.get_accounts()
            all_packages = []
            
            for account in accounts:
                account_id = account.get('account_id')
                account_name = account.get('name')
                
                if not account_id:
                    self.app_sdk.log(f"Skipping account with missing ID: {account}")
                    continue
                
                try:
                    # Get packages for this account
                    packages = self.get_packages(account_id)
                    
                    # Format packages with account name prefix
                    for package in packages:
                        package_obj = FADVPackage(
                            package_id=f"{account_id}-{package.get('package_id', '')}",
                            name=package.get('name', ''),
                            account_name=account_name
                        )
                        all_packages.append(package_obj.to_dict())
                    
                except Exception as e:
                    self.app_sdk.log(f"Error getting packages for account {account_id}: {str(e)}")
                    continue
            
            self.app_sdk.log(f"Total packages found: {len(all_packages)}")
            return all_packages
            
        except Exception as e:
            self.app_sdk.log(f"Error in list_all_packages: {str(e)}")
            raise
    
    def create_candidate(self, first_name: str, last_name: str, email: str) -> Dict[str, Any]:
        """
        Create a candidate in the First Advantage system.
        
        Args:
            first_name: Candidate's first name
            last_name: Candidate's last name
            email: Candidate's email address
            
        Returns:
            Dictionary containing candidate details including candidate_id
            
        Raises:
            ValueError: If the API request fails
        """
        url = f"{self.base_url}{FADVConstants.CANDIDATE_ENDPOINT}"
        self.app_sdk.log(f"Creating candidate: {first_name} {last_name} ({email})")
        
        # Create candidate object
        candidate = FADVCandidate(email=email)
        candidate.add_person(first_name, last_name)
        
        response = self.app_sdk.call_http_method(
            'POST',
            system_id='FirstAdvantage',
            url=url,
            headers=self.headers,
            json=candidate.to_dict(),
            timeout=FADVConstants.TIMEOUT_SECS
        )
        
        if response.status_code not in [200, 201]:
            self.app_sdk.log(f"Failed to create candidate: {response.text}")
            raise ValueError(f"Could not create candidate: {response.text}")
        
        candidate_data = response.json()
        self.app_sdk.log(f"Candidate created with ID: {candidate_data.get('candidate_id')}")
        return candidate_data
    
    def invite_candidate(self, 
                        email: str,
                        application_id: str,
                        candidate_id: str, 
                        package_id: str, 
                        profile_id: Optional[str] = None, 
                        pid: Optional[str] = None,
                        location_country: str = "",
                        location_state: str = "",
                        location_city: str = "",
                        action_user_email: str = "",
                        ats_job_id: str = "") -> Dict[str, Any]:
        """
        Invite a candidate to complete a background check.
        
        Args:
            email: The candidate's email address
            application_id: The application ID
            candidate_id: The candidate's ID in First Advantage
            package_id: The package ID for the background check
            profile_id: The candidate's profile ID in Eightfold
            pid: The PID in Eightfold
            location_country: The country of the position
            location_state: The state of the position
            location_city: The city of the position
            action_user_email: The email of the user initiating the action
            ats_job_id: The job ID in the ATS
            
        Returns:
            Dictionary containing the invite response including applicant_id
            
        Raises:
            ValueError: If the API request fails
        """
        url = f"{self.base_url}{FADVConstants.INVITE_ENDPOINT}"
        self.app_sdk.log(f"Inviting candidate {candidate_id} for package {package_id}")
        
        # Split composite package ID into account_id and package_id
        account_id, pkg_id = package_id.split("-", 1)
        
        # Create invite request
        invite_request = FADVInviteRequest(
            candidate_id=candidate_id,
            package_id=pkg_id
        )
        
        # Add quote backs
        invite_request.add_quote_back("email", email)
        
        if profile_id:
            invite_request.add_quote_back("profile_id", profile_id)
        
        if pid:
            invite_request.add_quote_back("pid", pid)
        
        if ats_job_id:
            invite_request.add_quote_back("ats_job_id", ats_job_id)
        
        if candidate_id:
            invite_request.add_quote_back("ats_candidate_id", candidate_id)
        
        if application_id:
            invite_request.add_quote_back("application_id", application_id)
        
        if account_id:
            invite_request.add_quote_back("order_account", account_id)
        
        if pkg_id:
            invite_request.add_quote_back("order_package", pkg_id)
        
        # Set order_as information
        invite_request.set_order_as(
            account_id=account_id,
            user_id="XCHANGE",
            email=action_user_email
        )
        
        # Add position location if all location fields are provided
        if location_country and location_state and location_city:
            invite_request.add_position_location(
                country=location_country,
                state=location_state,
                city=location_city
            )
        
        response = self.app_sdk.call_http_method(
            'POST',
            system_id='FirstAdvantage',
            url=url,
            headers=self.headers,
            json=invite_request.to_dict(),
            timeout=FADVConstants.TIMEOUT_SECS
        )
        
        if response.status_code not in [200, 201]:
            self.app_sdk.log(f"Failed to invite candidate: {response.text}")
            raise ValueError(f"Could not invite candidate: {response.text}")
        
        invite_data = response.json()
        self.app_sdk.log(f"Invite sent. Response: {invite_data}")
        return invite_data
    
    def _extract_quote_backs(self, quote_backs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract values from quote backs.
        
        Args:
            quote_backs: List of quote back objects
            
        Returns:
            Dictionary of extracted values
        """
        data = {
            'candidate_id': None,
            'applicant_id': None,
            'profile_id': None,
            'pid': None,
            'employer_code': None,
            'email': '',
            'order_account': None,
            'order_package': None,
        }
        
        for quote_back in quote_backs:
            if not isinstance(quote_back, dict):
                continue
                
            name = quote_back.get('name')
            value = quote_back.get('value')
            
            if name == 'candidate_id':
                data['candidate_id'] = value
            elif name == 'ApplicantId':
                data['applicant_id'] = value
            elif name == 'profile_id':
                data['profile_id'] = value
            elif name == 'pid':
                data['pid'] = value
            elif name == 'employer_code':
                data['employer_code'] = value
            elif name == 'email':
                data['email'] = value
            elif name == 'order_account':
                data['order_account'] = value
            elif name == 'order_package':
                data['order_package'] = value
                
        return data
    
    def _extract_additional_dates(self, additional_items: Union[List[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract dates from additional items.
        
        Args:
            additional_items: List or dictionary of additional items
            
        Returns:
            Dictionary of extracted dates
        """
        dates = {
            'ordered_date': None,
            'completion_date': None,
            'last_updated_date': None
        }
        
        if isinstance(additional_items, list):
            # Process as array
            for item in additional_items:
                if isinstance(item, dict):
                    item_type = item.get('type')
                    value = item.get('value')
                    
                    if item_type == 'ordered_date':
                        dates['ordered_date'] = value
                    elif item_type == 'completion_date':
                        dates['completion_date'] = value
                    elif item_type == 'last_updated_date':
                        dates['last_updated_date'] = value
        elif isinstance(additional_items, dict):
            # Process as single object
            item_type = additional_items.get('type')
            value = additional_items.get('value')
            
            if item_type == 'ordered_date':
                dates['ordered_date'] = value
            elif item_type == 'completion_date':
                dates['completion_date'] = value
            elif item_type == 'last_updated_date':
                dates['last_updated_date'] = value
                
        return dates
    
    def _process_order_details(self, order_data_list: List[Dict[str, Any]]) -> List[str]:
        """
        Process order details for comments.
        
        Args:
            order_data_list: List of order data objects
            
        Returns:
            List of formatted order detail strings
        """
        order_details = []
        
        for idx, order in enumerate(order_data_list):
            curr_order_id = order.get('order_id', f'Order{idx+1}')
            curr_order_status = order.get('order_status', 'Unknown')
            curr_result_status = order.get('result_status', 'Pending')
            curr_score = order.get('score', '')
            curr_display_result = curr_score if curr_score else curr_result_status
            
            # Extract screening details for this order
            curr_screenings = order.get('screenings', [])
            curr_screening_details = []
            
            for screening in curr_screenings:
                if isinstance(screening, dict):
                    description = screening.get('description')
                    screening_status = screening.get('order_status') or screening.get('order-status')
                    screening_result = screening.get('result_status', '')
                    
                    if description and screening_status:
                        if screening_result:
                            curr_screening_details.append(f"{description}: {screening_status} ({screening_result})")
                        else:
                            curr_screening_details.append(f"{description}: {screening_status}")
            
            # Format order details
            order_detail = f"Order {curr_order_id}: Status: {curr_order_status}, Result: {curr_display_result}"
            if curr_screening_details:
                order_detail += f"\nScreenings:"
                for screening_detail in curr_screening_details:
                    order_detail += f"\n- {screening_detail}"
            
            order_details.append(order_detail)
        
        # Join all order details with line breaks between them, not semicolons
        return order_details
    
    def process_webhook(self, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a webhook notification from First Advantage.
        
        Args:
            webhook_payload: The webhook payload from First Advantage
            
        Returns:
            Dictionary with actions to take based on the webhook
            
        Raises:
            ValueError: If the webhook payload is invalid
        """
        self.app_sdk.log(f"Processing webhook: {json.dumps(webhook_payload)}")
        
        # Handle different payload structures
        order_data_list = []
        
        if 'root' in webhook_payload and 'order' in webhook_payload['root'] and isinstance(webhook_payload['root']['order'], list):
            # Process all orders in the array
            orders = webhook_payload['root']['order']
            order_data_list = [order for order in orders if isinstance(order, dict)]
        else:
            # Handle direct order object
            order_data = webhook_payload.get('order', {})
            if order_data:
                order_data_list = [order_data]
        
        if not order_data_list:
            raise ValueError("Invalid webhook payload: missing order data")
        
        # Use the first order for main processing
        order_data = order_data_list[0]
        
        # Extract key information from primary order
        order_status = order_data.get('order_status')   
        # Extract metadata and quote_backs
        meta_data = order_data.get('meta_data', {})
        quote_backs = meta_data.get('quote_backs', [])
        
        # Filter out any non-dict or empty elements
        quote_backs = [qb for qb in quote_backs if isinstance(qb, dict)]
        # Extract identifiers from quote_backs
        quote_back_data = self._extract_quote_backs(quote_backs)
        
        # Extract dates from additional_items
        additional_items = order_data.get('additional_items')
        dates = self._extract_additional_dates(additional_items)
        
        # Convert dates to timestamps
        ordered_ts = convert_date_to_timestamp(dates['ordered_date'], self.app_sdk)
        completed_ts = convert_date_to_timestamp(dates['completion_date'], self.app_sdk)
        
        # Set current time for application events if no timestamp is available
        current_ts = int(datetime.now().timestamp())
        if not ordered_ts:
            ordered_ts = current_ts
        
        # Check for application details if available
        application_details = order_data.get('application_details', {})
        application_status = application_details.get('application_status')
        application_event = application_details.get('application_event')
        
        # Map order status to assessment status using enhanced mapping
        assessment_status = map_order_status_to_assessment_status(
            order_status=order_status, 
            application_event=application_event,
            application_status=application_status
        )
        
        # Process all orders and collect their details for comments
        order_details = self._process_order_details(order_data_list)
        
        # Format comments based on content and include all order details
        if order_status and order_status.startswith('Application'):
            comments = f'Form STANDARD status: {order_status}'
        elif application_event:
            comments = f'Form STANDARD status: {application_event}'
        else:
            comments = 'Screening Details:\n' + '\n'.join(order_details)
        
        # Use the appropriate test ID
        test_id = f"{quote_back_data['order_account']}-{quote_back_data['order_package']}" if quote_back_data['order_account'] and quote_back_data['order_package'] else ""
        
        # Build shared metadata even if we don't have a complete assessment yet
        invite_metadata = {
            'email': quote_back_data['email'] or '',
            'profile_id': quote_back_data['profile_id'] or '',
            'pid': quote_back_data['pid'] or '',
            'candidate_id': quote_back_data['candidate_id'] or '',
            'employer_code': quote_back_data['employer_code'] or '',
            'test_id': test_id
        }
        
        # Prepare response
        response_data = {
            'stacktrace': '',
            'actions': [{
                'action_name': 'save_assessment_to_profile_data',
                'request_data': {
                    'invite_metadata': invite_metadata,
                    'assessment_report': {
                        'status': assessment_status,
                        'assigned_ts': ordered_ts,
                        'start_ts': ordered_ts,
                        'completed_ts': completed_ts if order_status == 'Completed' or application_event == 'Application Submitted' else None,
                        'comments': comments if self.comments_enabled else None,
                        'response_json': webhook_payload,
                        'vendor_status': order_status or application_event or '',
                        'test_id': test_id,
                    }
                }
            }],
            'is_success': True,
            'error': False
        }
        
        self.app_sdk.log(f"Webhook processed. Assessment status: {assessment_status}")
        return response_data