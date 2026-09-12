import uuid
from typing import List, Dict
from datetime import datetime
from ..models.research_data import Citation, SourceType

class CitationTracker:
    def __init__(self):
        self.citations: Dict[str, Citation] = {}
        self.url_to_id: Dict[str, str] = {}

    def add_citation(self, url: str, title: str, source_type: SourceType, snippet: str) -> str:
        if url in self.url_to_id:
            return self.url_to_id[url]
            
        citation_id = str(uuid.uuid4())
        citation = Citation(
            url=url,
            title=title,
            source_type=source_type,
            snippet=snippet,
            accessed_date=datetime.now().isoformat()
        )
        self.citations[citation_id] = citation
        self.url_to_id[url] = citation_id
        return citation_id

    def get_all_citations(self) -> List[Citation]:
        return list(self.citations.values())

    def get_citation(self, citation_id: str) -> Citation:
        return self.citations.get(citation_id)

    def to_bibliography(self) -> str:
        lines = []
        for i, citation in enumerate(self.citations.values(), 1):
            lines.append(f"{i}. [{citation.title}]({citation.url}) - Accessed: {citation.accessed_date}")
        return "\n".join(lines)
