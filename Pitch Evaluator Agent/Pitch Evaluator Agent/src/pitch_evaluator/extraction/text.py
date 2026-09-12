from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pitch_evaluator.extraction.base import BaseExtractor
from pitch_evaluator.models import (
    NormalizedPitch,
    PitchSegment,
    SourceMetadata,
    SourceModality,
    Transcript,
    TranscriptSegment,
)


class TextExtractor(BaseExtractor):
    """Extract text content from plain text files."""

    supported_extensions: ClassVar[set[str]] = {".txt", ".md", ".markdown", ".text"}
    modality: ClassVar[SourceModality] = SourceModality.TEXT

    def __init__(self, max_file_size_bytes: int = 10 * 1024 * 1024) -> None:
        """Initialize with configurable max file size (default 10 MB for text)."""
        self.max_file_size_bytes = max_file_size_bytes

    def extract(self, source_path: Path, metadata: SourceMetadata) -> NormalizedPitch:
        """Extract text content and create NormalizedPitch with segments."""
        self.validate_file(source_path)

        content = source_path.read_text(encoding="utf-8")
        if not content.strip():
            from pitch_evaluator.extraction.exceptions import EmptyContentError

            raise EmptyContentError(str(source_path))

        # Create transcript from full text
        segment = TranscriptSegment(
            start_ms=0,
            end_ms=0,  # No timing for plain text
            speaker_id="speaker_1",
            text=content,
            confidence=1.0,  # Text is exact, not transcribed
        )

        transcript = Transcript(
            full_text=content,
            segments=[segment],
            language="en",  # Default, could be detected
            confidence=1.0,
        )

        # Create pitch segments - split by paragraphs for traceability
        segments = self._create_segments(content)

        return NormalizedPitch(
            source_modality=SourceModality.TEXT,
            source_metadata=metadata,
            transcript=transcript,
            visual_observations=[],
            document_content=[],
            segments=segments,
        )

    def _create_segments(self, content: str) -> list[PitchSegment]:
        """Create traceable segments from text content."""
        segments = []
        # Split by double newline (paragraphs) or single lines
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            # Fallback: split by lines
            paragraphs = [line.strip() for line in content.split("\n") if line.strip()]

        char_offset = 0
        for i, para in enumerate(paragraphs):
            # Find the actual position in original content
            start_ref = content.find(para, char_offset)
            if start_ref == -1:
                start_ref = char_offset
            end_ref = start_ref + len(para)
            char_offset = end_ref

            segments.append(
                PitchSegment(
                    segment_id=f"seg_{i}",
                    source=SourceModality.TEXT,
                    start_ref=start_ref,
                    end_ref=end_ref,
                    content=para,
                    speaker_id="speaker_1",
                )
            )

        # If no paragraphs found, create single segment
        if not segments:
            segments.append(
                PitchSegment(
                    segment_id="seg_0",
                    source=SourceModality.TEXT,
                    start_ref=0,
                    end_ref=len(content),
                    content=content,
                    speaker_id="speaker_1",
                )
            )

        return segments