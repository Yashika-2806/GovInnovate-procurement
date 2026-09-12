import hashlib
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx

from src.models.source import AuthorityLevel, SourceRegistryEntry
from src.services.fetcher import SafeFetcher
from src.sources.base import AuthorityEvidence, Candidate, RawSource
from src.sources.html_utils import html_to_structured_text

logger = logging.getLogger(__name__)

# Real, verified-live challenge pages on innovateindia.mygov.in used as a fallback
# seed when homepage crawling yields nothing (e.g. markup change). Every URL must
# return HTTP 200 with real content. NO deadlines/prizes are declared here — those
# are extracted only from the fetched page, per the no-fabrication rule.
VERIFIED_MYGOV_CHALLENGES = [
    {
        "title": "Avinya’27 – Energy Startup Challenge",
        "url": "https://innovateindia.mygov.in/avinya27-energy-startup-challenge/",
        "org": "Ministry of Petroleum & Natural Gas / MyGov",
        "snippet": "Energy startup competition promoting Indian startups in the energy sector with focus on innovation, sustainability and clean energy.",
    },
    {
        "title": "D.E.S.I.G.N for BioE3 Challenge",
        "url": "https://innovateindia.mygov.in/bioe3/",
        "org": "Department of Biotechnology (DBT), Ministry of Science and Technology",
        "snippet": "Challenge inviting innovators to harness biomanufacturing and bioeconomy solutions for climate, healthcare and sustainable food systems.",
    },
    {
        "title": "Innovation for Her",
        "url": "https://innovateindia.mygov.in/innovation-for-her/",
        "org": "Ministry of Women and Child Development",
        "snippet": "Inviting technology innovators to develop digital and IoT solutions for women's safety in public and workspace environments.",
    },
    {
        "title": "Digital Shram Sankalp",
        "url": "https://innovateindia.mygov.in/digital-shram-sankalp/",
        "org": "Ministry of Labour and Employment",
        "snippet": "Innovation ideathon seeking AI, ML and digital solutions to modernize labour welfare and social security delivery.",
    },
]

# Non-challenge slugs seen on the homepage that must not be treated as opportunities.
_NON_CHALLENGE_SLUGS = {
    "hi", "as", "bn", "gu", "kn", "ml", "mr", "or", "pa", "ta", "te", "ur",
    "login-with-otp", "privacy-policy", "terms-conditions", "about", "faq",
    "contact-us", "sitemap", "disclaimer", "help", "user", "dashboard",
}


class MyGovAdapter:
    """Adapter for MyGov Innovate challenges. Live web crawling + verified-real fallback."""

    def __init__(self, entry: SourceRegistryEntry):
        self.entry = entry
        self.fetcher = SafeFetcher()

    def discover(self, query: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[Candidate]:
        """Discover live challenges directly from innovateindia.mygov.in with a verified fallback."""
        candidates: List[Candidate] = []
        found_urls = set()

        # 1. Attempt live discovery from the portal homepage.
        try:
            with httpx.Client(headers=self.fetcher.headers, timeout=12.0, follow_redirects=True) as client:
                resp = client.get("https://innovateindia.mygov.in/")
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content.decode("utf-8", errors="replace"), "html.parser")
                    for a in soup.find_all("a", href=True):
                        href = a.get("href", "").strip()
                        if not href.startswith("https://innovateindia.mygov.in/"):
                            continue

                        path_parts = [p for p in urlparse(href).path.split("/") if p]
                        if len(path_parts) != 1:
                            continue

                        slug = path_parts[0]
                        if slug.lower() in _NON_CHALLENGE_SLUGS:
                            continue

                        full_url = f"https://innovateindia.mygov.in/{slug}/"
                        if full_url in found_urls:
                            continue
                        found_urls.add(full_url)

                        link_text = a.get_text(" ", strip=True)
                        title = link_text if len(link_text) > 8 else slug.replace("-", " ").title()
                        snippet = f"Government innovation challenge published on MyGov Innovate: {title}."

                        candidates.append(
                            Candidate(
                                source_id=self.entry.source_id,
                                title=title,
                                url=full_url,
                                organization_name="Government of India / MyGov",
                                source_type="webpage",
                                raw_snippet=snippet,
                                metadata={"portal": "MyGov Innovate", "country": "IN", "slug": slug},
                            )
                        )
                    logger.info("Discovered %d live challenge links from MyGov Innovate.", len(candidates))
        except Exception as e:
            logger.warning("Live discovery from MyGov Innovate failed: %s. Using verified catalogue.", e)

        # 2. Fallback to the verified-real catalogue if the crawl yielded nothing.
        if not candidates:
            for item in VERIFIED_MYGOV_CHALLENGES:
                candidates.append(
                    Candidate(
                        source_id=self.entry.source_id,
                        title=item["title"],
                        url=item["url"],
                        organization_name=item["org"],
                        source_type="webpage",
                        raw_snippet=item["snippet"],
                        metadata={"portal": "MyGov Innovate", "country": "IN"},
                    )
                )

        # 3. Optional query filter.
        if query:
            q = query.lower()
            candidates = [
                c for c in candidates
                if q in c.title.lower() or q in (c.raw_snippet or "").lower() or q in c.organization_name.lower()
            ]

        return candidates

    def fetch(self, candidate: Candidate) -> RawSource:
        """Fetch the live challenge webpage and build clean, source-grounded text.

        Raises on any fetch/HTTP failure so the pipeline records a fetch error rather
        than persisting fabricated content. A temporary failure never becomes verified.
        """
        raw = self.fetcher.fetch_sync(candidate.url)
        if raw.status_code != 200 or not raw.text_content:
            raise ValueError(f"Non-200 or empty response ({raw.status_code}) for {candidate.url}")

        structured_text, _ = html_to_structured_text(
            raw_html=raw.raw_html or raw.text_content,
            portal="MyGov Innovate (Government of India)",
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
        """Verify Tier 1 official government authority (.gov.in / mygov.in)."""
        parsed = urlparse(raw_source.final_url)
        domain = (parsed.hostname or "").lower()
        is_mygov = domain.endswith("mygov.in") or domain.endswith(".gov.in")

        return AuthorityEvidence(
            is_authoritative=is_mygov,
            authority_level=AuthorityLevel.OFFICIAL.value if is_mygov else AuthorityLevel.SECONDARY.value,
            issuing_organization="Government of India / MyGov",
            domain=domain,
            confidence_score=0.99 if is_mygov else 0.30,
            verification_notes="Verified against official Government of India (.gov.in / mygov.in) domain hierarchy.",
        )
