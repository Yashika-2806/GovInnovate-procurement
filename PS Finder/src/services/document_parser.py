import logging
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DocumentChunk:
    def __init__(self, text: str, page_number: Optional[int] = None, section_title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.text = text
        self.page_number = page_number
        self.section_title = section_title
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "metadata": self.metadata
        }


class DocumentParser:
    """Parses HTML and PDF documents into page-aware and section-aware chunks."""

    @staticmethod
    def parse_html(html_content: str, max_chunk_size: int = 1500) -> List[DocumentChunk]:
        """Extract clean text and structure from HTML, splitting by headings."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts, styles, navigations, footers, headers
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
            tag.decompose()

        chunks: List[DocumentChunk] = []
        current_section = "Main"
        current_buffer = []

        # Walk through block elements
        for elem in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "div"]):
            tag_name = elem.name
            text = elem.get_text(separator=" ", strip=True)
            if not text:
                continue

            if tag_name in ("h1", "h2", "h3", "h4"):
                if current_buffer:
                    combined = "\n".join(current_buffer)
                    if len(combined) > 30:
                        chunks.append(DocumentChunk(text=combined, section_title=current_section))
                    current_buffer = []
                current_section = text[:80]
            else:
                current_buffer.append(text)
                if sum(len(s) for s in current_buffer) >= max_chunk_size:
                    chunks.append(DocumentChunk(text="\n".join(current_buffer), section_title=current_section))
                    current_buffer = []

        if current_buffer:
            combined = "\n".join(current_buffer)
            if len(combined) > 30:
                chunks.append(DocumentChunk(text=combined, section_title=current_section))

        return chunks

    @staticmethod
    def parse_pdf_bytes(pdf_bytes: bytes) -> List[DocumentChunk]:
        """Extract page-aware chunks from PDF using PyMuPDF (fitz)."""
        chunks: List[DocumentChunk] = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()
                if text:
                    chunks.append(DocumentChunk(
                        text=text,
                        page_number=page_num + 1,
                        section_title=f"Page {page_num + 1}"
                    ))
            doc.close()
        except ImportError:
            logger.warning("PyMuPDF (fitz) not available, PDF parsing skipped.")
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")

        return chunks
