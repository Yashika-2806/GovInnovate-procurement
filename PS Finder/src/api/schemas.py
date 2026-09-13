from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.models.opportunity import Opportunity
from src.models.version import OpportunityVersion


class OpportunityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Opportunity]


class SearchRequest(BaseModel):
    query: Optional[str] = None
    organization_type: Optional[str] = None
    domain: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    page: int = 1
    page_size: int = 20


class ExplainResponse(BaseModel):
    opportunity_id: str
    problem: str
    why_it_matters: str
    who_is_affected: str | List[str]
    what_org_wants: str
    key_requirements: List[str]
    constraints: List[str]
    funding_prize: str
    support: str
    deadline: str
    eligibility: List[str]
    expected_outcome: str
    source_citation: str
    critic_approved: bool = True


class DiscoveryRunResponse(BaseModel):
    trace_id: str
    candidates_discovered: int
    verified_opportunities_saved: int
    opportunities: List[Opportunity]


class MonitoringRunResponse(BaseModel):
    checked_count: int
    updated_count: int
    expired_count: int
    status_changes: List[Dict[str, Any]]
