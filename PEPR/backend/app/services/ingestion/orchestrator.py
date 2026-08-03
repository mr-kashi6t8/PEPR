import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import DataSource, IngestionJob, IngestionRun
from app.services.ingestion.manager import IngestionManager

logger = logging.getLogger("pepr.ingestion.orchestrator")


def load_sources_catalog() -> List[Dict[str, Any]]:
    config_path = Path(__file__).resolve().parents[3] / "sources.json"
    if not config_path.exists():
        return []

    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("sources", [])


def _source_base_url(source: Dict[str, Any]) -> str:
    config = source.get("config", {})
    return (
        config.get("endpoint")
        or config.get("url")
        or config.get("rss_url")
        or config.get("source_url")
        or ""
    )


async def _get_or_create_tracking_source(db: AsyncSession, source_key: str, source_type: str, base_url: str) -> DataSource:
    result = await db.execute(select(DataSource).where(DataSource.name == source_key))
    source = result.scalars().first()
    if source:
        return source

    source = DataSource(
        name=source_key,
        source_type=source_type,
        base_url=base_url,
        is_active=True,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def _get_or_create_ingestion_job(db: AsyncSession, source: DataSource, job_name: str, schedule: str | None = None) -> IngestionJob:
    result = await db.execute(select(IngestionJob).where(IngestionJob.source_id == source.id))
    job = result.scalars().first()
    if job:
        return job

    job = IngestionJob(
        source_id=source.id,
        name=job_name,
        cron_schedule=schedule,
        is_active=True,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def run_catalog_source(db: AsyncSession, source: Dict[str, Any]) -> Dict[str, Any]:
    source_key = source.get("id")
    source_name = source.get("name", source_key or "unknown-source")
    connector_type = source.get("type", "")
    config = source.get("config", {})

    if not source_key or not connector_type:
        return {
            "source_id": source_key,
            "source_name": source_name,
            "status": "FAILED",
            "error": "Missing source id or connector type",
        }

    tracking_source = await _get_or_create_tracking_source(db, source_key, connector_type, _source_base_url(source))
    job = await _get_or_create_ingestion_job(db, tracking_source, source_name, source.get("schedule"))

    run = IngestionRun(job_id=job.id, status="RUNNING", records_fetched=0)
    db.add(run)
    await db.commit()
    await db.refresh(run)
    run_id = run.id

    try:
        manager = IngestionManager(db=db, source_id=source_key, connector_type=connector_type, config=config)
        result = await manager.run_ingestion()

        # Connector/analyzer work may leave the session in a dirty transactional state even when the
        # underlying writes already committed, so clear it before recording the run status.
        await db.rollback()

        final_status = "SUCCESS" if result.get("status") == "success" else "FAILED"
        await db.execute(
            update(IngestionRun)
            .where(IngestionRun.id == run_id)
            .values(
                status=final_status,
                records_fetched=result.get("records_processed", 0),
                error_message=result.get("error") if final_status != "SUCCESS" else None,
            )
        )
        await db.commit()

        logger.info(
            "Ingestion result source_id=%s source_name=%s status=%s records=%s",
            source_key,
            source_name,
            final_status,
            result.get("records_processed", 0),
        )

        return {
            "source_id": source_key,
            "source_name": source_name,
            "run_id": str(run_id),
            "status": final_status,
            "records_processed": result.get("records_processed", 0),
            "error": result.get("error"),
        }
    except Exception as exc:
        await db.rollback()
        await db.execute(
            update(IngestionRun)
            .where(IngestionRun.id == run_id)
            .values(status="FAILED", error_message=str(exc))
        )
        await db.commit()

        logger.exception("Ingestion failed source_id=%s source_name=%s", source_key, source_name)
        return {
            "source_id": source_key,
            "source_name": source_name,
            "run_id": str(run_id),
            "status": "FAILED",
            "error": str(exc),
        }


async def run_catalog_sources(db: AsyncSession, sources: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    semaphore = asyncio.Semaphore(4)

    async def _process_source(source: Dict[str, Any]) -> Dict[str, Any]:
        if not source.get("config", {}).get("enabled", True):
            return {
                "source_id": source.get("id"),
                "source_name": source.get("name", source.get("id", "unknown-source")),
                "status": "SKIPPED",
                "error": "Source disabled in config",
            }
        async with semaphore:
            async with AsyncSessionLocal() as source_db:
                return await run_catalog_source(source_db, source)

    tasks = [_process_source(src) for src in sources]
    results = list(await asyncio.gather(*tasks))

    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
    failure_count = sum(1 for r in results if r.get("status") == "FAILED")

    logger.info(
        "Catalog sweep finished total=%s success=%s failed=%s",
        len(results),
        success_count,
        failure_count,
    )

    # After all sources complete, run M2 Statistical & ML Engine once with fresh data
    # This ensures trends and anomalies are always evaluated after every ingestion run
    if success_count > 0:
        try:
            from app.services.analysis.post_ingestion import run_post_ingestion_analysis
            async with AsyncSessionLocal() as analysis_db:
                await run_post_ingestion_analysis(analysis_db, "all")
            logger.info("Post-catalog M2 Statistical & ML Engine sweep completed.")
        except Exception as m2_err:
            logger.warning("Post-catalog M2 engine failed (non-fatal): %s", m2_err)

    return results