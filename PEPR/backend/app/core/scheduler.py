import asyncio
import logging
from typing import Any, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.infrastructure.database import AsyncSessionLocal
from app.services.ingestion.orchestrator import load_sources_catalog, run_catalog_source, run_catalog_sources
from app.services.reports.generator import report_generator

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_scheduled_ingestion(source: Dict[str, Any]) -> None:
    logger.info("Starting scheduled ingestion for %s", source.get("id"))
    async with AsyncSessionLocal() as db:
        result = await run_catalog_source(db, source)
        logger.info("Scheduled ingestion completed for %s: %s", source.get("id"), result)


async def _run_daily_source_sweep() -> None:
    sources = load_sources_catalog()
    logger.info("Starting daily M1/M3 sweep for %s sources", len(sources))

    async with AsyncSessionLocal() as db:
        results = await run_catalog_sources(db, sources)
        for result in results:
            logger.info(
                "Daily sweep source=%s status=%s records=%s",
                result.get("source_id"),
                result.get("status"),
                result.get("records_processed", 0),
            )


def _register_ingestion_jobs() -> None:
    for source in load_sources_catalog():
        source_id = source.get("id")
        schedule = source.get("schedule", "0 0 * * *")
        if not source.get("config", {}).get("enabled", True):
            logger.info("Skipping disabled source %s", source_id)
            continue

        if not source_id or not source.get("type"):
            continue

        try:
            scheduler.add_job(
                _run_scheduled_ingestion,
                trigger=CronTrigger.from_crontab(schedule),
                args=[source],
                id=f"ingest_{source_id}",
                name=f"Ingest {source_id}",
                replace_existing=True,
            )
        except ValueError as exc:
            logger.warning("Skipping ingestion schedule for %s because %s", source_id, exc)


def start_scheduler():
    logger.info("Starting background scheduler...")

    _register_ingestion_jobs()

    # Add weekly report job: Every Monday at 09:00 AM
    scheduler.add_job(
        report_generator.generate_weekly_report,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_economic_report",
        name="Generate Weekly Economic Report",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_daily_source_sweep,
        trigger=CronTrigger(hour=2, minute=15),
        id="daily_m1_m3_sweep",
        name="Run Daily M1/M3 Sweep",
        replace_existing=True,
    )

    scheduler.start()


def stop_scheduler():
    logger.info("Stopping background scheduler...")
    scheduler.shutdown()
