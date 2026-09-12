from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pitch_evaluator.extraction.base import BaseExtractor
from pitch_evaluator.models import (
    DocumentContent,
    DocumentImage,
    DocumentSource,
    NormalizedPitch,
    PitchSegment,
    SourceMetadata,
    SourceModality,
    Table,
    TableCell,
)


class DocumentExtractor(BaseExtractor):
    """Extract content from PDF, PPT, and PPTX documents."""

    supported_extensions: ClassVar[set[str]] = {".pdf", ".ppt", ".pptx"}
    modality: ClassVar[SourceModality] = SourceModality.DOCUMENT

    def __init__(self, max_file_size_bytes: int = 50 * 1024 * 1024) -> None:
        """Initialize with configurable max file size (default 50 MB for documents)."""
        self.max_file_size_bytes = max_file_size_bytes

    def extract(self, source_path: Path, metadata: SourceMetadata) -> NormalizedPitch:
        """Extract document content and create NormalizedPitch."""
        self.validate_file(source_path)

        ext = source_path.suffix.lower()

        if ext == ".pdf":
            doc_content = self._extract_pdf(source_path)
        elif ext == ".pptx":
            doc_content = self._extract_pptx(source_path)
        elif ext == ".ppt":
            doc_content = self._extract_ppt(source_path)
        else:
            from pitch_evaluator.extraction.exceptions import UnsupportedFormatError

            raise UnsupportedFormatError(
                ext, sorted(self.supported_extensions), str(source_path)
            )

        if not doc_content:
            from pitch_evaluator.extraction.exceptions import EmptyContentError

            raise EmptyContentError(str(source_path))

        # Create pitch segments from document content
        segments = []
        for i, page in enumerate(doc_content):
            if page.text_content.strip():
                segments.append(
                    PitchSegment(
                        segment_id=f"doc_{i}",
                        source=SourceModality.DOCUMENT,
                        start_ref=page.page_number,
                        end_ref=page.page_number,
                        content=page.text_content,
                        slide_number=page.slide_number,
                    )
                )

            # Add table segments
            for j, table in enumerate(page.tables):
                table_text = self._table_to_text(table)
                if table_text:
                    segments.append(
                        PitchSegment(
                            segment_id=f"doc_{i}_table_{j}",
                            source=SourceModality.DOCUMENT,
                            start_ref=page.page_number,
                            end_ref=page.page_number,
                            content=f"[Table] {table_text}",
                            slide_number=page.slide_number,
                        )
                    )

        return NormalizedPitch(
            source_modality=SourceModality.DOCUMENT,
            source_metadata=metadata,
            transcript=None,
            visual_observations=[],
            document_content=doc_content,
            segments=segments,
        )

    def _extract_pdf(self, pdf_path: Path) -> list[DocumentContent]:
        """Extract text, images, and tables from PDF using pdfplumber."""
        try:
            import pdfplumber
        except ImportError as e:
            from pitch_evaluator.extraction.exceptions import DocumentParsingError

            raise DocumentParsingError(
                "pdfplumber not installed. Install with: pip install pdfplumber",
                str(pdf_path),
            ) from e

        content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""

                # Extract tables
                tables = []
                for table_idx, table in enumerate(page.extract_tables() or []):
                    cells = []
                    for row_idx, row in enumerate(table):
                        for col_idx, cell in enumerate(row):
                            if cell is not None:
                                cells.append(
                                    TableCell(
                                        value=str(cell),
                                        row=row_idx,
                                        col=col_idx,
                                    )
                                )
                    if cells:
                        tables.append(
                            Table(
                                cells=cells,
                                page_number=page_num,
                                rows=max(c.row for c in cells) + 1,
                                cols=max(c.col for c in cells) + 1,
                            )
                        )

                # Extract images (basic metadata only, not binary data)
                images = []
                for img_idx, img in enumerate(page.images or []):
                    images.append(
                        DocumentImage(
                            image_data=f"pdf_image_p{page_num}_i{img_idx}",
                            page_number=page_num,
                            position={"x": img.get("x0", 0), "y": img.get("y0", 0)},
                        )
                    )

                content.append(
                    DocumentContent(
                        source=DocumentSource.PDF,
                        page_number=page_num,
                        slide_number=None,
                        text_content=text,
                        images=images,
                        tables=tables,
                    )
                )

        return content

    def _extract_pptx(self, pptx_path: Path) -> list[DocumentContent]:
        """Extract content from PPTX using python-pptx."""
        try:
            from pptx import Presentation
        except ImportError as e:
            from pitch_evaluator.extraction.exceptions import DocumentParsingError

            raise DocumentParsingError(
                "python-pptx not installed. Install with: pip install python-pptx",
                str(pptx_path),
            ) from e

        content = []
        prs = Presentation(str(pptx_path))

        for slide_num, slide in enumerate(prs.slides, start=1):
            text_parts = []
            tables = []
            images = []

            for shape in slide.shapes:
                # Text from text frames
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = para.text.strip()
                        if text:
                            text_parts.append(text)

                # Tables
                if shape.has_table:
                    table = shape.table
                    cells = []
                    for row_idx, row in enumerate(table.rows):
                        for col_idx, cell in enumerate(row.cells):
                            text = cell.text.strip()
                            if text:
                                cells.append(
                                    TableCell(value=text, row=row_idx, col=col_idx)
                                )
                    if cells:
                        tables.append(
                            Table(
                                cells=cells,
                                page_number=slide_num,
                                rows=len(table.rows),
                                cols=len(table.columns),
                            )
                        )

                # Images
                if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
                    images.append(
                        DocumentImage(
                            image_data=f"pptx_image_s{slide_num}",
                            page_number=slide_num,
                            position={},
                        )
                    )

                # Group shapes - recurse
                if shape.shape_type == 6:  # MSO_SHAPE_TYPE.GROUP
                    for sub_shape in shape.shapes:
                        if sub_shape.has_text_frame:
                            for para in sub_shape.text_frame.paragraphs:
                                text = para.text.strip()
                                if text:
                                    text_parts.append(text)

            content.append(
                DocumentContent(
                    source=DocumentSource.PPTX,
                    page_number=slide_num,
                    slide_number=slide_num,
                    text_content="\n".join(text_parts),
                    images=images,
                    tables=tables,
                )
            )

        return content

    def _extract_ppt(self, ppt_path: Path) -> list[DocumentContent]:
        """Extract content from legacy PPT format.

        Note: python-pptx does not support .ppt (legacy binary format).
        This requires external tools like libreoffice or antiword.
        """
        from pitch_evaluator.extraction.exceptions import DocumentParsingError

        raise DocumentParsingError(
            "Legacy .ppt format not directly supported. "
            "Convert to .pptx using LibreOffice: libreoffice --headless --convert-to pptx file.ppt",
            str(ppt_path),
        )

    def _table_to_text(self, table: Table) -> str:
        """Convert table to text representation."""
        if not table.cells:
            return ""

        # Build row-wise representation
        rows: dict[int, dict[int, str]] = {}
        for cell in table.cells:
            if cell.row not in rows:
                rows[cell.row] = {}
            rows[cell.row][cell.col] = cell.value

        lines = []
        for row_idx in sorted(rows.keys()):
            row_data = rows[row_idx]
            cols = sorted(row_data.keys())
            line = " | ".join(row_data[col] for col in cols)
            lines.append(line)

        return "\n".join(lines)