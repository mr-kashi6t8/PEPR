import asyncio
import logging
from sqlalchemy import select, delete
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.models.analysis import DetectedTrend, DetectedAnomaly
from app.services.ingestion.connectors.commodity import CommodityConnector
from app.services.ingestion.connectors.sbp import SBPConnector
from app.services.ingestion.connectors.pbs import PBSConnector
from app.services.ingestion.connectors.psx import PSXConnector
from app.services.ingestion.connectors.fbr import FBRConnector
from app.services.ingestion.connectors.worldbank import WorldBankConnector
from app.services.analysis.post_ingestion import run_post_ingestion_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pepr.refresh_all_m1")

async def refresh_all():
    logger.info("=== REFRESHING ALL M1 DATA SOURCES AND INDICATORS ===")
    async with AsyncSessionLocal() as db:
        # 1. Clean up stale/invalid FBR_TAX_REVENUE observation rows if value > 100 (e.g. 2026.0 year bug)
        ind_fbr = (await db.execute(select(EconomicIndicator).where(EconomicIndicator.code == "FBR_TAX_REVENUE"))).scalars().first()
        if ind_fbr:
            bad_obs_stmt = select(IndicatorObservation.id).where(
                IndicatorObservation.indicator_id == ind_fbr.id,
                IndicatorObservation.value > 100.0
            )
            bad_ids = (await db.execute(bad_obs_stmt)).scalars().all()
            if bad_ids:
                await db.execute(delete(DetectedAnomaly).where(DetectedAnomaly.observation_id.in_(bad_ids)))
                await db.execute(delete(IndicatorObservation).where(IndicatorObservation.id.in_(bad_ids)))
                logger.info(f"Purged {len(bad_ids)} invalid FBR year observations.")
                await db.commit()

        # 2. Run All Ingestion Connectors for M1 Indicators
        connectors = [
            ("Commodity & Energy", CommodityConnector(config={"url": "https://open.er-api.com/v6/latest/USD"}, db=db)),
            ("SBP Interbank & FX", SBPConnector(config={"endpoint": "https://www.sbp.org.pk/"}, db=db)),
            ("PBS Inflation Engine", PBSConnector(config={"url": "https://www.pbs.gov.pk/"}, db=db)),
            ("PSX Market Portal", PSXConnector(config={"endpoint": "https://dps.psx.com.pk/"}, db=db)),
            ("FBR Tax Engine", FBRConnector(config={"url": "https://www.fbr.gov.pk/"}, db=db)),
            ("World Bank Macro Watch", WorldBankConnector(config={}, db=db))
        ]

        for name, conn in connectors:
            logger.info(f"Running connector: {name}...")
            try:
                raw = await conn.fetch()
                norm = conn.normalize(raw)
                if conn.validate(norm):
                    await conn.persist(norm)
                    await db.commit()
                    logger.info(f"Successfully persisted live data for {name}.")
            except Exception as e:
                logger.warning(f"Connector {name} non-fatal warning: {e}")

        # 3. Trigger Post-Ingestion Trend, Anomaly, Policy Gap, and Problem Synthesis Engines
        logger.info("Executing M2-M5 Analysis Engines...")
        await run_post_ingestion_analysis(db, source_type="all_m1")
        logger.info("=== REFRESH ALL M1 COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(refresh_all())
