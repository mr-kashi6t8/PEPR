import asyncio
import logging
from sqlalchemy import select, delete
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.services.ingestion.connectors.commodity import CommodityConnector
from app.services.analysis.post_ingestion import run_post_ingestion_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pepr.refresh_live")

async def refresh():
    logger.info("--- STARTING LIVE INDICATOR DATA REFRESH ---")
    async with AsyncSessionLocal() as db:
        # 1. Clean up stale/hardcoded commodity observations
        commodity_codes = [
            "COMM_BRENT_CRUDE",
            "COMM_PETROL_PRICE",
            "COMM_DIESEL_PRICE",
            "COMM_GOLD_RATE_TOLA",
            "PAK_USD_PKR_RATE"
        ]

        logger.info("Purging stale hardcoded commodity observations, anomalies, and trends...")
        from app.models.analysis import DetectedTrend, DetectedAnomaly
        for code in commodity_codes:
            ind_stmt = select(EconomicIndicator).where(EconomicIndicator.code == code)
            ind_res = await db.execute(ind_stmt)
            ind = ind_res.scalars().first()
            if ind:
                # 1. Get observation IDs
                obs_stmt = select(IndicatorObservation.id).where(IndicatorObservation.indicator_id == ind.id)
                obs_ids_res = await db.execute(obs_stmt)
                obs_ids = obs_ids_res.scalars().all()

                if obs_ids:
                    # 2. Delete anomalies referencing these observations
                    await db.execute(delete(DetectedAnomaly).where(DetectedAnomaly.observation_id.in_(obs_ids)))

                # 3. Delete trends referencing this indicator
                await db.execute(delete(DetectedTrend).where(DetectedTrend.indicator_id == ind.id))

                # 4. Delete observations
                await db.execute(delete(IndicatorObservation).where(IndicatorObservation.indicator_id == ind.id))
        await db.commit()

        # 2. Run live CommodityConnector ingestion
        logger.info("Executing CommodityConnector to fetch LIVE market data...")
        conn = CommodityConnector(config={"url": "https://open.er-api.com/v6/latest/USD"}, db=db)
        raw = await conn.fetch()
        logger.info(f"Raw live payload fetched: {raw}")
        norm = conn.normalize(raw)
        logger.info(f"Normalized live data: {norm}")
        if conn.validate(norm):
            await conn.persist(norm)
            await db.commit()
            logger.info("Successfully persisted fresh live commodity observation data!")

        # 3. Run full post-ingestion analysis pipeline
        logger.info("Executing post-ingestion trend, anomaly, policy gap, and problem synthesizer engines...")
        await run_post_ingestion_analysis(db, source_type="commodity")
        logger.info("--- LIVE REFRESH COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(refresh())
