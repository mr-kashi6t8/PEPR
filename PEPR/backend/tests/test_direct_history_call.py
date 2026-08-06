import asyncio
import uuid
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.api.v1.endpoints.indicators import get_indicator_history

async def test_direct_call():
    async with AsyncSessionLocal() as db:
        print("=== DIRECT TESTING get_indicator_history ASYNC FUNCTION ===")
        ind_stmt = select(EconomicIndicator).where(EconomicIndicator.code == "SBP_POLICY_RATE")
        ind = (await db.execute(ind_stmt)).scalars().first()

        print(f"Testing Indicator: {ind.name} (ID: {ind.id})")
        res = await get_indicator_history(indicator_id=ind.id, db=db)
        
        print(f"\n[✓] SUCCESS! Returned indicator_id={res['indicator_id']}")
        print(f"[✓] Total Historical Data Points: {len(res['history'])}")
        for pt in res['history'][:5]:
            print(f"      - Date: {pt['date']} | Value: {pt['value']}")

if __name__ == "__main__":
    asyncio.run(test_direct_call())
