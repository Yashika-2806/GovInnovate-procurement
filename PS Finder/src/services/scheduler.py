import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config.settings import get_settings
from src.graph.discovery_graph import build_discovery_graph
from src.graph.monitoring_graph import build_monitoring_graph

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = BackgroundScheduler()


def run_scheduled_discovery():
    """Job A: Scheduled periodic discovery of new opportunities."""
    logger.info("Executing scheduled discovery run...")
    try:
        graph = build_discovery_graph()
        result = graph.invoke({})
        logger.info(f"Scheduled discovery completed: {len(result.get('final_opportunities', []))} opportunities saved.")
    except Exception as e:
        logger.error(f"Scheduled discovery failed: {e}")


def run_scheduled_monitoring():
    """Job B: Scheduled periodic monitoring of active opportunities."""
    logger.info("Executing scheduled monitoring re-check...")
    try:
        graph = build_monitoring_graph()
        result = graph.invoke({})
        logger.info(f"Scheduled monitoring completed: {result.get('checked_count', 0)} checked, {result.get('updated_count', 0)} updated.")
    except Exception as e:
        logger.error(f"Scheduled monitoring failed: {e}")


def start_scheduler():
    """Start background scheduler if enabled."""
    if settings.DAILY_DISCOVERY_ENABLED:
        scheduler.add_job(
            run_scheduled_discovery,
            trigger=IntervalTrigger(hours=settings.DISCOVERY_INTERVAL_HOURS),
            id="daily_discovery_job",
            replace_existing=True
        )
        logger.info(f"Daily discovery scheduled every {settings.DISCOVERY_INTERVAL_HOURS} hours.")

    if settings.DAILY_MONITORING_ENABLED:
        scheduler.add_job(
            run_scheduled_monitoring,
            trigger=IntervalTrigger(hours=settings.MONITORING_INTERVAL_HOURS),
            id="daily_monitoring_job",
            replace_existing=True
        )
        logger.info(f"Daily monitoring scheduled every {settings.MONITORING_INTERVAL_HOURS} hours.")

    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
