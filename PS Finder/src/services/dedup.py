import difflib
import logging
from typing import List, Optional, Tuple

from src.models.opportunity import Opportunity
from src.repositories.opportunities import OpportunityRepository

logger = logging.getLogger(__name__)


class DeduplicationService:
    """Detects exact and semantic duplicates, applying automated reference linking (Choice 9B)."""

    def __init__(self, repo: OpportunityRepository):
        self.repo = repo

    def check_duplicate(self, candidate: Opportunity, existing_list: List[Opportunity]) -> Tuple[bool, Optional[str], str]:
        """
        Check if candidate opportunity duplicates any existing record.
        Returns:
            (is_exact_match: bool, duplicate_opp_id: Optional[str], decision: str)
            decision can be 'UNIQUE', 'EXACT_DUPLICATE', or 'NEEDS_REVIEW'
        """
        for existing in existing_list:
            # 1. Canonical URL or ID match -> Exact match
            if existing.id == candidate.id or existing.source.url == candidate.source.url:
                return (True, existing.id, "EXACT_DUPLICATE")

            # 2. Same organization and title similarity
            same_org = existing.organization.name.lower().strip() == candidate.organization.name.lower().strip()
            title_ratio = difflib.SequenceMatcher(None, existing.title.lower(), candidate.title.lower()).ratio()

            if same_org and title_ratio > 0.85:
                # High confidence duplicate from same organization
                return (True, existing.id, "EXACT_DUPLICATE")

            # 3. High title similarity across different URLs or subtle variations -> Flag as uncertain duplicate
            if title_ratio > 0.75:
                # Flag as NEEDS_REVIEW / uncertain duplicate (Choice 9B)
                return (False, existing.id, "NEEDS_REVIEW")

        return (False, None, "UNIQUE")
