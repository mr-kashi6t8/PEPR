import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.api.v1.endpoints.indicators import get_indicators_summary

async def test_live_update():
    async with AsyncSessionLocal() as db:
        print("=== 1. QUERYING CURRENT BEFORE VALUE FROM API ===")
        summary_before = await get_indicators_summary(db=db)
        cpi_before = next(i for i in summary_before if i["code"] == "PAK_CPI_YOY")
        print(f"CPI Before Ingestion -> Value: {cpi_before['latest_value']} {cpi_before['unit']} | Shift: {cpi_before['pct_change']}%")

        # 2. Simulate new data row coming into indicator_observations
        ind_stmt = select(EconomicIndicator).where(EconomicIndicator.code == "PAK_CPI_YOY")
        ind_res = await db.execute(ind_stmt)
        cpi_ind = ind_res.scalars().first()

        new_obs = IndicatorObservation(
            id=uuid.uuid4(),
            indicator_id=cpi_ind.id,
            timestamp=datetime.now(timezone.utc),
            value=3.42, # Simulated new CPI reading from PBS
        )
        db.add(new_obs)
        await db.commit()
        print("\n[+] Inserted new observation record into PostgreSQL: timestamp=NOW, value=3.42% YoY")

        # 3. Query API again
        summary_after = await get_indicators_summary(db=db)
        cpi_after = next(i for i in summary_after if i["code"] == "PAK_CPI_YOY")
        print(f"\n=== 2. QUERYING API AFTER NEW DATA INSERTION ===")
        print(f"CPI After Ingestion -> Value: {cpi_after['latest_value']} {cpi_after['unit']} | Shift: {cpi_after['pct_change']}%")

        # Clean up test row
        await db.delete(new_obs)
        await db.commit()
        print("\n[✓] Test row cleaned up.")

if __name__ == "__main__":
    asyncio.run(test_live_update())
