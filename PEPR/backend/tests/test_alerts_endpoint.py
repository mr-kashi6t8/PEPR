import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.api.v1.endpoints.alerts import get_system_alerts

async def main():
    async with AsyncSessionLocal() as db:
        print("=== TESTING REAL SYSTEM ALERTS ENDPOINT ===")
        alerts = await get_system_alerts(db=db)
        print(f"Generated {len(alerts)} real-time system alerts from PostgreSQL!")
        for alt in alerts:
            print(f"[{alt['severity']:<8}] [{alt['category']:<18}] {alt['title']}")

if __name__ == "__main__":
    asyncio.run(main())
