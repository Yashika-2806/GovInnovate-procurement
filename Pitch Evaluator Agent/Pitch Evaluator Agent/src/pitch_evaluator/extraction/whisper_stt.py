from __future__ import annotations

import math
from pathlib import Path
from typing import ClassVar

from pitch_evaluator.extraction.stt import SpeechToTextEngine, TranscriptionResult
from pitch_evaluator.models import TranscriptSegment


class FasterWhisperSTT(SpeechToTextEngine):
    """faster-whisper based speech-to-text engine.

    Requires: pip install faster-whisper
    """

    supported_formats: ClassVar[set[str]] = {
        ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4", ".mov", ".webm"
    }

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
        vad_filter: bool = True,
        beam_size: int = 5,
    ) -> None:
        """Initialize faster-whisper model.

        Args:
            model_size: Model size (tiny, base, small, medium, large-v1, large-v2, large-v3)
            device: Device to run on (cpu, cuda, auto)
            compute_type: Quantization type (int8, int8_float16, float16, float32)
            language: Language code (None for auto-detect)
            vad_filter: Enable voice activity detection
            beam_size: Beam size for decoding
        """
        try:
            from faster_whisper import WhisperModel  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError(
                "faster-whisper not installed. Install with: pip install faster-whisper"
            ) from e

        self._model = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )
        self._language = language
        self._vad_filter = vad_filter
        self._beam_size = beam_size

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe audio file using faster-whisper."""
        segments, info = self._model.transcribe(
            str(audio_path),
            language=self._language,
            vad_filter=self._vad_filter,
            beam_size=self._beam_size,
        )

        transcript_segments = []
        full_text_parts = []
        confidences = []

        for segment in segments:
            # faster_whisper Segment has avg_logprob attribute
            avg_logprob = getattr(segment, "avg_logprob", None)
            confidence = max(0.0, min(1.0, math.exp(avg_logprob))) if avg_logprob is not None else 0.5
            confidences.append(confidence)

            ts = TranscriptSegment(
                start_ms=int(segment.start * 1000),
                end_ms=int(segment.end * 1000),
                speaker_id="speaker_1",  # No diarization by default
                text=segment.text.strip(),
                confidence=confidence,
            )
            transcript_segments.append(ts)
            full_text_parts.append(segment.text.strip())

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        return TranscriptionResult(
            text=" ".join(full_text_parts),
            segments=transcript_segments,
            language=info.language or "unknown",
            confidence=avg_confidence,
        )