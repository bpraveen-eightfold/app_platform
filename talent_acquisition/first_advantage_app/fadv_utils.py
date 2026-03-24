"""
Utility functions for First Advantage integration.
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Union

from fadv_constants import FADVConstants


def map_order_status_to_assessment_status(
    order_status: Optional[str], 
    application_event: Optional[str] = None, 
    application_status: Optional[str] = None
) -> str:
    """
    Maps First Advantage order status to Eightfold assessment status.
    
    Args:
        order_status: The order status from First Advantage
        application_event: The application event from First Advantage
        application_status: The application status from First Advantage
        
    Returns:
        str: The mapped assessment status for Eightfold
        
    Note:
        Valid assessment statuses are: 'invited', 'in_progress', 'completed', 'reminder_sent', 'expired'
    """
    # Handle application events first - these take precedence
    if application_event:
        app_event_map = {
            'Application Created': FADVConstants.ASSESSMENT_INVITED,  # Maps to "Not Started"
            'Application Expired': FADVConstants.ASSESSMENT_EXPIRED,  # Maps to "Expired"
            'Applicant Invitation Email Resent': FADVConstants.ASSESSMENT_INVITED,  # Maps to "Not Started"
            'Applicant Registered': FADVConstants.ASSESSMENT_IN_PROGRESS,  # Maps to "Started"
            'Consent Accepted': FADVConstants.ASSESSMENT_IN_PROGRESS,  # Maps to "Started"
            'Consent Rejected': FADVConstants.ASSESSMENT_EXPIRED,  # Maps to "DealBroken", using 'expired' as closest match
            'Application Submitted': FADVConstants.ASSESSMENT_COMPLETED,  # Maps to "Completed"
            'Application Complete Email Sent': FADVConstants.ASSESSMENT_COMPLETED,  # Maps to "Completed"
            'BI Submitted': FADVConstants.ASSESSMENT_COMPLETED,  # Maps to "Completed"
            'Application Canceled': FADVConstants.ASSESSMENT_EXPIRED,  # Maps to "Deleted", using 'expired' as closest match
            'Reminder Email Sent': FADVConstants.ASSESSMENT_IN_PROGRESS  # Maps to "Started or Not Started", using 'in_progress'
        }
        return app_event_map.get(application_event, FADVConstants.ASSESSMENT_INVITED)
    
    # If no application event but we have application status
    if application_status:
        app_status_map = {
            'Started': FADVConstants.ASSESSMENT_IN_PROGRESS,
            'Not Started': FADVConstants.ASSESSMENT_INVITED,
            'Expired': FADVConstants.ASSESSMENT_EXPIRED,
            'DealBroken': FADVConstants.ASSESSMENT_EXPIRED,
            'Completed': FADVConstants.ASSESSMENT_COMPLETED,
            'Deleted': FADVConstants.ASSESSMENT_EXPIRED
        }
        return app_status_map.get(application_status, FADVConstants.ASSESSMENT_INVITED)
    
    # If no application info, use order status
    if not order_status:
        return FADVConstants.ASSESSMENT_INVITED  # Default for empty status
    
    # FADV enterprise advantage status mapping
    status_map = {
        'InProgress': FADVConstants.ASSESSMENT_IN_PROGRESS,
        'Completed': FADVConstants.ASSESSMENT_COMPLETED,
        'Canceled': FADVConstants.ASSESSMENT_EXPIRED,
        'Cancelled': FADVConstants.ASSESSMENT_EXPIRED,
        'Expired': FADVConstants.ASSESSMENT_EXPIRED,
        'Disabled': FADVConstants.ASSESSMENT_EXPIRED,
        'Preliminary': FADVConstants.ASSESSMENT_IN_PROGRESS,
        'Hold': FADVConstants.ASSESSMENT_IN_PROGRESS,
        'UnderConstruction': FADVConstants.ASSESSMENT_IN_PROGRESS,
        'UnexpectedStatus': FADVConstants.ASSESSMENT_IN_PROGRESS
    }
    
    # Check if status starts with "Application"
    if order_status.startswith('Application'):
        return FADVConstants.ASSESSMENT_INVITED
    
    return status_map.get(order_status, FADVConstants.ASSESSMENT_IN_PROGRESS)


def convert_date_to_timestamp(date_str: Optional[str], app_sdk = None) -> Optional[int]:
    """
    Converts a date string to UTC timestamp.
    
    Handles multiple date formats:
    - 'MM/DD/YYYY HH:MM:SS AM/PM'
    - 'MM/DD/YYYY'
    - 'YYYY-MM-DD'
    - 'YYYY-MM-DD HH:MM:SS'
    - 'YYYY-MM-DDTHH:MM:SS'
    - 'YYYY-MM-DDTHH:MM:SS.mmmZ' (ISO format)
    
    Args:
        date_str: The date string to convert
        app_sdk: Instance of EFAppSDK for logging
        
    Returns:
        int: Unix timestamp in seconds, or None if conversion fails
    """
    # Handle None or empty string cases early
    if date_str is None or (isinstance(date_str, str) and not date_str.strip()):
        return None
    
    # Handle unexpected types - this should almost never happen due to type hints
    # but is kept as a safety measure
    if not isinstance(date_str, str):
        if app_sdk:
            app_sdk.log(f"Invalid date string type: expected str, got {type(date_str).__name__}")
        return None
        
    # Clean up the date string
    # Remove extra whitespace 
    date_str = date_str.strip()
    # Handle A.M./P.M. format
    date_str = date_str.replace('A.M.', 'AM').replace('P.M.', 'PM')
    # Handle a.m./p.m. format
    date_str = date_str.replace('a.m.', 'AM').replace('p.m.', 'PM')
    
    # Try different date formats
    formats = [
        '%m/%d/%Y %I:%M:%S %p',  # MM/DD/YYYY HH:MM:SS AM/PM
        '%m/%d/%Y %I:%M %p',     # MM/DD/YYYY HH:MM AM/PM
        '%m/%d/%Y',               # MM/DD/YYYY
        '%Y-%m-%d',               # YYYY-MM-DD
        '%Y-%m-%d %H:%M:%S',      # YYYY-MM-DD HH:MM:SS
        '%Y-%m-%dT%H:%M:%S',      # YYYY-MM-DDTHH:MM:SS
        '%Y-%m-%dT%H:%M:%S.%fZ',  # YYYY-MM-DDTHH:MM:SS.mmmZ (ISO format)
    ]
    
    for date_format in formats:
        try:
            date_obj = datetime.strptime(date_str, date_format)
            return int(date_obj.timestamp())
        except ValueError:
            continue
        except Exception as e:
            if app_sdk:
                app_sdk.log(f"Unexpected error parsing date '{date_str}' with format '{date_format}': {str(e)}")
            continue
    
    # If none of the formats worked, log error and return None
    if app_sdk:
        app_sdk.log(f"Error converting date: Could not parse '{date_str}' with any known format")
    return None 