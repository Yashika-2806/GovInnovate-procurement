"""Pitch Evaluator execution service and orchestration contract.

Provides the top-level PitchEvaluator service that coordinates multimodal
extraction, evidence extraction, criterion analysis, and deterministic scoring.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field

from pitch_evaluator.analysis import AnalysisOrchestrator
from pitch_evaluator.config import EvaluationCriteriaConfig, load_criteria_config
from pitch_evaluator.extraction import ExtractionFactory
from pitch_evaluator.models import (
    NormalizedPitch,
    PitchEvaluation,
    PitchSegment,
    SourceMetadata,
    SourceModality,
    Transcript,
    TranscriptSegment,
)


class EvaluatePitchRequest(BaseModel):
    """Local integration contract for pitch evaluation requests."""

    pitch_id: Annotated[str, Field(min_length=1, description="Unique identifier for the pitch")]
    startup_id: Annotated[str, Field(min_length=1, description="Unique identifier for the startup")]
    problem_statement_id: Annotated[
        str, Field(default="default_problem_statement", min_length=1, description="Problem statement identifier")
    ] = "default_problem_statement"
    pitch_content: Annotated[
        str | None, Field(default=None, description="Direct text content of the pitch")
    ] = None
    file_path: Annotated[
        str | None, Field(default=None, description="Filesystem path to source pitch document or media file")
    ] = None
    evaluation_config: Annotated[
        dict[str, Any] | None, Field(default=None, description="Optional override criteria configuration")
    ] = None
    context: Annotated[
        dict[str, Any], Field(default_factory=dict, description="Arbitrary contextual metadata")
    ] = Field(default_factory=dict)


class PitchEvaluator:
    """Unified top-level execution service for Pitch Evaluation.

    Executes the 8-stage evaluation pipeline:
    1. Content extraction (multimodal -> NormalizedPitch)
    2. Evidence extraction (keyword/LLM -> EvidenceCitation[])
    3. Criterion analysis (CriterionAnalysisEngine -> CriterionAnalysis[])
    4. Deterministic weighted scoring
    5. Evidence quality calculation
    6. Overall confidence calculation
    7. Deterministic risk signals extraction
    8. Final PitchEvaluation assembly
    """

    def __init__(
        self,
        engine: str = "mock",
        evidence_engine: str = "mock",
        stt_engine: str = "mock",
        criteria_config: EvaluationCriteriaConfig | str | Path | None = None,
        **engine_kwargs: Any,
    ) -> None:
        """Initialize PitchEvaluator service.

        Args:
            engine: Criterion analysis engine type ("mock" or "llm")
            evidence_engine: Evidence extraction engine type ("mock" or "llm")
            stt_engine: Speech-to-text engine type ("mock" or "whisper")
            criteria_config: Criteria config instance or path to YAML config file
            **engine_kwargs: Additional engine kwargs (model, base_url, etc.)
        """
        # Resolve config
        if isinstance(criteria_config, (str, Path)):
            self._criteria_config = load_criteria_config(criteria_config)
        elif criteria_config is None:
            self._criteria_config = load_criteria_config()
        else:
            self._criteria_config = criteria_config

        # Initialize multimodal extraction factory
        self._extraction_factory = ExtractionFactory(stt_engine=stt_engine)

        # Initialize analysis orchestrator
        self._orchestrator = AnalysisOrchestrator(
            engine=engine,
            evidence_engine=evidence_engine,
            criteria_config=self._criteria_config,
            **engine_kwargs,
        )

    @property
    def criteria_config(self) -> EvaluationCriteriaConfig:
        """Return the active criteria configuration."""
        return self._criteria_config

    def evaluate_normalized_pitch(
        self,
        normalized_pitch: NormalizedPitch,
        pitch_id: str,
        startup_id: str,
        problem_statement_id: str,
    ) -> PitchEvaluation:
        """Evaluate an already normalized pitch."""
        start_time = datetime.now(UTC)
        output = self._orchestrator.evaluate(
            normalized_pitch=normalized_pitch,
            pitch_id=pitch_id,
            startup_id=startup_id,
            problem_statement_id=problem_statement_id,
        )
        duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

        # Update processing time in metadata
        output.pitch_evaluation.metadata.processing_time_ms = max(duration_ms, 1)
        return output.pitch_evaluation

    def evaluate_text(
        self,
        text: str,
        pitch_id: str,
        startup_id: str,
        problem_statement_id: str,
    ) -> PitchEvaluation:
        """Evaluate raw text pitch content."""
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Pitch text cannot be empty")

        # Create basic segments from sentences or paragraphs
        paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [clean_text]

        segments: list[PitchSegment] = []
        transcript_segments: list[TranscriptSegment] = []
        current_offset = 0

        for i, para in enumerate(paragraphs):
            seg_len = len(para)
            seg_id = f"text_seg_{i + 1}"
            segments.append(
                PitchSegment(
                    segment_id=seg_id,
                    source=SourceModality.TEXT,
                    start_ref=current_offset,
                    end_ref=current_offset + seg_len,
                    content=para,
                    speaker_id="speaker_1",
                )
            )
            transcript_segments.append(
                TranscriptSegment(
                    start_ms=i * 5000,
                    end_ms=(i + 1) * 5000,
                    speaker_id="speaker_1",
                    text=para,
                    confidence=0.95,
                )
            )
            current_offset += seg_len + 1

        normalized_pitch = NormalizedPitch(
            source_modality=SourceModality.TEXT,
            source_metadata=SourceMetadata(
                filename="direct_text_pitch.txt",
                mime_type="text/plain",
                file_size_bytes=len(clean_text.encode("utf-8")),
                checksum=f"text_cs_{uuid.uuid4().hex[:8]}",
                uploaded_at=datetime.now(UTC),
                uploaded_by="pitch_evaluator_service",
            ),
            transcript=Transcript(
                full_text=clean_text,
                segments=transcript_segments,
                language="en",
                confidence=0.95,
            ),
            visual_observations=[],
            document_content=[],
            segments=segments,
        )

        return self.evaluate_normalized_pitch(
            normalized_pitch=normalized_pitch,
            pitch_id=pitch_id,
            startup_id=startup_id,
            problem_statement_id=problem_statement_id,
        )

    def evaluate_file(
        self,
        source_path: Path | str,
        pitch_id: str,
        startup_id: str,
        problem_statement_id: str,
        metadata: SourceMetadata | None = None,
    ) -> PitchEvaluation:
        """Extract multimodal content from a file and evaluate."""
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Pitch file not found: {path}")

        if metadata is None:
            metadata = SourceMetadata(
                filename=path.name,
                mime_type="application/octet-stream",
                file_size_bytes=path.stat().st_size,
                checksum=f"file_{path.name}_{uuid.uuid4().hex[:8]}",
                uploaded_at=datetime.now(UTC),
                uploaded_by="pitch_evaluator_service",
            )

        normalized_pitch = self._extraction_factory.extract(path, metadata)
        return self.evaluate_normalized_pitch(
            normalized_pitch=normalized_pitch,
            pitch_id=pitch_id,
            startup_id=startup_id,
            problem_statement_id=problem_statement_id,
        )

    def evaluate_pitch(self, request: EvaluatePitchRequest) -> PitchEvaluation:
        """Evaluate a pitch based on an EvaluatePitchRequest."""
        if request.file_path:
            return self.evaluate_file(
                source_path=request.file_path,
                pitch_id=request.pitch_id,
                startup_id=request.startup_id,
                problem_statement_id=request.problem_statement_id,
            )
        elif request.pitch_content is not None:
            return self.evaluate_text(
                text=request.pitch_content,
                pitch_id=request.pitch_id,
                startup_id=request.startup_id,
                problem_statement_id=request.problem_statement_id,
            )
        else:
            raise ValueError("EvaluatePitchRequest must provide either 'pitch_content' or 'file_path'")
