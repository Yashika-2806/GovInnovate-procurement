"""Shared helpers for turning fetched HTML into clean, source-grounded text.

These helpers NEVER add opportunity facts (prizes, deadlines, eligibility, etc.).
They only reproduce the real page content plus factual provenance lines (portal
name, issuing organization from the source registry, and the source URL). All
downstream extraction works exclusively from this real text, in line with the
cardinal rule: no fabricated opportunities.
"""
import logging
from typing import Tuple

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Explicit closure signals used by the monitoring job to detect CLOSED (not EXPIRED)
# opportunities. Kept conservative to avoid false positives.
CLOSURE_MARKERS = (
    "submission closed",
    "submissions closed",
    "submissions are closed",
    "challenge is closed",
    "challenge closed",
    "entries closed",
    "registration closed",
    "registrations closed",
    "closed for submission",
    "closed for submissions",
    "this challenge has ended",
)

_STRIP_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript", "form", "svg", "iframe"]


def html_to_structured_text(
    raw_html: str,
    portal: str,
    organization: str,
    url: str,
    title_fallback: str,
) -> Tuple[str, str]:
    """Convert fetched HTML into clean structured text.

    Returns ``(structured_text, page_title)``. The provenance header lines are
    factual metadata about *where* the content came from; the remainder is the
    page's own headings, paragraphs and list items verbatim.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()

    title_tag = soup.find(["h1"])
    page_title = title_tag.get_text(" ", strip=True) if title_tag else title_fallback

    lines = [
        f"SOURCE PORTAL: {portal}",
        f"ISSUING ORGANIZATION: {organization}",
        f"SOURCE URL: {url}",
        "",
        f"# {page_title}",
    ]

    body = soup.find("main") or soup.find("body") or soup
    seen = set()
    for elem in body.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = elem.get_text(" ", strip=True)
        if len(text) <= 3 or text in seen:
            continue
        seen.add(text)
        if elem.name in ("h1", "h2", "h3", "h4"):
            lines.append(f"\n## {text}")
        else:
            lines.append(f"• {text}")

    return "\n".join(lines), page_title


def visible_text(raw_html: str) -> str:
    """Return lowercase-normalizable plain visible text of a page (for marker scans)."""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    return soup.get_text(" ", strip=True)
