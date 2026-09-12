from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Source-grounded provenance evidence for an extracted claim or field."""
    field_name: str = Field(..., description="The field this evidence supports (e.g., 'deadline', 'prize')")
    excerpt: str = Field(..., description="Verbatim text excerpt from the authoritative source")
    source_url: str = Field(..., description="The exact URL where this evidence was found")
    page_number: Optional[int] = Field(None, description="PDF page number if source is a document")
    html_section: Optional[str] = Field(None, description="HTML tag, CSS selector, or heading name")
    document_hash: Optional[str] = Field(None, description="SHA-256 hash of the source document/page")
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

