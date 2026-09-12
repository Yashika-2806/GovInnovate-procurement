"""
CLI Script to initialize database and run seed discovery from registered Tier 1 official sources.
Usage:
    python scripts/seed_sources.py
"""
import io
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.discovery_graph import build_discovery_graph
from src.repositories.database import SessionLocal, init_db
from src.repositories.sources import SourceRepository
from src.sources.registry import SourceRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


def main():
    logger.info("Initializing database schema...")
    init_db()

    logger.info("Syncing registered official sources...")
    registry = SourceRegistry()
    sources = registry.load_sources()

    db = SessionLocal()
    try:
        source_repo = SourceRepository(db)
        for s in sources:
            source_repo.upsert(s)
            logger.info(f"Registered Tier 1 source: {s.name} ({s.source_id})")
    finally:
        db.close()

    logger.info("Running initial discovery pipeline...")
    discovery_graph = build_discovery_graph()
    result = discovery_graph.invoke({})

    candidates = result.get("candidates", [])
    verified_opps = result.get("final_opportunities", [])

    logger.info("=" * 60)
    logger.info(f"Discovery Summary:")
    logger.info(f"  • Candidates found: {len(candidates)}")
    logger.info(f"  • Verified official opportunities persisted: {len(verified_opps)}")
    for opp in verified_opps:
        logger.info(f"    - [{opp['status']}] {opp['title']} (Org: {opp['organization']['name']}, Deadline: {opp['deadline']})")
    logger.info("=" * 60)
    logger.info("Seed completed successfully!")


if __name__ == "__main__":
    main()
