import logging
from urllib.parse import urlparse
from typing import Optional, Tuple

from src.models.source import AuthorityLevel, VerificationStatus
from src.sources.base import AuthorityEvidence, RawSource

logger = logging.getLogger(__name__)


class VerificationService:
    """Verifies source authenticity and authoritative provenance."""

    OFFICIAL_DOMAINS = [
        ".gov.in",
        ".nic.in",
        ".gov",
        "startupindia.gov.in",
        "mygov.in",
        "innovateindia.mygov.in",
        "meity.gov.in",
        "psa.gov.in",
        "niti.gov.in",
        "gem.gov.in",
        "eprocure.gov.in",
    ]

    SECONDARY_DOMAINS = [
        "medium.com",
        "linkedin.com",
        "twitter.com",
        "x.com",
        "facebook.com",
        "news.google.com",
        "timesofindia.indiatimes.com",
        "thehindu.com",
        "techcrunch.com",
        "yourstory.com",
        "inc42.com"
    ]

    def verify_source(self, raw_source: RawSource, initial_evidence: Optional[AuthorityEvidence] = None) -> Tuple[VerificationStatus, str]:
        """Determine verification status based on domain authority, source structure, and anti-spoofing checks."""
        parsed = urlparse(raw_source.final_url)
        hostname = (parsed.hostname or "").lower()

        # Check secondary sources: immediate rejection from VERIFIED_OFFICIAL
        for sec_domain in self.SECONDARY_DOMAINS:
            if hostname == sec_domain or hostname.endswith("." + sec_domain):
                return (
                    VerificationStatus.REJECTED,
                    f"Rejected: Source '{hostname}' is a secondary or media domain. Tier 1 authoritative source required."
                )

        # Check official domain whitelist / hierarchy
        is_official = any(hostname.endswith(off) or hostname == off for off in self.OFFICIAL_DOMAINS)

        if initial_evidence and initial_evidence.is_authoritative:
            is_official = True

        if is_official:
            return (
                VerificationStatus.VERIFIED_OFFICIAL,
                f"Verified against authoritative official government source ({hostname})."
            )

        # Non-whitelisted domain: check if institutional or needs manual review
        if hostname.endswith(".edu") or hostname.endswith(".ac.in") or hostname.endswith(".org"):
            return (
                VerificationStatus.NEEDS_REVIEW,
                f"Source ({hostname}) is institutional. Needs review to confirm official issuance."
            )

        return (
            VerificationStatus.NEEDS_REVIEW,
            f"Unconfirmed authority level for domain '{hostname}'."
        )
