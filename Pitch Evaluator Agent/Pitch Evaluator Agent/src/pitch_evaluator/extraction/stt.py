from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from pitch_evaluator.models import TranscriptSegment


@dataclass
class TranscriptionResult:
    """Result from a speech-to-text engine."""

    text: str
    segments: list[TranscriptSegment]
    language: str
    confidence: float


class SpeechToTextEngine(ABC):
    """Abstract interface for speech-to-text engines."""

    @abstractmethod
    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe audio file and return structured result."""
        ...

    @property
    @abstractmethod
    def supported_formats(self) -> set[str]:
        """Return supported audio formats."""
        ...


class MockSTTEngine(SpeechToTextEngine):
    """Mock STT engine for testing without model dependencies."""

    supported_formats: ClassVar[set[str]] = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}

    def __init__(
        self,
        mock_text: str = "This is a mock transcription for testing.",
        mock_segments: list[TranscriptSegment] | None = None,
        language: str = "en",
        confidence: float = 0.95,
    ) -> None:
        self._mock_text = mock_text
        self._mock_segments = mock_segments or [
            TranscriptSegment(
                start_ms=0,
                end_ms=5000,
                speaker_id="speaker_1",
                text=mock_text,
                confidence=confidence,
            )
        ]
        self._language = language
        self._confidence = confidence

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        return TranscriptionResult(
            text=self._mock_text,
            segments=self._mock_segments,
            language=self._language,
            confidence=self._confidence,
        )


def create_stt_engine(engine_type: str = "mock", **kwargs: Any) -> SpeechToTextEngine:
    """Factory function to create STT engine.

    Args:
        engine_type: "mock" for testing, "faster-whisper" for production
        **kwargs: Engine-specific configuration

    Returns:
        SpeechToTextEngine instance
    """
    if engine_type == "mock":
        return MockSTTEngine(**kwargs)
    elif engine_type == "faster-whisper":
        # Lazy import - only if actually used
        try:
            from pitch_evaluator.extraction.whisper_stt import FasterWhisperSTT

            return FasterWhisperSTT(**kwargs)
        except ImportError as e:
            raise RuntimeError(
                "faster-whisper not installed. Install with: pip install faster-whisper"
            ) from e
    else:
        raise ValueError(f"Unknown STT engine type: {engine_type}")