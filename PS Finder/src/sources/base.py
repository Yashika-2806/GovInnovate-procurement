from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class Candidate(BaseModel):
    """Discovered candidate opportunity before full extraction and verification."""
    source_id: str
    title: str
    url: str
    organization_name: str
    source_type: str = "webpage"  # webpage, pdf, api
    raw_snippet: Optional[str] = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RawSource(BaseModel):
    """Raw content fetched from an authoritative or candidate URL."""
    url: str
    final_url: str
    status_code: int
    content_type: str
    text_content: str
    raw_html: Optional[str] = None
    document_hash: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuthorityEvidence(BaseModel):
    """Evidence of source authenticity and authority tier."""
    is_authoritative: bool
    authority_level: str  # official (Tier 1), institutional (Tier 2), secondary (Tier 3)
    issuing_organization: str
    domain: str
    confidence_score: float
    verification_notes: str


@runtime_checkable
class SourceAdapter(Protocol):
    """Abstract contract for source ingestion adapters."""

    def discover(self, query: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Candidate]:
        """Discover candidate solution-seeking opportunities from this source."""
        ...

    def fetch(self, candidate: Candidate) -> RawSource:
        """Fetch raw content and metadata for candidate."""
        ...

    def identify_authority(self, raw_source: RawSource) -> AuthorityEvidence:
        """Verify if source is official/authoritative for issuing organization."""
        ...
