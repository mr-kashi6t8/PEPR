from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from typing import Dict, Any
import time

from app.infrastructure.database import get_db
from app.infrastructure.redis_client import get_redis_client
from app.infrastructure.qdrant_client import get_qdrant_client, check_qdrant_health
from app.models.ingestion import IngestionRun
from app.schemas.health import HealthResponse, SystemHealthResponse
from app.core.config import settings
import redis.asyncio as redis
from qdrant_client import AsyncQdrantClient

router = APIRouter()

START_TIME = time.time()

@router.get("", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", service="pepr-api")

@router.get("/db", response_model=SystemHealthResponse)
async def system_health_dashboard(db: AsyncSession = Depends(get_db)):
    database_status = "ONLINE"
    vector_db_status = "UNKNOWN"
    ai_gateway_status = "AVAILABLE" if settings.OPENROUTER_API_KEY else "NOT CONFIGURED"
    active_jobs = 0

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database_status = "DOWN"

    try:
        res = await check_qdrant_health()
        vector_db_status = "ONLINE"
    except Exception:
        vector_db_status = "DOWN"

    try:
        result = await db.execute(
            select(func.count(IngestionRun.id)).where(IngestionRun.status.ilike("running"))
        )
        active_jobs = int(result.scalar_one() or 0)
    except Exception:
        active_jobs = 0

    if database_status == "DOWN" or vector_db_status == "DOWN":
        overall_status = "CRITICAL"
    elif ai_gateway_status != "AVAILABLE":
        overall_status = "WARNING"
    else:
        overall_status = "HEALTHY"

    return SystemHealthResponse(
        overall_status=overall_status,
        database_status=database_status,
        vector_db_status=vector_db_status,
        ai_gateway_status=ai_gateway_status,
        active_jobs=active_jobs,
        uptime_seconds=int(time.time() - START_TIME),
    )

@router.get("/database", response_model=HealthResponse)
async def database_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return HealthResponse(status="ok", service="postgresql")
    except Exception as e:
        return HealthResponse(status="down", service="postgresql", details={"error": str(e)})

@router.get("/redis", response_model=HealthResponse)
async def redis_health(redis_client: redis.Redis = Depends(get_redis_client)):
    try:
        await redis_client.ping()
        return HealthResponse(status="ok", service="redis")
    except Exception as e:
        return HealthResponse(status="down", service="redis", details={"error": str(e)})

@router.get("/vector-db", response_model=HealthResponse)
async def qdrant_health():
    try:
        res = await check_qdrant_health()
        return HealthResponse(status="ok", service="qdrant", details=res)
    except Exception as e:
        return HealthResponse(status="down", service="qdrant", details={"error": str(e)})
