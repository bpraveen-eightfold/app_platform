from dataclasses import dataclass
from typing import Optional, List
from typing import Literal
from sterling_constants import SterlingConstants

@dataclass
class SterlingPackage:
    id: str
    title: str
    active: bool
    type: str
    components: List[str] = None
    requiredFields: List[str] = None

@dataclass
class SterlingCandidateDriverLicense:
    licenseNumber: str
    type: str
    issuingAgency: str

@dataclass
class SterlingCandidateAddress:
    addressLine: str
    municipality: str
    regionCode: str
    postalCode: str
    countryCode: str
    country: str
    validFrom: Optional[str]
    validTo: Optional[str]

@dataclass
class SterlingCandidate:
    id: Optional[str] = None
    clientReferenceId: Optional[str] = None
    email: str = None
    givenName: str = None
    confirmedNoMiddleName: Optional[bool] = None
    familyName: str = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    ssn: Optional[str] = None
    address: Optional[SterlingCandidateAddress] = None
    additionalAddresses: Optional[List[SterlingCandidateAddress]] = None
    aliases: Optional[List[dict]] = None
    educationHistory: Optional[List[dict]] = None
    employmentHistory: Optional[List[dict]] = None
    licenses: Optional[List[dict]] = None
    screeningIds: Optional[List[str]] = None
    driversLicense: Optional[SterlingCandidateDriverLicense] = None

    def to_dict(self):
        return {
            'id': self.id,
            'clientReferenceId': self.clientReferenceId,
            'email': self.email,
            'givenName': self.givenName,
            'confirmedNoMiddleName': self.confirmedNoMiddleName,
            'familyName': self.familyName,
            'dob': self.dob,
            'phone': self.phone,
            'ssn': self.ssn,
            'address': self.address,
            'additionalAddresses': self.additionalAddresses,
            'aliases': self.aliases,
            'educationHistory': self.educationHistory,
            'employmentHistory': self.employmentHistory,
            'licenses': self.licenses,
            'screeningIds': self.screeningIds,
            'driversLicense': self.driversLicense
        }

@dataclass
class SterlingSubAccount:
    accountId: str
    accountName: str

@dataclass
class SterlingScreeningInvite:
    method: Literal[SterlingConstants.SCREENING_METHOD_EMAIL, SterlingConstants.SCREENING_METHOD_LINK]

class SterlingCallback:
    def __init__(self, uri, credentials):
        self.uri = uri
        self.credentials = credentials

    def to_dict(self):
        return {
            'uri': self.uri,
            'credentials': self.credentials
        }


@dataclass
class SterlingScreening:
    id: str
    packageId: str
    candidateId: str
    status: str
    result: str
    reportItems: List[dict]
    accountName: Optional[str] = None
    updatedAt: Optional[str] = None
    invite: Optional[SterlingScreeningInvite] = None
    links: Optional[dict] = None
    estimatedCompletionTime: Optional[str] = None
    accountId: Optional[str] = None
    packageName: Optional[str] = None


