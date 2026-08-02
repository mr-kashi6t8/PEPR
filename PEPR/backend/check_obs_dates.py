import asyncio
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation

async def check():
    async with AsyncSessionLocal() as db:
        print("=== CHECKING OBSERVATION TIMESTAMPS IN POSTGRESQL ===")
        stmt = select(EconomicIndicator)
        res = await db.execute(stmt)
        indicators = res.scalars().all()

        for ind in indicators[:5]:
            obs_stmt = (
                select(IndicatorObservation)
                .where(IndicatorObservation.indicator_id == ind.id)
                .order_by(IndicatorObservation.timestamp.asc())
                .limit(10)
            )
            obs_res = await db.execute(obs_stmt)
            observations = obs_res.scalars().all()
            print(f"\nIndicator: {ind.name} [{ind.code}]")
            for o in observations:
                print(f"  • Timestamp: {o.timestamp} | Value: {o.value}")

if __name__ == "__main__":
    asyncio.run(check())
