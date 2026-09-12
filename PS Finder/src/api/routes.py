import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.schemas import (
    DiscoveryRunResponse, ExplainResponse, MonitoringRunResponse,
    OpportunityListResponse, SearchRequest
)
from src.graph.discovery_graph import build_discovery_graph
from src.graph.explain_graph import build_explain_graph
from src.graph.monitoring_graph import build_monitoring_graph
from src.models.opportunity import Opportunity
from src.models.source import SourceInfo
from src.models.version import OpportunityVersion
from src.repositories.database import get_db
from src.repositories.opportunities import OpportunityRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["opportunities"])


@router.get("/opportunities", response_model=OpportunityListResponse)
def list_opportunities(
    q: Optional[str] = Query(None, description="Free text search on title, problem statement, or org"),
    organization_type: Optional[str] = Query(None, description="Filter: government or private"),
    organization_level: Optional[str] = Query(None, description="Filter: national, state, municipal, psu"),
    domain: Optional[str] = Query(None, description="Filter: smart_cities, healthcare, cybersecurity, etc."),
    country: Optional[str] = Query(None, description="Filter: India, etc."),
    opportunity_type: Optional[str] = Query(None, description="Filter: innovation_challenge, rfp, eoi"),
    status: Optional[str] = Query(None, description="Filter: ACTIVE, CLOSED, EXPIRED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search and list verified opportunities with multi-dimensional filtering."""
    repo = OpportunityRepository(db)
    items, total = repo.search(
        query=q,
        organization_type=organization_type,
        organization_level=organization_level,
        domain=domain,
        country=country,
        opportunity_type=opportunity_type,
        status=status,
        page=page,
        page_size=page_size
    )
    return OpportunityListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/opportunities/{opp_id}", response_model=Opportunity)
def get_opportunity_details(opp_id: str, db: Session = Depends(get_db)):
    """Fetch complete verified opportunity record and provenance."""
    repo = OpportunityRepository(db)
    opp = repo.get_by_id(opp_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Verified opportunity not found.")
    return opp


@router.post("/opportunities/search", response_model=OpportunityListResponse)
def agentic_search(req: SearchRequest, db: Session = Depends(get_db)):
    """Agent-driven search query endpoint for downstream multi-agent platform."""
    repo = OpportunityRepository(db)
    items, total = repo.search(
        query=req.query,
        organization_type=req.organization_type,
        domain=req.domain,
        country=req.country,
        status=req.status,
        page=req.page,
        page_size=req.page_size
    )
    return OpportunityListResponse(
        total=total,
        page=req.page,
        page_size=req.page_size,
        items=items
    )


@router.get("/opportunities/search", response_model=OpportunityListResponse)
def agentic_search_get(
    q: Optional[str] = Query(None, description="Search query"),
    organization_type: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """GET search endpoint for simple client and browser queries."""
    repo = OpportunityRepository(db)
    items, total = repo.search(
        query=q,
        organization_type=organization_type,
        domain=domain,
        country=country,
        status=status,
        page=page,
        page_size=page_size
    )
    return OpportunityListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.post("/opportunities/{opp_id}/explain", response_model=ExplainResponse)
@router.get("/opportunities/{opp_id}/explain", response_model=ExplainResponse)
def explain_opportunity(opp_id: str, db: Session = Depends(get_db)):
    """Execute the Explain Graph to generate a source-grounded explanation with citation criticism."""
    repo = OpportunityRepository(db)
    opp = repo.get_by_id(opp_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    explain_graph = build_explain_graph()
    result = explain_graph.invoke({"opportunity_id": opp_id})

    final_expl = result.get("final_explanation") or result.get("draft_explanation")
    if not final_expl:
        raise HTTPException(status_code=500, detail="Failed to generate grounded explanation.")

    return ExplainResponse(
        opportunity_id=opp_id,
        problem=final_expl.get("problem", opp.problem_statement),
        why_it_matters=final_expl.get("why_it_matters", "Not specified in the source."),
        who_is_affected=final_expl.get("who_is_affected", "Not specified in the source."),
        what_org_wants=final_expl.get("what_org_wants", "Not specified in the source."),
        key_requirements=final_expl.get("key_requirements", opp.requirements or ["Not specified in the source."]),
        constraints=final_expl.get("constraints", opp.constraints or ["Not specified in the source."]),
        funding_prize=final_expl.get("funding_prize", "Not specified in the source."),
        support=final_expl.get("support", opp.support or "Not specified in the source."),
        deadline=final_expl.get("deadline", opp.deadline or "Not specified in the source."),
        eligibility=final_expl.get("eligibility", opp.eligibility or ["Not specified in the source."]),
        expected_outcome=final_expl.get("expected_outcome", opp.expected_outcome or "Not specified in the source."),
        source_citation=final_expl.get("source_citation", f"Verified against {opp.source.url}"),
        critic_approved=result.get("critic_approved", True)
    )


@router.get("/opportunities/{opp_id}/source", response_model=SourceInfo)
def get_opportunity_source(opp_id: str, db: Session = Depends(get_db)):
    """Fetch authoritative original source information."""
    repo = OpportunityRepository(db)
    opp = repo.get_by_id(opp_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    return opp.source


@router.get("/opportunities/{opp_id}/history", response_model=List[OpportunityVersion])
def get_opportunity_history(opp_id: str, db: Session = Depends(get_db)):
    """Fetch complete version diff history for an opportunity."""
    repo = OpportunityRepository(db)
    versions = repo.get_versions(opp_id)
    return versions


@router.post("/discovery/run", response_model=DiscoveryRunResponse)
def trigger_discovery(query: Optional[str] = None):
    """Trigger the LangGraph Discovery Graph to discover, verify, and persist opportunities."""
    discovery_graph = build_discovery_graph()
    result = discovery_graph.invoke({"query": query})

    final_opps_data = result.get("final_opportunities", [])
    final_opps = [Opportunity(**o) for o in final_opps_data]

    return DiscoveryRunResponse(
        trace_id=result.get("trace_id", ""),
        candidates_discovered=len(result.get("candidates", [])),
        verified_opportunities_saved=len(final_opps),
        opportunities=final_opps
    )


@router.post("/monitoring/run", response_model=MonitoringRunResponse)
def trigger_monitoring():
    """Trigger the LangGraph Monitoring Graph to check active opportunities and update status/versions."""
    monitoring_graph = build_monitoring_graph()
    result = monitoring_graph.invoke({})

    return MonitoringRunResponse(
        checked_count=result.get("checked_count", 0),
        updated_count=result.get("updated_count", 0),
        expired_count=result.get("expired_count", 0),
        status_changes=result.get("status_changes", [])
    )
