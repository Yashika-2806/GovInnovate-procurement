import logging
import uuid
from typing import Any, Dict, List
from langgraph.graph import StateGraph, END

from src.graph.state import ProblemDiscoveryState
from src.models.opportunity import Opportunity, OpportunityStatus
from src.models.source import VerificationStatus
from src.repositories.database import SessionLocal
from src.repositories.opportunities import OpportunityRepository
from src.repositories.sources import SourceRepository
from src.services.dedup import DeduplicationService
from src.services.document_parser import DocumentParser
from src.services.eligibility import EligibilityClassifier
from src.services.embeddings import VectorStoreService
from src.services.extraction import ExtractionService
from src.services.verification import VerificationService
from src.sources.base import Candidate, RawSource
from src.sources.government.mygov import MyGovAdapter
from src.sources.government.startup_india import StartupIndiaAdapter
from src.sources.registry import SourceRegistry

logger = logging.getLogger(__name__)


def build_discovery_graph():
    """Constructs the LangGraph Problem & Challenge Discovery pipeline."""

    registry = SourceRegistry()
    registry.register_adapter_class("StartupIndiaAdapter", StartupIndiaAdapter)
    registry.register_adapter_class("MyGovAdapter", MyGovAdapter)

    verification_service = VerificationService()
    eligibility_classifier = EligibilityClassifier()
    extraction_service = ExtractionService()
    vector_store = VectorStoreService()

    # --- Nodes ---

    def init_request(state: ProblemDiscoveryState) -> Dict[str, Any]:
        return {
            "trace_id": state.get("trace_id") or str(uuid.uuid4()),
            "errors": [],
            "warnings": [],
            "candidates": [],
            "fetched_sources": [],
            "verified_sources": [],
            "rejected_candidates": [],
            "extracted_opportunities": [],
            "final_opportunities": []
        }

    def discover_candidates(state: ProblemDiscoveryState) -> Dict[str, Any]:
        query = state.get("query")
        filters = state.get("filters", {})
        sources = registry.load_sources()
        all_candidates: List[Dict[str, Any]] = []

        for src_entry in sources:
            adapter = registry.get_adapter(src_entry)
            if not adapter:
                continue
            try:
                candidates = adapter.discover(query=query, filters=filters)
                for c in candidates:
                    all_candidates.append(c.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"Error discovering candidates from {src_entry.name}: {e}")

        return {"candidates": all_candidates}

    def fetch_and_verify(state: ProblemDiscoveryState) -> Dict[str, Any]:
        candidates = state.get("candidates", [])
        verified_sources = []
        rejected = []

        for cand_dict in candidates:
            cand = Candidate(**cand_dict)
            source_entry = next((s for s in registry.load_sources() if s.source_id == cand.source_id), None)
            if not source_entry:
                continue
            adapter = registry.get_adapter(source_entry)
            if not adapter:
                continue

            try:
                raw_source = adapter.fetch(cand)
                auth_evidence = adapter.identify_authority(raw_source)
                status, reason = verification_service.verify_source(raw_source, auth_evidence)

                if status == VerificationStatus.VERIFIED_OFFICIAL:
                    verified_sources.append({
                        "candidate": cand.model_dump(mode="json"),
                        "raw_source": raw_source.model_dump(mode="json"),
                        "verification_status": status.value,
                        "verification_reason": reason
                    })
                else:
                    rejected.append({
                        "candidate": cand.model_dump(mode="json"),
                        "reason": f"Verification failed: {reason}"
                    })
            except Exception as e:
                rejected.append({
                    "candidate": cand.model_dump(mode="json"),
                    "reason": f"Fetch error: {str(e)}"
                })

        return {
            "verified_sources": verified_sources,
            "rejected_candidates": rejected
        }

    def classify_and_extract(state: ProblemDiscoveryState) -> Dict[str, Any]:
        verified_items = state.get("verified_sources", [])
        extracted_opps = []
        rejected = state.get("rejected_candidates", [])

        for item in verified_items:
            cand = Candidate(**item["candidate"])
            raw = RawSource(**item["raw_source"])

            # Eligibility check (reject routine procurement / non-problems)
            elig_status, elig_reason = eligibility_classifier.classify(raw.text_content, cand.title)
            if elig_status == "REJECTED":
                rejected.append({
                    "candidate": cand.model_dump(mode="json"),
                    "reason": f"Ineligible: {elig_reason}"
                })
                continue

            # Extract structured schema
            opp = extraction_service.extract(raw, cand.title, cand.organization_name)
            extracted_opps.append(opp.model_dump(mode="json"))

            # Chunk and index into vector store for RAG Grounded Explain
            chunks = DocumentParser.parse_html(raw.text_content)
            vector_store.index_chunks(opp.id, chunks)

        return {
            "extracted_opportunities": extracted_opps,
            "rejected_candidates": rejected
        }

    def deduplicate_and_persist(state: ProblemDiscoveryState) -> Dict[str, Any]:
        extracted = state.get("extracted_opportunities", [])
        final_opps = []

        db = SessionLocal()
        try:
            repo = OpportunityRepository(db)
            dedup_service = DeduplicationService(repo)
            existing_active = repo.get_active_opportunities()

            for opp_dict in extracted:
                opp = Opportunity(**opp_dict)
                is_exact, dup_id, decision = dedup_service.check_duplicate(opp, existing_active)

                if is_exact:
                    # Update existing record or skip if identical
                    logger.info(f"Duplicate detected: {opp.title} duplicates {dup_id}. Updating record.")
                    saved = repo.save(opp)
                    final_opps.append(saved.model_dump(mode="json"))
                elif decision == "NEEDS_REVIEW":
                    # Choice 9B: mark unverified_duplicate_of pointer and persist
                    opp.unverified_duplicate_of = dup_id
                    saved = repo.save(opp)
                    final_opps.append(saved.model_dump(mode="json"))
                else:
                    saved = repo.save(opp)
                    final_opps.append(saved.model_dump(mode="json"))
                    existing_active.append(saved)
        finally:
            db.close()

        return {"final_opportunities": final_opps}

    # --- Build Graph ---
    graph = StateGraph(ProblemDiscoveryState)

    graph.add_node("init_request", init_request)
    graph.add_node("discover_candidates", discover_candidates)
    graph.add_node("fetch_and_verify", fetch_and_verify)
    graph.add_node("classify_and_extract", classify_and_extract)
    graph.add_node("deduplicate_and_persist", deduplicate_and_persist)

    graph.set_entry_point("init_request")
    graph.add_edge("init_request", "discover_candidates")
    graph.add_edge("discover_candidates", "fetch_and_verify")
    graph.add_edge("fetch_and_verify", "classify_and_extract")
    graph.add_edge("classify_and_extract", "deduplicate_and_persist")
    graph.add_edge("deduplicate_and_persist", END)

    return graph.compile()
