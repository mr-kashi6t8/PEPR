import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import DataSource
from sqlalchemy import select

async def list_sources():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(DataSource))
        for s in res.scalars().all():
            print(s.id, s.name, s.source_type, s.base_url)

if __name__ == '__main__':
    asyncio.run(list_sources())
