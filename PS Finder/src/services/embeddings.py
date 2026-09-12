import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.settings import get_settings
from src.services.document_parser import DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStoreService:
    """Vector storage service for document chunks using ChromaDB."""

    def __init__(self):
        self.persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self._collection = self._client.get_or_create_collection(
                name="source_documents",
                metadata={"hnsw:space": "cosine"}
            )
            return self._collection
        except Exception as e:
            logger.warning(f"Failed to initialize persistent ChromaDB: {e}. Using in-memory fallback.")
            import chromadb
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(name="source_documents")
            return self._collection

    def index_chunks(self, opp_id: str, chunks: List[DocumentChunk]):
        """Index chunks for a specific opportunity ID."""
        if not chunks:
            return

        collection = self._get_collection()
        documents = []
        metadatas = []
        ids = []

        for idx, chunk in enumerate(chunks):
            doc_id = f"{opp_id}_chunk_{idx}"
            documents.append(chunk.text)
            metadatas.append({
                "opp_id": opp_id,
                "page_number": chunk.page_number or 1,
                "section_title": chunk.section_title or "Main"
            })
            ids.append(doc_id)

        try:
            collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        except Exception as e:
            logger.error(f"Error indexing chunks in vector store: {e}")

    def retrieve_relevant(self, opp_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve most relevant chunks for an opportunity."""
        collection = self._get_collection()
        try:
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"opp_id": opp_id}
            )

            retrieved = []
            if results and results.get("documents") and results["documents"][0]:
                for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                    retrieved.append({
                        "text": doc,
                        "page_number": meta.get("page_number", 1),
                        "section_title": meta.get("section_title", "Main")
                    })
            return retrieved
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []
