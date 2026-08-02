import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.api.v1.endpoints.ingestion import trigger_ingestion_run

async def main():
    async with AsyncSessionLocal() as db:
        res1 = await trigger_ingestion_run('sbp_daily', db=db)
        print("SBP Trigger Result:", res1)
        res2 = await trigger_ingestion_run('dawn_economy_rss', db=db)
        print("Dawn RSS Trigger Result:", res2)

if __name__ == "__main__":
    asyncio.run(main())
