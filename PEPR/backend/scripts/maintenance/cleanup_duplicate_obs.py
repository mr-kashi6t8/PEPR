import asyncio
from sqlalchemy import select, delete
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.models.analysis import DetectedAnomaly

async def deduplicate():
    async with AsyncSessionLocal() as db:
        print("=== DEDUPLICATING POSTGRESQL OBSERVATION TIMESTAMPS ===")
        # Clear detected_anomalies first to avoid FK constraint
        await db.execute(delete(DetectedAnomaly))
        await db.commit()

        ind_stmt = select(EconomicIndicator)
        indicators = (await db.execute(ind_stmt)).scalars().all()

        deleted_total = 0
        for ind in indicators:
            obs_stmt = (
                select(IndicatorObservation)
                .where(IndicatorObservation.indicator_id == ind.id)
                .order_by(IndicatorObservation.timestamp.asc(), IndicatorObservation.created_at.desc())
            )
            obs_list = (await db.execute(obs_stmt)).scalars().all()

            seen_dates = set()
            for o in obs_list:
                date_key = o.timestamp.strftime("%Y-%m-%d %H:%M") if o.timestamp else ""
                if date_key in seen_dates:
                    await db.delete(o)
                    deleted_total += 1
                else:
                    seen_dates.add(date_key)

        await db.commit()
        print(f"Deleted {deleted_total} duplicate observation records from PostgreSQL!")

        # Re-run ML Anomaly & Trend Engine to generate clean anomalies for valid observations
        from app.services.analysis.post_ingestion import run_post_ingestion_analysis
        await run_post_ingestion_analysis(db=db, source_type="macro")
        print("ML Anomaly Engine re-evaluated on clean time series!")

if __name__ == "__main__":
    asyncio.run(deduplicate())
