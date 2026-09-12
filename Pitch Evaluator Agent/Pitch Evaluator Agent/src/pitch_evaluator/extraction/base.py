from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from pitch_evaluator.models import NormalizedPitch, SourceMetadata, SourceModality


class Extractor(Protocol):
    """Protocol for content extractors."""

    @abstractmethod
    def extract(self, source_path: Path, metadata: SourceMetadata) -> NormalizedPitch:
        """Extract content from source and return NormalizedPitch."""
        ...

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return set of supported file extensions (e.g., {'.txt', '.md'})."""
        ...

    @property
    @abstractmethod
    def modality(self) -> SourceModality:
        """Return the source modality this extractor handles."""
        ...


class BaseExtractor(ABC):
    """Base class for content extractors with common functionality."""

    max_file_size_bytes: int = 500 * 1024 * 1024  # 500 MB default

    @abstractmethod
    def extract(self, source_path: Path, metadata: SourceMetadata) -> NormalizedPitch:
        """Extract content from source and return NormalizedPitch."""
        ...

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return set of supported file extensions."""
        ...

    @property
    @abstractmethod
    def modality(self) -> SourceModality:
        """Return the source modality this extractor handles."""
        ...

    def validate_file(self, source_path: Path) -> None:
        """Validate file exists, is readable, and within size limits."""
        if not source_path.exists():
            raise FileNotFoundError(f"File not found: {source_path}")

        if not source_path.is_file():
            raise ValueError(f"Path is not a file: {source_path}")

        size = source_path.stat().st_size
        if size > self.max_file_size_bytes:
            from pitch_evaluator.extraction.exceptions import FileTooLargeError

            raise FileTooLargeError(size, self.max_file_size_bytes, str(source_path))

        if size == 0:
            from pitch_evaluator.extraction.exceptions import EmptyContentError

            raise EmptyContentError(str(source_path))

        ext = source_path.suffix.lower()
        if ext not in self.supported_extensions:
            from pitch_evaluator.extraction.exceptions import UnsupportedFormatError

            raise UnsupportedFormatError(
                ext, sorted(self.supported_extensions), str(source_path)
            )