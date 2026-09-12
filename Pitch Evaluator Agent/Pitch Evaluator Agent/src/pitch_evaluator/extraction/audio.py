from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pitch_evaluator.extraction.base import BaseExtractor
from pitch_evaluator.extraction.stt import (
    SpeechToTextEngine,
    TranscriptionResult,
    create_stt_engine,
)
from pitch_evaluator.models import (
    NormalizedPitch,
    PitchSegment,
    SourceMetadata,
    SourceModality,
    Transcript,
)


class AudioExtractor(BaseExtractor):
    """Extract audio content via speech-to-text transcription."""

    supported_extensions: ClassVar[set[str]] = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}
    modality: ClassVar[SourceModality] = SourceModality.AUDIO

    def __init__(
        self,
        stt_engine: SpeechToTextEngine | str = "mock",
        max_file_size_bytes: int = 100 * 1024 * 1024,
        **stt_kwargs: object,
    ) -> None:
        """Initialize audio extractor.

        Args:
            stt_engine: SpeechToTextEngine instance or engine type string ("mock", "faster-whisper")
            max_file_size_bytes: Maximum file size (default 100 MB)
            **stt_kwargs: Additional arguments passed to STT engine factory
        """
        self.max_file_size_bytes = max_file_size_bytes

        if isinstance(stt_engine, str):
            self._stt_engine = create_stt_engine(stt_engine, **stt_kwargs)
        else:
            self._stt_engine = stt_engine

    @property
    def stt_engine(self) -> SpeechToTextEngine:
        return self._stt_engine

    def extract(self, source_path: Path, metadata: SourceMetadata) -> NormalizedPitch:
        """Extract audio content via STT and create NormalizedPitch."""
        self.validate_file(source_path)

        # Validate format against STT engine
        ext = source_path.suffix.lower()
        if ext not in self._stt_engine.supported_formats:
            from pitch_evaluator.extraction.exceptions import UnsupportedFormatError

            raise UnsupportedFormatError(
                ext, sorted(self._stt_engine.supported_formats), str(source_path)
            )

        # Transcribe
        try:
            result: TranscriptionResult = self._stt_engine.transcribe(source_path)
        except Exception as e:
            from pitch_evaluator.extraction.exceptions import TranscriptionError

            raise TranscriptionError(str(e), str(source_path)) from e

        if not result.text.strip():
            from pitch_evaluator.extraction.exceptions import EmptyContentError

            raise EmptyContentError(str(source_path))

        # Create transcript
        transcript = Transcript(
            full_text=result.text,
            segments=result.segments,
            language=result.language,
            confidence=result.confidence,
        )

        # Create pitch segments from transcript segments
        segments = []
        for i, seg in enumerate(result.segments):
            segments.append(
                PitchSegment(
                    segment_id=f"seg_{i}",
                    source=SourceModality.AUDIO,
                    start_ref=seg.start_ms,
                    end_ref=seg.end_ms,
                    content=seg.text,
                    speaker_id=seg.speaker_id,
                )
            )

        return NormalizedPitch(
            source_modality=SourceModality.AUDIO,
            source_metadata=metadata,
            transcript=transcript,
            visual_observations=[],
            document_content=[],
            segments=segments,
        )