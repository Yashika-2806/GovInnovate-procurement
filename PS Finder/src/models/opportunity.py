from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.models.evidence import Evidence
from src.models.organization import Organization
from src.models.source import SourceInfo, VerificationStatus


class OpportunityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class OpportunityType(str, Enum):
    INNOVATION_CHALLENGE = "innovation_challenge"
    RFP = "rfp"
    RFE = "rfe"
    EOI = "eoi"
    TENDER_PROBLEM_STATEMENT = "tender_problem_statement"
    OPEN_INNOVATION_REQUEST = "open_innovation_request"


class Geography(BaseModel):
    country: Optional[str] = "India"
    region: Optional[str] = None  # state / province
    city: Optional[str] = None


class PrizeInfo(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = "INR"
    raw_text: Optional[str] = None


class FundingInfo(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = "INR"
    raw_text: Optional[str] = None


class Opportunity(BaseModel):
    """Normalized, verified problem/challenge opportunity record."""
    id: str = Field(..., description="Unique opportunity identifier (e.g., opp_startup_india_123)")
    title: str = Field(..., description="Official title from original source")
    problem_statement: str = Field(..., description="Explicit solution-seeking request/problem statement")

    organization: Organization = Field(..., description="Issuing organization details")

    opportunity_type: OpportunityType = Field(..., description="Normalized opportunity type")
    source_opportunity_type: Optional[str] = Field(None, description="Exact source terminology")

    domains: List[str] = Field(default_factory=list, description="Categorized domains (e.g., healthcare, smart_cities)")
    geography: Geography = Field(default_factory=Geography)

    status: OpportunityStatus = Field(default=OpportunityStatus.ACTIVE)

    published_date: Optional[str] = Field(None, description="Publication date as ISO string or source date")
    deadline: Optional[str] = Field(None, description="Submission deadline")

    prize: Optional[PrizeInfo] = None
    funding: Optional[FundingInfo] = None
    support: Optional[str] = Field(None, description="Explicit support provided (e.g. pilot, mentorship, data access)")

    eligibility: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    expected_outcome: Optional[str] = None

    verification_status: VerificationStatus = Field(default=VerificationStatus.VERIFIED_OFFICIAL)
    source: SourceInfo
    source_evidence: List[Evidence] = Field(default_factory=list)

    version: int = Field(default=1)
    unverified_duplicate_of: Optional[str] = Field(None, description="Pointer if flagged as uncertain duplicate (Choice 9B)")

    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_changed_at: Optional[datetime] = None
