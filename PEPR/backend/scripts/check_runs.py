import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import IngestionRun
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(IngestionRun).order_by(IngestionRun.created_at.desc()).limit(10))
        for run in res.scalars().all():
            print(run.id, run.status, run.records_fetched, run.error_message)

if __name__ == '__main__':
    asyncio.run(main())
