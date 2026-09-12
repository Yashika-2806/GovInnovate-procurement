"""
CLI Script to manually trigger daily monitoring of active opportunities.
Usage:
    python scripts/run_monitoring.py
"""
import io
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.monitoring_graph import build_monitoring_graph

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("monitoring")


def main():
    logger.info("Triggering Daily Monitoring LangGraph...")
    graph = build_monitoring_graph()
    result = graph.invoke({})

    logger.info("=" * 60)
    logger.info(f"Monitoring Results:")
    logger.info(f"  • Opportunities Checked: {result.get('checked_count', 0)}")
    logger.info(f"  • Opportunities Updated: {result.get('updated_count', 0)}")
    logger.info(f"  • Expired Opportunities: {result.get('expired_count', 0)}")
    for change in result.get("status_changes", []):
        logger.info(f"    - Opp {change['opp_id']}: {change['field']} {change['old_value']} -> {change['new_value']} ({change['reason']})")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
