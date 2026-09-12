import hashlib
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.models.source import AuthorityLevel, SourceRegistryEntry
from src.services.fetcher import SafeFetcher
from src.sources.base import AuthorityEvidence, Candidate, RawSource
from src.sources.html_utils import html_to_structured_text

logger = logging.getLogger(__name__)

# Curated *real, fetchable* Startup India entry points. startupindia.gov.in is an
# Angular single-page app whose challenge listing is rendered client-side and is not
# reliably crawlable from raw HTML, so we seed known-good server-rendered content
# pages. Every URL here must return HTTP 200 with real content; nothing about the
# opportunity (deadline, prize, eligibility) is asserted here — those are extracted
# only from the fetched page. Do NOT add URLs that 404.
STARTUP_INDIA_SEED_PAGES = [
    {
        "title": "Bharat Startup Grand Challenge",
        "url": "https://www.startupindia.gov.in/content/sih/en/bharat-startup-grand-challenge.html",
        "org": "Department for Promotion of Industry and Internal Trade (DPIIT)",
        "snippet": "Startup India flagship initiative bridging startups with real-world technological and industrial problem statements across priority sectors.",
    },
]


class StartupIndiaAdapter:
    """Adapter for official Startup India pages. Fetches live content only; never fabricates."""

    def __init__(self, entry: SourceRegistryEntry):
        self.entry = entry
        self.fetcher = SafeFetcher()

    def discover(self, query: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Candidate]:
        """Return candidate opportunities from curated real Startup India pages."""
        candidates: List[Candidate] = []
        for item in STARTUP_INDIA_SEED_PAGES:
            if query:
                q = query.lower()
                if q not in item["title"].lower() and q not in item["snippet"].lower() and q not in item["org"].lower():
                    continue
            candidates.append(
                Candidate(
                    source_id=self.entry.source_id,
                    title=item["title"],
                    url=item["url"],
                    organization_name=item["org"],
                    source_type="webpage",
                    raw_snippet=item["snippet"],
                    metadata={"portal": "Startup India", "country": "IN"},
                )
            )
        return candidates

    def fetch(self, candidate: Candidate) -> RawSource:
        """Fetch the live challenge webpage and build clean, source-grounded text.

        Raises on any fetch/HTTP failure so the pipeline records the candidate as a
        fetch error instead of persisting fabricated content. A temporary failure
        never becomes a verified opportunity.
        """
        raw = self.fetcher.fetch_sync(candidate.url)
        if raw.status_code != 200 or not raw.text_content:
            raise ValueError(f"Non-200 or empty response ({raw.status_code}) for {candidate.url}")

        structured_text, _ = html_to_structured_text(
            raw_html=raw.raw_html or raw.text_content,
            portal="Startup India (DPIIT, Ministry of Commerce and Industry)",
            organization=candidate.organization_name,
            url=candidate.url,
            title_fallback=candidate.title,
        )
        doc_hash = hashlib.sha256(structured_text.encode("utf-8")).hexdigest()

        return RawSource(
            url=candidate.url,
            final_url=raw.final_url,
            status_code=raw.status_code,
            content_type="text/html",
            text_content=structured_text,
            raw_html=raw.raw_html,
            document_hash=doc_hash,
            metadata={"source_name": self.entry.name, "live_fetched": True},
        )

    def identify_authority(self, raw_source: RawSource) -> AuthorityEvidence:
        """Verify Tier 1 official authority against the .gov.in domain."""
        parsed = urlparse(raw_source.final_url)
        domain = (parsed.hostname or "").lower()

        is_gov_in = domain.endswith(".gov.in") or "startupindia.gov.in" in domain

        return AuthorityEvidence(
            is_authoritative=is_gov_in,
            authority_level=AuthorityLevel.OFFICIAL.value if is_gov_in else AuthorityLevel.SECONDARY.value,
            issuing_organization="Government of India / Startup India",
            domain=domain,
            confidence_score=0.99 if is_gov_in else 0.40,
            verification_notes="Verified against official Government of India .gov.in domain hierarchy.",
        )
