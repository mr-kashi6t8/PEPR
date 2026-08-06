import asyncio
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation, IndicatorMetadata

async def check():
    async with AsyncSessionLocal() as db:
        print("=== CHECKING POSTGRESQL INDICATORS & OBSERVATIONS ===")
        stmt = select(EconomicIndicator)
        res = await db.execute(stmt)
        indicators = res.scalars().all()

        for ind in indicators:
            obs_stmt = (
                select(IndicatorObservation)
                .where(IndicatorObservation.indicator_id == ind.id)
                .order_by(IndicatorObservation.timestamp.desc())
                .limit(5)
            )
            obs_res = await db.execute(obs_stmt)
            obs = obs_res.scalars().all()

            meta_stmt = select(IndicatorMetadata).where(IndicatorMetadata.indicator_id == ind.id)
            meta_res = await db.execute(meta_stmt)
            meta = meta_res.scalars().first()

            print(f"[{ind.code:<20}] Name: {ind.name:<40} | Observations Count: {len(obs)} | Latest Obs: {[o.value for o in obs]} | Meta Unit: {meta.unit if meta else 'None'} | Freq: {meta.frequency if meta else 'None'}")

if __name__ == "__main__":
    asyncio.run(check())
