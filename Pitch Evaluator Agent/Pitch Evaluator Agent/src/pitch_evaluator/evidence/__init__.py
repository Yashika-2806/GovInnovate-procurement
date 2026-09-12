"""Pitch Evaluator evidence extraction package."""

from pitch_evaluator.evidence.engine import (
    EvidenceExtractionEngine,
    EvidenceExtractionResult,
    create_evidence_engine,
)
from pitch_evaluator.evidence.extractor import EvidenceExtractionOutput, EvidenceExtractor
from pitch_evaluator.evidence.llm_engine import LLMEvidenceEngine
from pitch_evaluator.evidence.llm_models import (
    LLMEvidenceCitation,
    LLMEvidenceExtractionOutput,
)
from pitch_evaluator.evidence.mock_engine import MockEvidenceEngine
from pitch_evaluator.evidence.prompts import (
    EVIDENCE_EXTRACTION_SYSTEM_PROMPT,
    build_user_prompt,
)

__all__ = [
    "EVIDENCE_EXTRACTION_SYSTEM_PROMPT",
    "EvidenceExtractionEngine",
    "EvidenceExtractionOutput",
    "EvidenceExtractionResult",
    "EvidenceExtractor",
    "LLMEvidenceCitation",
    "LLMEvidenceEngine",
    "LLMEvidenceExtractionOutput",
    "MockEvidenceEngine",
    "build_user_prompt",
    "create_evidence_engine",
]