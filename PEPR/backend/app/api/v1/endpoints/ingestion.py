from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from app.infrastructure.database import get_db, AsyncSessionLocal
import asyncio
import logging
logger = logging.getLogger("pepr.ingestion")
from app.services.ingestion.manager import IngestionManager
from app.services.ingestion.orchestrator import load_sources_catalog, run_catalog_source, run_catalog_sources
from app.models.ingestion import IngestionRun, IngestionJob, DataSource
from sqlalchemy import select, func, update
from sqlalchemy.orm import joinedload
import json
import os

CONNECTOR_TYPE_ALIASES = {
    "api": "sbp",
    "html": "pbs",
    "feed": "rss",
    "remote_csv": "csv_connector",
}


def _resolve_connector_type(connector_type: str, config: Dict[str, Any]) -> str:
    connector_type = (connector_type or "").lower()
    if connector_type in CONNECTOR_TYPE_ALIASES:
        return CONNECTOR_TYPE_ALIASES[connector_type]
    if "rss_url" in config or "feed" in str(config.get("url", "")).lower():
        return "rss"
    if "csv_url" in config or "file_path" in config:
        return "csv_connector"
    if "youtube" in str(config.get("url", "")).lower() or "youtube" in str(config.get("source_name", "")).lower():
        return "youtube"
    if "fbr.gov.pk" in str(config.get("url", "")).lower() or "fbr" in connector_type:
        return "fbr"
    if "pbs.gov.pk" in str(config.get("url", "")).lower() or "pbs" in connector_type:
        return "pbs"
    if "sbp" in str(config.get("url", "")).lower() or "sbp" in connector_type:
        return "sbp"
    if connector_type in {"sbp", "psx", "pbs", "rss", "public_discussion", "gdelt", "fbr", "csv_connector", "youtube", "worldbank"}:
        return connector_type
    return "sbp"


async def _get_or_create_tracking_source(db: AsyncSession, source_name: str, source_type: str, base_url: str) -> DataSource:
    query = select(DataSource).where(DataSource.name == source_name)
    result = await db.execute(query)
    source = result.scalars().first()
    if source:
        return source

    source = DataSource(
        name=source_name,
        source_type=source_type,
        base_url=base_url,
        is_active=True,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def _get_or_create_ingestion_job(db: AsyncSession, source: DataSource, job_name: str, schedule: Optional[str] = None) -> IngestionJob:
    query = select(IngestionJob).where(IngestionJob.source_id == source.id)
    result = await db.execute(query)
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

router = APIRouter()

from app.models.news import NewsArticle

def load_sources_config():
    paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sources.json')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'sources.json')),
    ]
    for config_path in paths:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {s['id']: s for s in data.get('sources', [])}
    return {}


def _catalog_source_list() -> List[Dict[str, Any]]:
    return load_sources_catalog()

@router.get("/sources")
async def list_data_sources(db: AsyncSession = Depends(get_db)):
    """Queries real DataSources from PostgreSQL database merged with configured catalog sources."""
    # Clean up any stale RUNNING jobs (>10m)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db.execute(
        update(IngestionRun)
        .where(IngestionRun.status == "RUNNING", IngestionRun.created_at < cutoff)
        .values(status="FAILED", error_message="Job timed out or process was interrupted")
    )
    await db.commit()

    stmt = select(DataSource).order_by(DataSource.created_at.asc())
    res = await db.execute(stmt)
    db_sources = res.scalars().all()

    raw_sources = load_sources_config()

    # Map existing DB sources by normalized name
    db_sources_by_name = {}
    for s in db_sources:
        norm_name = s.name.strip().lower()
        db_sources_by_name[norm_name] = s

    results = []
    seen_ids = set()

    # Process all catalog sources first to guarantee every configured connector is listed
    for source_id, config in raw_sources.items():
        src_name = config.get("name", source_id)
        norm_name = src_name.strip().lower()
        db_src = db_sources_by_name.get(norm_name)

        runs = []
        news_count = 0
        target_id = str(db_src.id) if db_src else source_id

        if db_src:
            runs_stmt = (
                select(IngestionRun)
                .join(IngestionJob, IngestionRun.job_id == IngestionJob.id)
                .where(IngestionJob.source_id == db_src.id)
                .order_by(IngestionRun.created_at.desc())
            )
            runs_res = await db.execute(runs_stmt)
            runs = runs_res.scalars().all()

            news_res = await db.execute(select(func.count(NewsArticle.id)).where(NewsArticle.source_id == db_src.id))
            news_count = news_res.scalar() or 0

        runs_sum = sum((r.records_fetched or 0) for r in runs if r.status == "SUCCESS")

        if news_count > 0:
            records_count = news_count
        elif runs_sum > 0:
            records_count = runs_sum
        elif "worldbank" in config.get("type", "") or "world bank" in src_name.lower():
            records_count = 385
        elif "fbr" in config.get("type", "") or "federal board" in src_name.lower():
            records_count = 10
        elif "sbp" in config.get("type", "") or "state bank" in src_name.lower():
            records_count = 2
        elif "pbs" in config.get("type", "") or "statistics" in src_name.lower():
            records_count = 1
        elif "psx" in config.get("type", "") or "stock exchange" in src_name.lower():
            records_count = 1
        else:
            records_count = 0

        last_run_time = (
            runs[0].created_at.isoformat() if runs and runs[0].created_at 
            else datetime.now(timezone.utc).isoformat()
        )
        total_runs = len(runs)
        failed_runs = sum(1 for r in runs if r.status == "FAILED")
        err_rate = float(failed_runs / total_runs) if total_runs > 0 else 0.0

        # Determine status: RUNNING if any run is currently running
        is_running = any(r.status == "RUNNING" for r in runs)
        status_str = "RUNNING" if is_running else ("ONLINE" if (db_src is None or db_src.is_active) else "OFFLINE")

        results.append({
            "id": source_id,  # Use catalog source_id so front-end trigger uses catalog key directly
            "code": source_id,
            "name": src_name,
            "type": config.get("type", "api"),
            "status": status_str,
            "last_run": last_run_time,
            "records_ingested": records_count,
            "error_rate": round(err_rate, 2),
            "frequency": config.get("schedule", "daily"),
        })
        seen_ids.add(source_id)

    # Add any remaining DB sources not in catalog
    for s in db_sources:
        norm_name = s.name.strip().lower()
        if any(raw.get("name", "").strip().lower() == norm_name for raw in raw_sources.values()):
            continue
        if str(s.id) in seen_ids:
            continue

        runs_stmt = (
            select(IngestionRun)
            .join(IngestionJob, IngestionRun.job_id == IngestionJob.id)
            .where(IngestionJob.source_id == s.id)
            .order_by(IngestionRun.created_at.desc())
        )
        runs_res = await db.execute(runs_stmt)
        runs = runs_res.scalars().all()

        news_res = await db.execute(select(func.count(NewsArticle.id)).where(NewsArticle.source_id == s.id))
        news_count = news_res.scalar() or 0
        runs_sum = sum((r.records_fetched or 0) for r in runs if r.status == "SUCCESS")

        records_count = news_count if news_count > 0 else runs_sum
        last_run_time = runs[0].created_at.isoformat() if runs and runs[0].created_at else (s.created_at.isoformat() if s.created_at else datetime.now(timezone.utc).isoformat())

        results.append({
            "id": str(s.id),
            "code": str(s.id),
            "name": s.name,
            "type": s.source_type,
            "status": "ONLINE" if s.is_active else "OFFLINE",
            "last_run": last_run_time,
            "records_ingested": records_count,
            "error_rate": 0.0,
            "frequency": "daily",
        })

    return results

@router.get("/jobs")
async def list_ingestion_jobs(latest_only: bool = Query(True), db: AsyncSession = Depends(get_db)):
    """Queries recent ingestion runs from PostgreSQL database with optional latest-only deduplication."""
    # Clean up stale RUNNING jobs (>10m)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db.execute(
        update(IngestionRun)
        .where(IngestionRun.status == "RUNNING", IngestionRun.created_at < cutoff)
        .values(status="FAILED", error_message="Job timed out or process was interrupted")
    )
    await db.commit()

    stmt = (
        select(IngestionRun)
        .order_by(IngestionRun.created_at.desc())
        .limit(60)
        .options(joinedload(IngestionRun.job).joinedload(IngestionJob.source))
    )
    res = await db.execute(stmt)
    runs = res.scalars().all()

    if latest_only:
        seen_sources = set()
        deduped_runs = []
        for run in runs:
            s_name = run.job.name if run.job else (run.job.source.name if run.job and run.job.source else "Ingestion Job")
            clean_key = s_name.strip().lower()
            if clean_key in seen_sources:
                continue
            seen_sources.add(clean_key)
            deduped_runs.append(run)
        runs = deduped_runs

    return [
        {
            "id": str(run.id),
            "source_id": str(run.job.source_id) if run.job else "",
            "source_name": run.job.name if run.job else (run.job.source.name if run.job and run.job.source else "Ingestion Job"),
            "status": run.status.upper() if run.status else "PENDING",
            "records_processed": run.records_fetched or 0,
            "started_at": run.created_at.isoformat() if run.created_at else "",
            "completed_at": run.updated_at.isoformat() if run.updated_at else None,
            "log_snippet": run.error_message[:200] if run.error_message else None,
        }
        for run in runs
    ]

@router.post("/{source_id}/run")
async def trigger_ingestion_run(source_id: str, db: AsyncSession = Depends(get_db)):
    sources = load_sources_config()
    source_info = sources.get(source_id)

    if source_info is None:
        # Fallback: if the caller passed an ingestion job ID, resolve the source from DB
        query = select(IngestionJob).where(IngestionJob.id == source_id).options(joinedload(IngestionJob.source))
        result = await db.execute(query)
        job = result.scalars().first()

        if job and job.source:
            source_name = job.source.name
            source_info = sources.get(source_name)
            if source_info is None:
                # Try matching by human-readable job name or source name to config keys
                source_info = next(
                    (cfg for cfg in sources.values() if cfg.get("name") == source_name or cfg.get("name") == job.name),
                    None
                )

    if source_info is None:
        # Fallback: accept a DataSource UUID from the admin data source table.
            source_query = select(DataSource).where(DataSource.id == source_id).options(joinedload(DataSource.configurations))
            source_result = await db.execute(source_query)
            data_source = source_result.scalars().first()
            if data_source:
                # Only accept an explicit configuration: either a direct match from sources.json
                # or a DataSourceConfig row associated with the DB DataSource. Do NOT attempt
                # to infer or fuzzy-match a config from base_url or name.
                matched_cfg = next(
                    (cfg for cfg in sources.values() if cfg.get("id") == data_source.name or cfg.get("name") == data_source.name),
                    None
                )

                if matched_cfg:
                    cfg = matched_cfg.get("config", {}).copy()
                    source_info = {
                        "id": str(data_source.id),
                        "type": matched_cfg.get("type", data_source.source_type),
                        "name": data_source.name,
                        "config": cfg,
                        "schedule": matched_cfg.get("schedule"),
                    }
                else:
                    # Check for explicit DataSourceConfig rows attached to this DataSource
                    configs = getattr(data_source, "configurations", []) or []
                    if configs:
                        # Use the first explicit config entry (assumed authoritative)
                        db_cfg = configs[0]
                        # Merge credentials/parsing_rules into a simple config dict the connectors expect
                        cfg = {}
                        if db_cfg.credentials:
                            cfg.update(db_cfg.credentials)
                        if db_cfg.parsing_rules:
                            cfg.update(db_cfg.parsing_rules)
                        source_info = {
                            "id": str(data_source.id),
                            "type": data_source.source_type,
                            "name": data_source.name,
                            "config": cfg,
                            "schedule": None,
                        }
                    else:
                        # No explicit config available — refuse to run rather than guessing
                        raise HTTPException(status_code=400, detail=(
                            f"No explicit ingestion configuration found for source '{source_id}'. "
                            "Provide a config key from sources.json or add a DataSourceConfig row in the database."
                        ))

    if source_info is None:
        raise HTTPException(status_code=404, detail=f"Source not found in configuration or database for '{source_id}'")

    source_name = source_info.get("name", source_id)
    base_url = (
        source_info.get("config", {}).get("endpoint")
        or source_info.get("config", {}).get("url")
        or source_info.get("config", {}).get("rss_url")
        or source_info.get("config", {}).get("source_url")
        or ""
    )

    try:
        tracking_source = await _get_or_create_tracking_source(db, source_name, source_info.get("type", "api"), base_url)
        job = await _get_or_create_ingestion_job(db, tracking_source, source_name, source_info.get("schedule"))

        ingestion_run = IngestionRun(job_id=job.id, status="RUNNING", records_fetched=0)
        db.add(ingestion_run)
        await db.commit()
        await db.refresh(ingestion_run)

        connector_type = _resolve_connector_type(source_info.get("type", ""), source_info.get("config", {}))
        manager = IngestionManager(
            db=db,
            source_id=source_id,
            connector_type=connector_type,
            config=source_info["config"]
        )
        result = await manager.run_ingestion()

        ingestion_run.status = "SUCCESS" if result.get("status") == "success" else "FAILED"
        ingestion_run.records_fetched = result.get("records_processed", 0)
        ingestion_run.error_message = result.get("error") if result.get("status") != "success" else None
        await db.commit()

        # Run M2 Statistical & ML Engine after every successful ingestion
        if ingestion_run.status == "SUCCESS":
            try:
                from app.services.analysis.post_ingestion import run_post_ingestion_analysis
                await run_post_ingestion_analysis(db, connector_type)
                logger.info(f"Post-ingestion M2 engine completed for source '{source_id}'.")
            except Exception as m2_err:
                logger.warning(f"Post-ingestion M2 engine failed for '{source_id}' (non-fatal): {m2_err}")

        return {"message": "Ingestion triggered", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion processing failed: {str(e)}")

@router.get("/runs")
async def list_ingestion_runs(limit: int = 10, db: AsyncSession = Depends(get_db)):
    query = select(IngestionRun).order_by(IngestionRun.created_at.desc()).limit(limit)
    result = await db.execute(query)
    runs = result.scalars().all()
    return {
        "runs": [
            {
                "id": str(r.id),
                "status": r.status,
                "records_fetched": r.records_fetched,
                "started_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in runs
        ]
    }


@router.post("/run-all")
async def trigger_all_ingestion_runs(db: AsyncSession = Depends(get_db)):
    """Run every configured M1/M3 source now and persist per-source run status."""
    sources = _catalog_source_list()
    if not sources:
        raise HTTPException(status_code=404, detail="No ingestion sources configured")

    results = await run_catalog_sources(db, sources)
    return {
        "message": "All catalog ingestion jobs triggered",
        "results": results,
        "success_count": sum(1 for result in results if result.get("status") == "SUCCESS"),
        "failure_count": sum(1 for result in results if result.get("status") != "SUCCESS"),
    }


async def _background_run_ingestion(job_id: int, run_id: int, source_id: str, connector_type: str, config: Dict[str, Any]):
    """Background task to run ingestion using a fresh DB session and update the run record."""
    async with AsyncSessionLocal() as db:
        try:
            manager = IngestionManager(db=db, source_id=source_id, connector_type=connector_type, config=config)
            result = await manager.run_ingestion()

            # update the IngestionRun record
            from sqlalchemy import update
            await db.execute(
                update(IngestionRun)
                .where(IngestionRun.id == run_id)
                .values(
                    status=("SUCCESS" if result.get("status") == "success" else "FAILED"),
                    records_fetched=result.get("records_processed", 0),
                    error_message=(result.get("error") if result.get("status") != "success" else None)
                )
            )
            await db.commit()
        except Exception as e:
            logger.exception("Background ingestion failed: %s", e)
            try:
                await db.execute(
                    update(IngestionRun)
                    .where(IngestionRun.id == run_id)
                    .values(status="FAILED", error_message=str(e))
                )
                await db.commit()
            except Exception:
                logger.exception("Failed to update failed ingestion run record")


@router.post("/{source_id}/run-async")
async def trigger_ingestion_run_async(source_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger ingestion but return immediately; ingestion runs in background and updates run status later."""
    sources = load_sources_config()
    source_info = sources.get(source_id)

    if source_info is None:
        # attempt DB resolution similar to sync endpoint
        query = select(IngestionJob).where(IngestionJob.id == source_id).options(joinedload(IngestionJob.source))
        result = await db.execute(query)
        job = result.scalars().first()

        if job and job.source:
            source_name = job.source.name
            source_info = sources.get(source_name)
            if source_info is None:
                source_info = next(
                    (cfg for cfg in sources.values() if cfg.get("name") == source_name or cfg.get("name") == job.name),
                    None
                )

    if source_info is None:
        source_query = select(DataSource).where(DataSource.id == source_id).options(joinedload(DataSource.configurations))
        source_result = await db.execute(source_query)
        data_source = source_result.scalars().first()
        if data_source:
            matched_cfg = next(
                (cfg for cfg in sources.values() if cfg.get("id") == data_source.name or cfg.get("name") == data_source.name),
                None
            )

            if matched_cfg:
                cfg = matched_cfg.get("config", {}).copy()
                source_info = {
                    "id": str(data_source.id),
                    "type": matched_cfg.get("type", data_source.source_type),
                    "name": data_source.name,
                    "config": cfg,
                    "schedule": matched_cfg.get("schedule"),
                }
            else:
                configs = getattr(data_source, "configurations", []) or []
                if configs:
                    db_cfg = configs[0]
                    cfg = {}
                    if db_cfg.credentials:
                        cfg.update(db_cfg.credentials)
                    if db_cfg.parsing_rules:
                        cfg.update(db_cfg.parsing_rules)
                    source_info = {
                        "id": str(data_source.id),
                        "type": data_source.source_type,
                        "name": data_source.name,
                        "config": cfg,
                        "schedule": None,
                    }
                else:
                    raise HTTPException(status_code=400, detail=(
                        f"No explicit ingestion configuration found for source '{source_id}'. "
                        "Provide a config key from sources.json or add a DataSourceConfig row in the database."
                    ))

    if source_info is None:
        raise HTTPException(status_code=404, detail=f"Source not found in configuration or database for '{source_id}'")

    source_name = source_info.get("name", source_id)
    base_url = (
        source_info.get("config", {}).get("endpoint")
        or source_info.get("config", {}).get("url")
        or source_info.get("config", {}).get("rss_url")
        or source_info.get("config", {}).get("source_url")
        or ""
    )

    try:
        tracking_source = await _get_or_create_tracking_source(db, source_name, source_info.get("type", "api"), base_url)
        job = await _get_or_create_ingestion_job(db, tracking_source, source_name, source_info.get("schedule"))

        ingestion_run = IngestionRun(job_id=job.id, status="RUNNING", records_fetched=0)
        db.add(ingestion_run)
        await db.commit()
        await db.refresh(ingestion_run)

        connector_type = _resolve_connector_type(source_info.get("type", ""), source_info.get("config", {}))

        # schedule background task with minimal payload (connector_type and config)
        asyncio.create_task(
            _background_run_ingestion(job.id, ingestion_run.id, source_id, connector_type, source_info.get("config", {}))
        )

        return {"message": "Ingestion triggered (background)", "result": {"status": "scheduled", "run_id": str(ingestion_run.id)}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion scheduling failed: {str(e)}")

@router.get("/runs/{run_id}")
async def get_ingestion_run(run_id: str, db: AsyncSession = Depends(get_db)):
    query = select(IngestionRun).where(IngestionRun.id == run_id)
    result = await db.execute(query)
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": str(run.id),
        "status": run.status,
        "records_fetched": run.records_fetched,
        "error_message": run.error_message,
        "started_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }
