from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, ClassVar

from pitch_evaluator.extraction.base import BaseExtractor
from pitch_evaluator.extraction.stt import (
    SpeechToTextEngine,
    TranscriptionResult,
    create_stt_engine,
)
from pitch_evaluator.models import (
    NormalizedPitch,
    ObservationType,
    PitchSegment,
    SourceMetadata,
    SourceModality,
    Transcript,
    TranscriptSegment,
    VisualObservation,
)


class VideoExtractor(BaseExtractor):
    """Extract video content via audio extraction + STT + optional keyframe extraction."""

    supported_extensions: ClassVar[set[str]] = {
        ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"
    }
    modality: ClassVar[SourceModality] = SourceModality.VIDEO

    # Keywords that trigger visual analysis
    VISUAL_TRIGGER_KEYWORDS: ClassVar[set[str]] = {
        "demo",
        "demonstration",
        "prototype",
        "show",
        "dashboard",
        "deploy",
        "deployment",
        "ui",
        "interface",
        "screen",
        "app",
        "application",
        "product",
        "hardware",
        "device",
    }

    def __init__(
        self,
        stt_engine: SpeechToTextEngine | str = "mock",
        max_file_size_bytes: int = 500 * 1024 * 1024,
        keyframe_interval_seconds: int = 10,
        enable_keyframe_extraction: bool = True,
        ffmpeg_timeout_seconds: int = 300,
        **stt_kwargs: Any,
    ) -> None:
        """Initialize video extractor.

        Args:
            stt_engine: SpeechToTextEngine instance or engine type string
            max_file_size_bytes: Maximum file size (default 500 MB)
            keyframe_interval_seconds: Interval for keyframe extraction (default 10s)
            enable_keyframe_extraction: Whether to extract keyframes (default True)
            ffmpeg_timeout_seconds: Timeout for ffmpeg operations (default 300s)
            **stt_kwargs: Additional arguments for STT engine
        """
        self.max_file_size_bytes = max_file_size_bytes
        self.keyframe_interval_seconds = keyframe_interval_seconds
        self.enable_keyframe_extraction = enable_keyframe_extraction
        self.ffmpeg_timeout_seconds = ffmpeg_timeout_seconds

        if isinstance(stt_engine, str):
            self._stt_engine = create_stt_engine(stt_engine, **stt_kwargs)
        else:
            self._stt_engine = stt_engine

    @property
    def stt_engine(self) -> SpeechToTextEngine:
        return self._stt_engine

    def extract(self, source_path: Path, metadata: SourceMetadata) -> NormalizedPitch:
        """Extract video content: audio -> STT + keyframes -> NormalizedPitch."""
        self.validate_file(source_path)

        # Extract audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            audio_path = Path(tmp_audio.name)

        try:
            self._extract_audio(source_path, audio_path)

            # Transcribe extracted audio
            try:
                result: TranscriptionResult = self._stt_engine.transcribe(audio_path)
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

            # Extract keyframes and create visual observations (if enabled)
            visual_observations = []
            if self.enable_keyframe_extraction:
                visual_observations = self._extract_keyframes(source_path, result.segments)

            # Create pitch segments from transcript
            segments = []
            for i, seg in enumerate(result.segments):
                segments.append(
                    PitchSegment(
                        segment_id=f"seg_{i}",
                        source=SourceModality.VIDEO,
                        start_ref=seg.start_ms,
                        end_ref=seg.end_ms,
                        content=seg.text,
                        speaker_id=seg.speaker_id,
                    )
                )

            # Add visual observation segments
            for i, obs in enumerate(visual_observations):
                segments.append(
                    PitchSegment(
                        segment_id=f"vis_{i}",
                        source=SourceModality.VIDEO,
                        start_ref=obs.timestamp_ms,
                        end_ref=obs.timestamp_ms,
                        content=f"[Visual: {obs.description}]",
                        observation_type=obs.observation_type,
                    )
                )

            return NormalizedPitch(
                source_modality=SourceModality.VIDEO,
                source_metadata=metadata,
                transcript=transcript,
                visual_observations=visual_observations,
                document_content=[],
                segments=segments,
            )

        finally:
            # Cleanup temporary audio file
            if audio_path.exists():
                audio_path.unlink(missing_ok=True)

    def _extract_audio(self, video_path: Path, audio_path: Path) -> None:
        """Extract audio track from video using ffmpeg."""
        cmd = [
            "ffmpeg",
            "-y",  # overwrite
            "-i",
            str(video_path),
            "-vn",  # no video
            "-acodec",
            "pcm_s16le",  # uncompressed wav
            "-ar",
            "16000",  # 16kHz sample rate (Whisper preferred)
            "-ac",
            "1",  # mono
            str(audio_path),
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=self.ffmpeg_timeout_seconds,
            )
        except subprocess.TimeoutExpired as e:
            from pitch_evaluator.extraction.exceptions import MediaProcessingError

            raise MediaProcessingError(
                f"ffmpeg audio extraction timed out after {self.ffmpeg_timeout_seconds}s",
                str(video_path),
            ) from e
        except subprocess.CalledProcessError as e:
            from pitch_evaluator.extraction.exceptions import MediaProcessingError

            raise MediaProcessingError(
                f"ffmpeg audio extraction failed: {e.stderr.decode() if e.stderr else str(e)}",
                str(video_path),
            ) from e
        except FileNotFoundError as e:
            from pitch_evaluator.extraction.exceptions import MediaProcessingError

            raise MediaProcessingError(
                "ffmpeg not found. Please install ffmpeg for video processing.",
                str(video_path),
            ) from e

    def _extract_keyframes(
        self, video_path: Path, transcript_segments: list[TranscriptSegment]
    ) -> list[VisualObservation]:
        """Extract keyframes at intervals and near transcript trigger keywords.

        Returns VisualObservation objects with placeholder descriptions
        (actual VQA would be implemented later).
        """
        observations: list[VisualObservation] = []

        if not transcript_segments:
            return observations

        # Get video duration using ffprobe
        duration = self._get_video_duration(video_path)
        if duration <= 0:
            return observations

        # Extract keyframes at regular intervals
        interval_ms = self.keyframe_interval_seconds * 1000

        for frame_index, timestamp_ms in enumerate(
            range(0, int(duration * 1000), interval_ms), start=1
        ):
            # Check if any transcript segment near this timestamp has trigger keywords
            trigger_keyword = self._find_trigger_keyword(timestamp_ms, transcript_segments)

            # Create observation with placeholder (actual VQA not implemented in MVP)
            # Only create observations for frames with trigger keywords or at intervals
            if trigger_keyword or frame_index % 3 == 1:  # Every 3rd frame + triggers
                observations.append(
                    VisualObservation(
                        timestamp_ms=timestamp_ms,
                        frame_index=frame_index,
                        observation_type=ObservationType.OTHER,
                        description=f"Keyframe at {timestamp_ms / 1000:.1f}s"
                        + (f" (trigger: {trigger_keyword})" if trigger_keyword else ""),
                        confidence=0.0,  # No VQA confidence yet
                        extracted_text=None,
                        bounding_boxes=[],
                        trigger_keyword=trigger_keyword or "interval",
                    )
                )

        return observations

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds using ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]

        try:
            result = subprocess.run(
                cmd, check=True, capture_output=True, timeout=30
            )
            return float(result.stdout.decode().strip())
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
            return 0.0

    def _find_trigger_keyword(self, timestamp_ms: int, transcript_segments: list[TranscriptSegment]) -> str | None:
        """Find if any transcript segment near timestamp contains trigger keywords."""
        window_ms = 5000  # 5 second window

        for seg in transcript_segments:
            seg_start = seg.start_ms
            seg_end = seg.end_ms

            # Check if segment overlaps with timestamp window
            if seg_start <= timestamp_ms + window_ms and seg_end >= timestamp_ms - window_ms:
                text_lower = seg.text.lower()
                for keyword in self.VISUAL_TRIGGER_KEYWORDS:
                    if keyword in text_lower:
                        return keyword

        return None