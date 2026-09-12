import logging
import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from langgraph.graph import StateGraph, END

from src.graph.state import MonitoringState
from src.models.opportunity import Opportunity, OpportunityStatus
from src.repositories.database import SessionLocal
from src.repositories.opportunities import OpportunityRepository
from src.services.fetcher import SafeFetcher
from src.sources.html_utils import CLOSURE_MARKERS, visible_text

logger = logging.getLogger(__name__)

# Short per-request timeout: monitoring re-checks many sources and must stay responsive.
_MONITOR_FETCH_TIMEOUT = 20.0


def _to_date(value: Optional[str]) -> Optional[date]:
    """Parse a stored deadline (YYYY-MM-DD or DD/MM/YYYY) into a date, or None."""
    if not value:
        return None
    v = value.strip()
    try:
        return date.fromisoformat(v[:10])
    except ValueError:
        pass
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", v)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


def build_monitoring_graph():
    """Constructs the Daily Monitoring LangGraph that re-checks active opportunities.

    Status semantics (AGENTS.md §28/§29):
      - EXPIRED: the known submission deadline has passed (does not require a live fetch).
      - CLOSED: the live source explicitly states the opportunity is closed.
      - A source-FETCH failure NEVER changes status; it is logged as SOURCE_UNAVAILABLE.
    """

    fetcher = SafeFetcher()

    def load_active(state: MonitoringState) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            repo = OpportunityRepository(db)
            active_opps = repo.get_active_opportunities()
            return {
                "active_opportunities": [o.model_dump(mode="json") for o in active_opps],
                "checked_count": 0,
                "updated_count": 0,
                "expired_count": 0,
                "status_changes": [],
                "errors": [],
            }
        finally:
            db.close()

    def check_and_update_status(state: MonitoringState) -> Dict[str, Any]:
        active_list = state.get("active_opportunities", [])
        status_changes: List[Dict[str, Any]] = []
        updated_count = 0
        expired_count = 0
        errors: List[Dict[str, Any]] = []

        db = SessionLocal()
        try:
            repo = OpportunityRepository(db)
            today = datetime.now(timezone.utc).date()

            for opp_dict in active_list:
                opp = Opportunity(**opp_dict)
                if opp.status != OpportunityStatus.ACTIVE:
                    continue

                new_status: Optional[OpportunityStatus] = None
                reason = ""

                # 1. Deadline-based expiry: uses the known, source-grounded deadline and
                #    is valid independently of whether the live re-fetch succeeds.
                deadline_date = _to_date(opp.deadline)
                if deadline_date and deadline_date < today:
                    new_status = OpportunityStatus.EXPIRED
                    reason = f"Submission deadline {opp.deadline} has passed."

                # 2. Live re-check: can detect an EXPLICIT closure. A fetch failure must
                #    never change status — it is recorded as SOURCE_UNAVAILABLE only.
                if new_status is None:
                    try:
                        raw = fetcher.fetch_sync(opp.source.url, timeout_seconds=_MONITOR_FETCH_TIMEOUT)
                        text_lower = visible_text(raw.raw_html or raw.text_content).lower()
                        if any(marker in text_lower for marker in CLOSURE_MARKERS):
                            new_status = OpportunityStatus.CLOSED
                            reason = "Source explicitly indicates the opportunity is closed."
                    except Exception as e:
                        errors.append({
                            "opp_id": opp.id,
                            "reason": f"SOURCE_UNAVAILABLE: re-fetch failed ({type(e).__name__}); status left unchanged.",
                        })
                        logger.warning("Monitoring re-fetch failed for %s: %s", opp.id, e)

                if new_status is not None:
                    old_status = opp.status.value
                    opp.status = new_status
                    status_changes.append({
                        "opp_id": opp.id,
                        "field": "status",
                        "old_value": old_status,
                        "new_value": new_status.value,
                        "reason": reason,
                    })
                    repo.save(opp)
                    updated_count += 1
                    if new_status == OpportunityStatus.EXPIRED:
                        expired_count += 1

            return {
                "checked_count": len(active_list),
                "updated_count": updated_count,
                "expired_count": expired_count,
                "status_changes": status_changes,
                "errors": errors,
            }
        finally:
            db.close()

    graph = StateGraph(MonitoringState)
    graph.add_node("load_active", load_active)
    graph.add_node("check_and_update_status", check_and_update_status)

    graph.set_entry_point("load_active")
    graph.add_edge("load_active", "check_and_update_status")
    graph.add_edge("check_and_update_status", END)

    return graph.compile()
