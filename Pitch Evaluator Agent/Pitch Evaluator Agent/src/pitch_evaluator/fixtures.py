"""Synthetic test fixtures for Pitch Evaluator testing and demonstrations.

All data in this module is explicitly synthetic test data created for automated
testing and evaluation demonstrations. It does NOT represent real companies,
customers, government partnerships, revenue, funding, or deployments.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from pitch_evaluator.models import (
    NormalizedPitch,
    PitchSegment,
    SourceMetadata,
    SourceModality,
    Transcript,
    TranscriptSegment,
)

SYNTHETIC_PITCH_TEXT: Final[str] = (
    "Synthetic Test Pitch: GovProcure Assistant. "
    "Problem Validation: We conducted user research with 45 public procurement officers across municipal jurisdictions, "
    "quantifying that manual RFQ processing incurs 120 hours of administrative delay per tender, with 68% citing compliance "
    "errors as their primary operational pain point. "
    "Scalability: Cloud readiness architecture deployed on containerized microservices with horizontal auto-scaling, "
    "supporting automated unit economics at scale up to 10,000 concurrent bid submissions without degradation. "
    "Feasibility: Technical approach utilizes modular REST APIs and an open-source workflow engine; proof-of-concept "
    "prototypes have completed architectural validation with minimal technical debt and clear dependency mapping. "
    "Cost: Total cost of ownership analysis demonstrates annual budget fit through a tiered subscription pricing model, "
    "delivering a 35% reduction in administrative overhead and a favorable unit economics ROI breakdown. "
    "Government Fit: Fully aligned with public procurement regulations, adhering to SOC2 security standards and data "
    "protection compliance certifications required for municipal procurement workflows. "
    "Team Capability: Founder background and engineering team experience include 15 years in enterprise civic-tech systems, "
    "with an established hiring plan and strong execution track record."
)


def create_synthetic_pitch_fixture() -> NormalizedPitch:
    """Create a realistic, deterministic synthetic NormalizedPitch fixture.

    This fixture contains explicitly labeled synthetic claims across multiple
    criteria (Problem Validation, Scalability, Feasibility, Cost, Government Fit,
    Team Capability) while leaving others without evidence (Business/Sustainability,
    Competitive Differentiation) to demonstrate differentiated scoring and
    gap identification.
    """
    segments = [
        PitchSegment(
            segment_id="synth_seg_1",
            source=SourceModality.TEXT,
            start_ref=0,
            end_ref=250,
            content=(
                "Synthetic Test Pitch: User research across municipal public procurement jurisdictions "
                "quantifying 120 hours of administrative delay per tender, with pain point evidence showing "
                "compliance verification bottlenecks."
            ),
            speaker_id="founder_synth",
        ),
        PitchSegment(
            segment_id="synth_seg_2",
            source=SourceModality.TEXT,
            start_ref=250,
            end_ref=500,
            content=(
                "Synthetic Test Pitch: Scalability strategy demonstrates cloud readiness architecture on containerized "
                "services with horizontal auto-scaling to process high-volume procurement tenders at national scale."
            ),
            speaker_id="founder_synth",
        ),
        PitchSegment(
            segment_id="synth_seg_3",
            source=SourceModality.TEXT,
            start_ref=500,
            end_ref=750,
            content=(
                "Synthetic Test Pitch: Technical feasibility and engineering approach leverages modular architecture decisions, "
                "working software prototypes, and dependency analysis for reliable integration."
            ),
            speaker_id="founder_synth",
        ),
        PitchSegment(
            segment_id="synth_seg_4",
            source=SourceModality.TEXT,
            start_ref=750,
            end_ref=1000,
            content=(
                "Synthetic Test Pitch: Transparent pricing model and total cost of ownership structure designed for "
                "municipal budget fit with projected cost savings and positive unit economics ROI."
            ),
            speaker_id="founder_synth",
        ),
        PitchSegment(
            segment_id="synth_seg_5",
            source=SourceModality.TEXT,
            start_ref=1000,
            end_ref=1250,
            content=(
                "Synthetic Test Pitch: Government fit verified through compliance certifications, security standards alignment, "
                "and public procurement workflow compatibility."
            ),
            speaker_id="founder_synth",
        ),
        PitchSegment(
            segment_id="synth_seg_6",
            source=SourceModality.TEXT,
            start_ref=1250,
            end_ref=1500,
            content=(
                "Synthetic Test Pitch: Team capability grounded in founder background and civic technology engineering experience, "
                "supported by structured advisory roles and an execution track record."
            ),
            speaker_id="founder_synth",
        ),
    ]

    transcript_segments = [
        TranscriptSegment(
            start_ms=i * 5000,
            end_ms=(i + 1) * 5000,
            speaker_id="founder_synth",
            text=seg.content,
            confidence=0.95,
        )
        for i, seg in enumerate(segments)
    ]

    return NormalizedPitch(
        source_modality=SourceModality.TEXT,
        source_metadata=SourceMetadata(
            filename="synthetic_gov_pitch.txt",
            mime_type="text/plain",
            file_size_bytes=len(SYNTHETIC_PITCH_TEXT),
            checksum="synthetic_fixture_sha256_placeholder",
            uploaded_at=datetime.now(UTC),
            uploaded_by="govinnovate_test_suite",
        ),
        transcript=Transcript(
            full_text=SYNTHETIC_PITCH_TEXT,
            segments=transcript_segments,
            language="en",
            confidence=0.95,
        ),
        visual_observations=[],
        document_content=[],
        segments=segments,
    )
