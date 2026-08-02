import asyncio
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import DataSource, DataSourceConfig

YOUTUBE_DS_ID = '190eed8e-14c9-47e4-bd08-7a7aab98eddd'
CHANNEL_IDS = [
    "UCnUYZLuoy1rq1aVMwx4aTzw",
    "UCt3ld6j5HmEQJOQjQvX5GAA",
    "UCWgX_V3u9lG4_u7y84ZzGgQ",
    "UC85E1b-mJp_e8vB1c3e3XgQ",
    "UCJ4L0P3g7_g2XG6vVzE3k-g",
]

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(DataSource).where(DataSource.id == YOUTUBE_DS_ID)
        res = await db.execute(stmt)
        ds = res.scalars().first()
        if not ds:
            print('DataSource not found:', YOUTUBE_DS_ID)
            return

        cfg = DataSourceConfig(source_id=ds.id, credentials={"channel_ids": CHANNEL_IDS}, parsing_rules={})
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)
        print(f'Created DataSourceConfig id={cfg.id} for DataSource id={ds.id} name={ds.name}')

if __name__ == '__main__':
    asyncio.run(main())
