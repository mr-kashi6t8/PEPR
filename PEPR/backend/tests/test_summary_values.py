import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.api.v1.endpoints.indicators import get_indicators_summary

async def main():
    async with AsyncSessionLocal() as db:
        res = await get_indicators_summary(db)
        print("Summary items count:", len(res))
        for item in res:
            print(f"[{item['code']}] {item['name']}")
            print(f"   Value: {item['latest_value']} {item['unit']} | Prev: {item['previous_value']} | Change: {item['pct_change']}%")

if __name__ == "__main__":
    asyncio.run(main())
