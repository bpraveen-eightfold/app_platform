"""
Data classes for First Advantage integration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union


@dataclass
class FADVPerson:
    """
    Represents a person in the First Advantage system.
    
    Attributes:
        given_name: First name of the person
        family_name: Last name of the person
        type: Type of person, typically "subject"
    """
    given_name: str
    family_name: str
    type: str = "subject"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API requests."""
        return {
            "given_name": self.given_name,
            "family_name": self.family_name,
            "type": self.type
        }


@dataclass
class FADVCandidate:
    """
    Represents a candidate in the First Advantage system.
    
    Attributes:
        override_candidate_data: Whether to override existing candidate data
        persons: List of persons associated with this candidate
        email: Candidate's email address
    """
    override_candidate_data: str = "true"
    persons: List[Dict[str, str]] = field(default_factory=list)
    email: str = ""
    
    def __post_init__(self) -> None:
        """Ensure persons list is initialized properly."""
        if not self.persons:
            self.persons = []
    
    def add_person(self, given_name: str, family_name: str) -> None:
        """
        Add a person to the candidate.
        
        Args:
            given_name: First name of the person
            family_name: Last name of the person
        """
        person = FADVPerson(given_name=given_name, family_name=family_name)
        self.persons.append(person.to_dict())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            "override_candidate_data": self.override_candidate_data,
            "persons": self.persons,
            "email": self.email
        }


@dataclass
class FADVQuoteBack:
    """
    Represents a quote back item in the First Advantage system.
    
    Quote backs are used to pass metadata through the workflow.
    
    Attributes:
        name: Name of the quote back
        value: Value of the quote back
    """
    name: str
    value: Union[str, int]
    
    def to_dict(self) -> Dict[str, Union[str, int]]:
        """Convert to dictionary for API requests."""
        return {
            "name": self.name,
            "value": self.value
        }


@dataclass
class FADVOrderAs:
    """
    Represents order_as information in the First Advantage system.
    
    Identifies the account and user ordering the background check.
    
    Attributes:
        account_id: ID of the account
        user_id: ID of the user
        email: Email of the user
    """
    account_id: str
    user_id: str = "XCHANGE"
    email: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API requests."""
        return {
            "account_id": self.account_id,
            "user_id": self.user_id,
            "email": self.email
        }


@dataclass
class FADVPositionLocation:
    """
    Represents a position location in the First Advantage system.
    
    Attributes:
        country: Country code (e.g., "US")
        state: State or province
        city: City
    """
    country: str = "US"
    state: str = ""
    city: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API requests."""
        return {
            "country": self.country,
            "state": self.state,
            "city": self.city
        }


@dataclass
class FADVInviteRequest:
    """
    Represents an invite request to the First Advantage system.
    
    Attributes:
        candidate_id: ID of the candidate
        package_id: ID of the package
        quote_backs: List of quote backs for the request
        additional_attributes: Additional attributes for the request
        position_locations: List of position locations
    """
    candidate_id: str
    package_id: str
    quote_backs: List[Dict[str, Union[str, int]]] = field(default_factory=list)
    additional_attributes: Dict[str, Any] = field(default_factory=dict)
    position_locations: List[Dict[str, str]] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Ensure collections are initialized properly."""
        if self.quote_backs is None:
            self.quote_backs = []
        if self.additional_attributes is None:
            self.additional_attributes = {}
        if self.position_locations is None:
            self.position_locations = []
    
    def add_quote_back(self, name: str, value: Union[str, int]) -> None:
        """
        Add a quote back to the invite request.
        
        Args:
            name: Name of the quote back
            value: Value of the quote back
        """
        self.quote_backs.append(FADVQuoteBack(name, str(value)).to_dict())
    
    def set_order_as(self, account_id: str, user_id: str = "XCHANGE", email: str = "") -> None:
        """
        Set the order_as information for the invite request.
        
        Args:
            account_id: ID of the account
            user_id: ID of the user
            email: Email of the user
        """
        self.additional_attributes["order_as"] = FADVOrderAs(
            account_id=account_id,
            user_id=user_id,
            email=email
        ).to_dict()
    
    def add_position_location(self, country: str = "US", state: str = "", city: str = "") -> None:
        """
        Add a position location to the invite request.
        
        Args:
            country: Country code (e.g., "US")
            state: State or province
            city: City
        """
        self.position_locations.append(
            FADVPositionLocation(country, state, city).to_dict()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            "candidate_id": self.candidate_id,
            "package_id": self.package_id,
            "quote_backs": self.quote_backs,
            "additional_attributes": self.additional_attributes,
            "position_locations": self.position_locations
        }


@dataclass
class FADVPackage:
    """
    Represents a package in the First Advantage system.
    
    Attributes:
        package_id: ID of the package
        name: Name of the package
        account_name: Name of the account
        duration_minutes: Duration of the package in minutes
        published: Whether the package is published
    """
    package_id: str
    name: str
    account_name: str = ""
    duration_minutes: str = ""
    published: str = ""
    
    @property
    def id(self) -> str:
        """Return the ID of the package (API expects 'id' in response)."""
        return self.package_id
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API response."""
        return {
            "duration_minutes": self.duration_minutes,
            "id": self.package_id,
            "name": f"{self.account_name} - {self.name}" if self.account_name else self.name,
            "published": self.published
        } 