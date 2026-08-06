import asyncio
from app.api.v1.endpoints.ingestion import _background_run_ingestion
from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import IngestionRun
from sqlalchemy import select

async def main():
    run_id = '14b8881f-682a-4731-b01e-3a1ef7d08afe'
    source_id = '190eed8e-14c9-47e4-bd08-7a7aab98eddd'
    config = {'channel_ids': ['UCnUYZLuoy1rq1aVMwx4aTzw', 'UCt3ld6j5HmEQJOQjQvX5GAA']}
    await _background_run_ingestion(1, run_id, source_id, 'youtube', config)
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(IngestionRun).where(IngestionRun.id == run_id))
        run = res.scalars().first()
        print('status after direct call:', run.status, run.records_fetched, run.error_message)

if __name__ == '__main__':
    asyncio.run(main())
