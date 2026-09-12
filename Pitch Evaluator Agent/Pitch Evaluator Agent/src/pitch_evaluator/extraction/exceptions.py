from __future__ import annotations


class ExtractionError(Exception):
    """Base exception for extraction failures."""

    def __init__(self, message: str, source_path: str | None = None) -> None:
        super().__init__(message)
        self.source_path = source_path


class UnsupportedFormatError(ExtractionError):
    """Raised when file format is not supported."""

    def __init__(
        self,
        format: str,
        supported_formats: list[str],
        source_path: str | None = None,
    ) -> None:
        message = f"Unsupported format: {format}. Supported: {supported_formats}"
        super().__init__(message, source_path)
        self.format = format
        self.supported_formats = supported_formats


class FileTooLargeError(ExtractionError):
    """Raised when file exceeds size limit."""

    def __init__(
        self,
        size_bytes: int,
        max_size_bytes: int,
        source_path: str | None = None,
    ) -> None:
        message = f"File too large: {size_bytes} bytes (max: {max_size_bytes})"
        super().__init__(message, source_path)
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes


class EmptyContentError(ExtractionError):
    """Raised when extracted content is empty."""

    def __init__(self, source_path: str | None = None) -> None:
        super().__init__("Extracted content is empty", source_path)


class TranscriptionError(ExtractionError):
    """Raised when speech-to-text fails."""

    def __init__(self, message: str, source_path: str | None = None) -> None:
        super().__init__(f"Transcription failed: {message}", source_path)


class DocumentParsingError(ExtractionError):
    """Raised when document parsing fails."""

    def __init__(self, message: str, source_path: str | None = None) -> None:
        super().__init__(f"Document parsing failed: {message}", source_path)


class MediaProcessingError(ExtractionError):
    """Raised when media processing (ffmpeg, etc.) fails."""

    def __init__(self, message: str, source_path: str | None = None) -> None:
        super().__init__(f"Media processing failed: {message}", source_path)