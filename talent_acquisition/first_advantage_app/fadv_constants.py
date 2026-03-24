"""
Constants for First Advantage integration.
"""
from typing import Final


class FADVConstants:
    """Constants for First Advantage API."""

    # Assessment status mappings (used in the response)
    ASSESSMENT_INVITED: Final[str] = 'invited'
    ASSESSMENT_IN_PROGRESS: Final[str] = 'in_progress'
    ASSESSMENT_COMPLETED: Final[str] = 'completed'
    ASSESSMENT_EXPIRED: Final[str] = 'expired'

    # Default timeout for API requests (seconds)
    TIMEOUT_SECS: Final[int] = 120
    
    # Default API path endpoints
    CANDIDATE_ENDPOINT: Final[str] = '/candidate'
    INVITE_ENDPOINT: Final[str] = '/invite'
    ACCOUNTS_ENDPOINT: Final[str] = '/accounts'
    PACKAGES_ENDPOINT: Final[str] = '/packages'
