import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.api.v1.endpoints.indicators import get_indicators_summary

async def test():
    async with AsyncSessionLocal() as db:
        print("=== TESTING CLEANED INDICATORS DIRECTORY SUMMARY ===")
        indicators = await get_indicators_summary(db=db)
        for ind in indicators:
            print(f"[{ind['code']:<22}] Value: {ind['latest_value']:<12} {ind['unit']:<15} | % Change: {ind['pct_change']:>+6.1f}% | Source: {ind['source']:<18} | Freq: {ind['frequency']}")

if __name__ == "__main__":
    asyncio.run(test())
