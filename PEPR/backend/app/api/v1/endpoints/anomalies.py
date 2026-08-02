from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from app.infrastructure.database import get_db
from app.models.analysis import DetectedAnomaly
from app.models.economy import IndicatorObservation

router = APIRouter()

from datetime import datetime, timezone, timedelta
from fastapi import Query

@router.get("")
@router.get("/")
async def list_anomalies(timeframe: str = Query("latest"), db: AsyncSession = Depends(get_db)):
    """Retrieve detected anomalies from the database with timeframe filtering (latest, weekly, monthly, all)."""
    from app.models.economy import EconomicIndicator, IndicatorObservation
    from app.services.analysis.anomaly_detector import AnomalyDetector
    import uuid

    query = (
        select(DetectedAnomaly, IndicatorObservation, EconomicIndicator)
        .join(IndicatorObservation, DetectedAnomaly.observation_id == IndicatorObservation.id)
        .join(EconomicIndicator, IndicatorObservation.indicator_id == EconomicIndicator.id)
        .order_by(DetectedAnomaly.created_at.desc())
    )

    if timeframe == "weekly":
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        query = query.where(DetectedAnomaly.created_at >= cutoff)
    elif timeframe == "monthly":
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        query = query.where(DetectedAnomaly.created_at >= cutoff)

    result = await db.execute(query)
    rows = result.all()

    if not rows and timeframe not in ["weekly", "monthly"]:
        print("[Anomalies] No anomalies in DB, generating now...")
        indicators = (await db.execute(select(EconomicIndicator))).scalars().all()
        anomaly_count = 0
        
        for ind in indicators:
            obs_stmt = (
                select(IndicatorObservation)
                .where(IndicatorObservation.indicator_id == ind.id)
                .order_by(IndicatorObservation.timestamp.asc())
            )
            obs_list = (await db.execute(obs_stmt)).scalars().all()
            
            if len(obs_list) >= 2:
                obs_dicts = [{"timestamp": o.timestamp, "value": o.value, "id": o.id} for o in obs_list]
                anom_detector = AnomalyDetector(indicator_id=str(ind.id))
                anom_list = anom_detector.analyze(obs_dicts)
                
                # Store all detected anomalies with correct observation IDs
                for a in anom_list:
                    obs_id = a.get("observation_id")
                    if obs_id:  # Use the mapped observation ID
                        anom_obj = DetectedAnomaly(
                            id=uuid.uuid4(),
                            observation_id=obs_id,
                            anomaly_score=float(a["anomaly_score"]),
                            algorithm_used=a["detection_method"],
                        )
                        db.add(anom_obj)
                        anomaly_count += 1
        
        await db.commit()
        print(f"[Anomalies] Created {anomaly_count} anomaly records")

        result = await db.execute(query)
        rows = result.all()

    if timeframe == "latest" and rows:
        latest_ts = max((anomaly.created_at for anomaly, obs, ind in rows if anomaly.created_at), default=None)
        if latest_ts:
            rows = [
                (anomaly, obs, ind)
                for anomaly, obs, ind in rows
                if anomaly.created_at and abs((latest_ts - anomaly.created_at).total_seconds()) <= 14400
            ]

    response = []
    for anomaly, obs, ind in rows:
        response.append({
            "id": str(anomaly.id),
            "indicator_id": str(ind.id),
            "indicator_name": ind.name,
            "indicator_code": ind.code,
            "category": getattr(ind, "category", "Macroeconomic"),
            "observation_id": str(anomaly.observation_id),
            "observation_date": obs.timestamp.isoformat() if obs.timestamp else None,
            "actual_value": obs.value,
            "anomaly_score": anomaly.anomaly_score,
            "algorithm_used": anomaly.algorithm_used,
            "detected_at": anomaly.created_at.isoformat() if anomaly.created_at else None
        })
        
    return {"anomalies": response}
