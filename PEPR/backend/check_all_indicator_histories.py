import asyncio
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.api.v1.endpoints.indicators import get_indicator_history

async def check():
    async with AsyncSessionLocal() as db:
        print("=== AUDITING HISTORY FOR ALL 17 INDICATORS ===")
        indicators = (await db.execute(select(EconomicIndicator))).scalars().all()

        for ind in indicators:
            res = await get_indicator_history(indicator_id=ind.id, db=db)
            history = res.get("history", [])
            print(f"Indicator [{ind.code:<20}] '{ind.name:<40}' -> Total History Points = {len(history)}")
            if len(history) == 0:
                print(f"  ⚠️ WARNING: {ind.name} HAS ZERO HISTORY POINTS IN DB!")

if __name__ == "__main__":
    asyncio.run(check())
