from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AuthorityLevel(str, Enum):
    OFFICIAL = "official"          # Tier 1: gov portal, official org site
    INSTITUTIONAL = "institutional" # Tier 2: universities, research inst
    SECONDARY = "secondary"        # Tier 3: news, aggregators (discovery hints only)


class VerificationStatus(str, Enum):
    VERIFIED_OFFICIAL = "VERIFIED_OFFICIAL"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class SourceRegistryEntry(BaseModel):
    source_id: str
    name: str
    organization: str
    organization_type: str = "government"
    country: str = "IN"
    authority_level: AuthorityLevel = AuthorityLevel.OFFICIAL
    base_url: str
    enabled: bool = True
    adapter: str
    discovery_frequency: str = "daily"


class SourceInfo(BaseModel):
    """Provenance information about the original source of an opportunity."""
    url: str
    canonical_source_url: Optional[str] = None
    source_domain: str
    source_title: Optional[str] = None
    source_type: str = "webpage"  # webpage, pdf, api
    issuing_organization: str
    published_date: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_hash: Optional[str] = None
