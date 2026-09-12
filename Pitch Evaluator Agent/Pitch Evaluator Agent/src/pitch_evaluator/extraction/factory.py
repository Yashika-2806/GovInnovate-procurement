from __future__ import annotations

from pathlib import Path
from typing import Any

from pitch_evaluator.extraction.audio import AudioExtractor
from pitch_evaluator.extraction.base import BaseExtractor
from pitch_evaluator.extraction.documents import DocumentExtractor
from pitch_evaluator.extraction.stt import SpeechToTextEngine
from pitch_evaluator.extraction.text import TextExtractor
from pitch_evaluator.extraction.video import VideoExtractor
from pitch_evaluator.models import NormalizedPitch, SourceMetadata, SourceModality


class ExtractionFactory:
    """Factory for creating and managing content extractors."""

    def __init__(
        self,
        stt_engine: SpeechToTextEngine | str = "mock",
        text_max_size: int = 10 * 1024 * 1024,
        audio_max_size: int = 100 * 1024 * 1024,
        video_max_size: int = 500 * 1024 * 1024,
        document_max_size: int = 50 * 1024 * 1024,
        enable_video_keyframes: bool = True,
        **stt_kwargs: Any,
    ) -> None:
        """Initialize extraction factory with configurable extractors.

        Args:
            stt_engine: STT engine instance or type string
            text_max_size: Max file size for text (default 10 MB)
            audio_max_size: Max file size for audio (default 100 MB)
            video_max_size: Max file size for video (default 500 MB)
            document_max_size: Max file size for documents (default 50 MB)
            enable_video_keyframes: Enable keyframe extraction for video
            **stt_kwargs: Additional STT engine configuration
        """
        self._extractors: dict[str, BaseExtractor] = {
            ".txt": TextExtractor(max_file_size_bytes=text_max_size),
            ".md": TextExtractor(max_file_size_bytes=text_max_size),
            ".markdown": TextExtractor(max_file_size_bytes=text_max_size),
            ".text": TextExtractor(max_file_size_bytes=text_max_size),
            ".mp3": AudioExtractor(stt_engine, max_file_size_bytes=audio_max_size, **stt_kwargs),
            ".wav": AudioExtractor(stt_engine, max_file_size_bytes=audio_max_size, **stt_kwargs),
            ".m4a": AudioExtractor(stt_engine, max_file_size_bytes=audio_max_size, **stt_kwargs),
            ".flac": AudioExtractor(stt_engine, max_file_size_bytes=audio_max_size, **stt_kwargs),
            ".ogg": AudioExtractor(stt_engine, max_file_size_bytes=audio_max_size, **stt_kwargs),
            ".mp4": VideoExtractor(
                stt_engine,
                max_file_size_bytes=video_max_size,
                enable_keyframe_extraction=enable_video_keyframes,
            ),
            ".mov": VideoExtractor(
                stt_engine,
                max_file_size_bytes=video_max_size,
                enable_keyframe_extraction=enable_video_keyframes,
            ),
            ".avi": VideoExtractor(
                stt_engine,
                max_file_size_bytes=video_max_size,
                enable_keyframe_extraction=enable_video_keyframes,
            ),
            ".mkv": VideoExtractor(
                stt_engine,
                max_file_size_bytes=video_max_size,
                enable_keyframe_extraction=enable_video_keyframes,
            ),
            ".webm": VideoExtractor(
                stt_engine,
                max_file_size_bytes=video_max_size,
                enable_keyframe_extraction=enable_video_keyframes,
            ),
            ".m4v": VideoExtractor(
                stt_engine,
                max_file_size_bytes=video_max_size,
                enable_keyframe_extraction=enable_video_keyframes,
            ),
            ".pdf": DocumentExtractor(max_file_size_bytes=document_max_size),
            ".pptx": DocumentExtractor(max_file_size_bytes=document_max_size),
            ".ppt": DocumentExtractor(max_file_size_bytes=document_max_size),
        }

    def get_extractor(self, source_path: Path) -> BaseExtractor:
        """Get appropriate extractor for file extension."""
        ext = source_path.suffix.lower()
        if ext not in self._extractors:
            from pitch_evaluator.extraction.exceptions import UnsupportedFormatError

            supported = sorted(self._extractors.keys())
            raise UnsupportedFormatError(ext, supported, str(source_path))
        return self._extractors[ext]

    def extract(self, source_path: Path, metadata: SourceMetadata) -> NormalizedPitch:
        """Extract content from file using appropriate extractor."""
        extractor = self.get_extractor(source_path)
        return extractor.extract(source_path, metadata)

    def get_supported_extensions(self) -> set[str]:
        """Return all supported file extensions."""
        return set(self._extractors.keys())

    def get_extractor_for_modality(self, modality: SourceModality) -> BaseExtractor | None:
        """Get any extractor that handles the given modality."""
        for extractor in self._extractors.values():
            if extractor.modality == modality:
                return extractor
        return None