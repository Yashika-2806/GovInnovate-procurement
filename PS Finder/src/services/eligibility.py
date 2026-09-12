import logging
import re
from typing import Tuple
from src.sources.base import RawSource

logger = logging.getLogger(__name__)


class EligibilityClassifier:
    """Classifies whether a candidate is an explicit solution-seeking opportunity vs routine procurement."""

    # Keywords signaling explicit problem/challenge/solution requests
    SOLUTION_SEEKING_KEYWORDS = [
        "challenge", "problem statement", "innovation", "innovator", "startups",
        "solution seeking", "call for solutions", "hackathon", "rfp", "rfe",
        "eoi", "open innovation", "pilot project", "proof of concept", "poc",
        "grand challenge", "development of technology", "prototype", "seek proposals"
    ]

    # Keywords signaling routine procurement / commodity purchases
    ROUTINE_PROCUREMENT_PATTERNS = [
        r"\bsupply of \d+\b",
        r"\bpurchase of \d+\b",
        r"\bprocurement of standard\b",
        r"\bsupply \d+ (standard|cctv|desktops|chairs|laptops|stationery)\b",
        r"\bannual maintenance contract\b",
        r"\bamc for\b",
        r"\bprinting of\b",
        r"\bcleaning services\b",
        r"\bhousekeeping\b",
        r"\bsecurity guard\b"
    ]

    def classify(self, text_content: str, title: str) -> Tuple[str, str]:
        """Returns ('QUALIFIED' | 'REJECTED' | 'NEEDS_REVIEW', reason)."""
        combined = f"{title} {text_content}".lower()

        # Check routine procurement negative filters
        for pattern in self.ROUTINE_PROCUREMENT_PATTERNS:
            if re.search(pattern, combined):
                return (
                    "REJECTED",
                    f"Routine procurement detected matching pattern '{pattern}'. Lacks explicit innovation or problem-solving requirement."
                )

        # Check explicit solution-seeking markers
        matches = [kw for kw in self.SOLUTION_SEEKING_KEYWORDS if kw in combined]
        if len(matches) >= 2:
            return (
                "QUALIFIED",
                f"Explicit solution-seeking challenge verified with keywords: {', '.join(matches[:4])}."
            )
        elif len(matches) == 1:
            return (
                "NEEDS_REVIEW",
                f"Borderline opportunity: only matched single indicator '{matches[0]}'."
            )

        return (
            "REJECTED",
            "Rejected: No explicit problem statement or challenge terminology found."
        )
