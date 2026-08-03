from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
import uuid

from app.infrastructure.database import get_db
from app.models.analysis import DetectedTrend

router = APIRouter()

@router.options("")
async def options_list_trends():
    return {"allow": ["GET", "OPTIONS"]}

from datetime import datetime, timezone, timedelta
from fastapi import Query

@router.get("")
@router.get("/")
async def list_trends(timeframe: str = Query("latest"), db: AsyncSession = Depends(get_db)):
    """Retrieve detected trends from DB with timeframe filtering (latest, weekly, monthly, all)."""
    from app.models.economy import EconomicIndicator, IndicatorObservation
    from app.services.analysis.trend_detector import TrendDetector

    query = (
        select(DetectedTrend, EconomicIndicator)
        .join(EconomicIndicator, DetectedTrend.indicator_id == EconomicIndicator.id)
        .order_by(DetectedTrend.created_at.desc())
    )

    if timeframe == "weekly":
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        query = query.where(DetectedTrend.created_at >= cutoff)
    elif timeframe == "monthly":
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        query = query.where(DetectedTrend.created_at >= cutoff)

    result = await db.execute(query)
    rows = result.all()

    if not rows and timeframe not in ["weekly", "monthly"]:
        print("[Trends] No trends in DB, generating now...")
        indicators = (await db.execute(select(EconomicIndicator))).scalars().all()
        trend_count = 0
        
        for ind in indicators:
            obs_stmt = (
                select(IndicatorObservation)
                .where(IndicatorObservation.indicator_id == ind.id)
                .order_by(IndicatorObservation.timestamp.asc())
            )
            obs_list = (await db.execute(obs_stmt)).scalars().all()
            
            if len(obs_list) >= 2:
                obs_dicts = [{"timestamp": o.timestamp, "value": o.value, "id": o.id} for o in obs_list]
                td = TrendDetector(indicator_id=str(ind.id))
                res = td.analyze(obs_dicts)
                
                if res:
                    trend_obj = DetectedTrend(
                        id=uuid.uuid4(),
                        indicator_id=ind.id,
                        trend_direction=res["direction"],
                        current_value=res["current_value"],
                        previous_value=res["previous_value"],
                        pct_change=res["percentage_change"],
                        period=res["period"],
                        severity=res["severity"],
                        detection_method=res["detection_method"],
                        confidence_score=res["confidence"],
                    )
                    db.add(trend_obj)
                    trend_count += 1
        
        await db.commit()
        print(f"[Trends] Created {trend_count} trend records")

        result = await db.execute(query)
        rows = result.all()

    if timeframe == "latest" and rows:
        latest_ts = max((t.created_at for t, ind in rows if t.created_at), default=None)
        if latest_ts:
            rows = [
                (t, ind)
                for t, ind in rows
                if t.created_at and abs((latest_ts - t.created_at).total_seconds()) <= 14400
            ]
    
    response = []
    for t, ind in rows:
        curr_val = float(t.current_value or 0.0)
        pct_val = float(t.pct_change or 0.0)
        expected_val = round(curr_val * (1.0 + (pct_val / 100.0) * 0.1), 2) if curr_val != 0 else 0.0
        margin_val = max(abs(curr_val * 0.04), 0.5) if curr_val != 0 else 1.0

        forecast_obj = {
            "expected": expected_val,
            "min_corridor": round(expected_val - margin_val, 2),
            "max_corridor": round(expected_val + margin_val, 2),
        }

        response.append({
            "id": str(t.id),
            "indicator_id": str(t.indicator_id),
            "indicator_name": ind.name,
            "indicator_code": ind.code,
            "category": getattr(ind, "category", "Macroeconomic"),
            "trend_direction": t.trend_direction,
            "current_value": t.current_value,
            "previous_value": t.previous_value,
            "pct_change": t.pct_change,
            "period": t.period,
            "severity": t.severity,
            "detection_method": t.detection_method,
            "confidence_score": t.confidence_score,
            "forecast_30d": forecast_obj,
            "created_at": t.created_at.isoformat() if t.created_at else None
        })
    return {"trends": response}

@router.get("/{trend_id}")
async def get_trend(trend_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific trend by ID."""
    query = select(DetectedTrend).where(DetectedTrend.id == trend_id)
    result = await db.execute(query)
    trend = result.scalars().first()
    
    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")
        
    return {
        "id": str(trend.id),
        "indicator_id": str(trend.indicator_id),
        "trend_direction": trend.trend_direction,
        "current_value": trend.current_value,
        "previous_value": trend.previous_value,
        "pct_change": trend.pct_change,
        "period": trend.period,
        "severity": trend.severity,
        "detection_method": trend.detection_method,
        "confidence_score": trend.confidence_score,
        "supporting_observations": trend.supporting_observations,
        "source_references": trend.source_references
    }
