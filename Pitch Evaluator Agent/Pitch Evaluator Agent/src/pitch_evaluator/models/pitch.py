from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator


class SourceModality(str, Enum):
    """Source modality of the pitch content."""

    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class ObservationType(str, Enum):
    """Type of visual observation from video analysis."""

    PROTOTYPE_DEMO = "prototype_demo"
    UI_SCREEN = "ui_screen"
    PHYSICAL_HARDWARE = "physical_hardware"
    SLIDE_CONTENT = "slide_content"
    DEPLOYMENT_EVIDENCE = "deployment_evidence"
    OTHER = "other"


class DocumentSource(str, Enum):
    """Source document type."""

    PDF = "pdf"
    PPT = "ppt"
    PPTX = "pptx"


class BoundingBox(BaseModel):
    """Bounding box for visual elements."""

    x: Annotated[float, Field(ge=0.0)]
    y: Annotated[float, Field(ge=0.0)]
    width: Annotated[float, Field(ge=0.0)]
    height: Annotated[float, Field(ge=0.0)]


class SourceMetadata(BaseModel):
    """Metadata about the source pitch file."""

    filename: str
    mime_type: str
    file_size_bytes: Annotated[int, Field(ge=0)]
    checksum: str
    uploaded_at: datetime
    uploaded_by: str
    duration_seconds: Annotated[float | None, Field(ge=0.0)] = None
    page_count: Annotated[int | None, Field(ge=0)] = None


class TranscriptSegment(BaseModel):
    """A single timestamped, speaker-labeled transcript segment."""

    start_ms: Annotated[int, Field(ge=0)]
    end_ms: Annotated[int, Field(ge=0)]
    speaker_id: str
    text: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]

    @field_validator("end_ms", mode="after")
    @classmethod
    def _validate_end_after_start(cls, v: int, info: Any) -> int:
        if "start_ms" in info.data and v < info.data["start_ms"]:
            raise ValueError("end_ms cannot be before start_ms")
        return v


class Transcript(BaseModel):
    """Full transcript with segments."""

    full_text: str
    segments: Annotated[list[TranscriptSegment], Field(min_length=1)]
    language: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]


class VisualObservation(BaseModel):
    """A visual observation extracted from video frames."""

    timestamp_ms: Annotated[int, Field(ge=0)]
    frame_index: Annotated[int, Field(ge=0)]
    observation_type: ObservationType
    description: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    extracted_text: str | None = None
    bounding_boxes: Annotated[list[BoundingBox], Field(default_factory=list)]
    trigger_keyword: str


class DocumentImage(BaseModel):
    """An image extracted from a document."""

    image_data: str  # base64 encoded or reference
    page_number: Annotated[int, Field(ge=1)]
    position: dict[str, Any]  # flexible position info


class TableCell(BaseModel):
    """A single table cell."""

    value: str
    row: Annotated[int, Field(ge=0)]
    col: Annotated[int, Field(ge=0)]


class Table(BaseModel):
    """A table extracted from a document."""

    cells: list[TableCell]
    page_number: Annotated[int, Field(ge=1)]
    rows: Annotated[int, Field(ge=1)]
    cols: Annotated[int, Field(ge=1)]


class DocumentContent(BaseModel):
    """Content extracted from a document (PDF/PPT/PPTX)."""

    source: DocumentSource
    page_number: Annotated[int, Field(ge=1)]
    slide_number: Annotated[int | None, Field(ge=1)] = None
    text_content: str
    images: Annotated[list[DocumentImage], Field(default_factory=list)]
    tables: Annotated[list[Table], Field(default_factory=list)]


class PitchSegment(BaseModel):
    """Unified segment representation across all modalities."""

    segment_id: str
    source: SourceModality
    start_ref: Annotated[int, Field(ge=0)]  # timestamp_ms or page_number
    end_ref: Annotated[int, Field(ge=0)]
    content: str
    speaker_id: str | None = None
    observation_type: ObservationType | None = None
    slide_number: int | None = None


class NormalizedPitch(BaseModel):
    """Normalized multimodal pitch representation."""

    source_modality: SourceModality
    source_metadata: SourceMetadata
    transcript: Transcript | None = None
    visual_observations: Annotated[list[VisualObservation], Field(default_factory=list)]
    document_content: Annotated[list[DocumentContent], Field(default_factory=list)]
    segments: Annotated[list[PitchSegment], Field(min_length=1)]

    @field_validator("segments", mode="after")
    @classmethod
    def _validate_segments_not_empty(cls, v: list[PitchSegment]) -> list[PitchSegment]:
        if not v:
            raise ValueError("At least one segment is required")
        return v