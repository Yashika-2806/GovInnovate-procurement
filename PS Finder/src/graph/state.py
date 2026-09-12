from typing import Any, Dict, List, Optional, TypedDict


class ProblemDiscoveryState(TypedDict, total=False):
    """LangGraph state for the Discovery Graph."""
    query: Optional[str]
    filters: Optional[Dict[str, Any]]
    candidate_urls: List[str]
    candidates: List[Dict[str, Any]]
    fetched_sources: List[Dict[str, Any]]
    verified_sources: List[Dict[str, Any]]
    rejected_candidates: List[Dict[str, Any]]
    extracted_opportunities: List[Dict[str, Any]]
    normalized_opportunities: List[Dict[str, Any]]
    final_opportunities: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[str]
    trace_id: str


class ExplainState(TypedDict, total=False):
    """LangGraph state for the Grounded Explain Graph with Citation Critic (Choice 7A)."""
    opportunity_id: str
    opportunity: Optional[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    draft_explanation: Optional[Dict[str, Any]]
    critic_approved: bool
    critic_notes: Optional[str]
    final_explanation: Optional[Dict[str, Any]]
    error: Optional[str]


class MonitoringState(TypedDict, total=False):
    """LangGraph state for the Daily Monitoring Graph (Section 19)."""
    active_opportunities: List[Dict[str, Any]]
    checked_count: int
    updated_count: int
    expired_count: int
    status_changes: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
