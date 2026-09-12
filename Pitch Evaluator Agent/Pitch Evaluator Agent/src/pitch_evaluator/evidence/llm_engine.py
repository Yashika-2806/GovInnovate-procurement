from __future__ import annotations

import json
import os

from pitch_evaluator.config import EvaluationCriteriaConfig
from pitch_evaluator.evidence.engine import (
    EvidenceExtractionEngine,
    EvidenceExtractionResult,
)
from pitch_evaluator.evidence.llm_models import (
    LLMEvidenceExtractionOutput,
)
from pitch_evaluator.evidence.prompts import (
    EVIDENCE_EXTRACTION_SYSTEM_PROMPT,
    build_user_prompt,
)
from pitch_evaluator.models import NormalizedPitch


class LLMEvidenceEngine(EvidenceExtractionEngine):
    """LLM-based evidence extraction engine.

    Supports any OpenAI-compatible API (including Ollama, vLLM, etc.)
    via the openai Python client.
    """

    def __init__(
        self,
        model: str = "llama3.1:70b",
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        timeout_seconds: int = 120,
    ) -> None:
        """Initialize LLM evidence engine.

        Args:
            model: Model name (e.g., "llama3.1:70b", "gpt-4o")
            base_url: OpenAI-compatible base URL (e.g., "http://localhost:11434/v1" for Ollama)
            api_key: API key (not needed for local Ollama)
            temperature: Sampling temperature (low for structured extraction)
            max_tokens: Maximum output tokens
            timeout_seconds: Request timeout
        """
        self._model = model
        self._base_url = base_url or os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "ollama")
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout_seconds = timeout_seconds

    @property
    def supported_criteria(self) -> list[str]:
        """LLM engine supports all criteria defined in config."""
        return [
            "Problem Validation",
            "Scalability",
            "Feasibility",
            "Cost",
            "Practicality",
            "Solution Fit",
            "Innovation",
            "Technical Feasibility",
            "Market Validation",
            "Team Capability",
            "Implementation Readiness",
            "Government Fit",
            "Business/Sustainability",
            "Competitive Differentiation",
        ]

    def extract_evidence(
        self,
        normalized_pitch: NormalizedPitch,
        criteria_config: EvaluationCriteriaConfig,
    ) -> EvidenceExtractionResult:
        """Extract evidence using LLM with structured output."""
        # Import openai client lazily
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(
                "openai package not installed. Install with: pip install openai"
            ) from e

        client = OpenAI(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=self._timeout_seconds,
        )

        # Build prompts
        user_prompt = build_user_prompt(
            normalized_pitch.model_dump(mode="json"),
            criteria_config.model_dump(mode="json"),
        )

        # Call LLM with structured output
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": EVIDENCE_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            response_format={"type": "json_object"},
        )

        raw_response = response.choices[0].message.content or "{}"

        # Parse and validate structured output
        try:
            parsed = json.loads(raw_response)
            validated_output = LLMEvidenceExtractionOutput.model_validate(parsed)
        except Exception as e:
            raise RuntimeError(f"LLM output validation failed: {e}\nRaw: {raw_response}") from e

        # Convert validated citations to raw dict format for downstream processing
        citations = []
        for citation in validated_output.citations:
            citations.append({
                "claim": citation.claim,
                "criterion": citation.criterion,
                "source_segment_ids": citation.source_segment_ids,
                "evidence_type": citation.evidence_type,
                "verification_level": citation.verification_level,
                "confidence": citation.confidence,
                "notes": citation.notes,
            })

        return EvidenceExtractionResult(
            citations=citations,
            raw_response=raw_response,
        )