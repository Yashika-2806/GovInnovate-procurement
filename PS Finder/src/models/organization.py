from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class OrganizationType(str, Enum):
    GOVERNMENT = "government"
    PRIVATE = "private"
    INSTITUTION = "institution"


class GovernmentLevel(str, Enum):
    NATIONAL = "national"
    STATE = "state"
    REGIONAL = "regional"
    MUNICIPAL = "municipal"
    PSU = "psu"
    INSTITUTION = "institution"
    PUBLIC_AUTHORITY = "public_authority"


class Organization(BaseModel):
    """Issuing organization details."""
    name: str = Field(..., description="Official name of the issuing organization")
    type: OrganizationType = Field(..., description="Organization sector type")
    level: Optional[str] = Field(None, description="Government level if applicable (e.g., 'municipal', 'national')")
    jurisdiction: Optional[str] = Field(None, description="Geographic jurisdiction of the organization")
    website: Optional[str] = Field(None, description="Official website URL")
