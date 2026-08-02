import asyncio
from sqlalchemy import select, func
from app.infrastructure.database import AsyncSessionLocal
from app.models.ingestion import DataSource
from app.models.news import NewsArticle
from app.models.economy import IndicatorObservation

async def check():
    async with AsyncSessionLocal() as db:
        print("=== CHECKING REAL DB RECORD COUNTS PER DATA SOURCE ===")
        stmt = select(DataSource)
        res = await db.execute(stmt)
        sources = res.scalars().all()

        for s in sources:
            # Check news_articles count
            news_res = await db.execute(select(func.count(NewsArticle.id)).where(NewsArticle.source_id == s.id))
            news_count = news_res.scalar() or 0

            # Check indicator_observations count (join with indicators)
            obs_count = 0
            if s.source_type in {"sbp", "pbs", "psx", "worldbank", "fbr", "api"}:
                obs_res = await db.execute(select(func.count(IndicatorObservation.id)))
                obs_count = obs_res.scalar() or 0

            print(f"[{s.name:<30}] Source Type: {s.source_type:<10} | News Articles: {news_count} | Total Observations in DB: {obs_count}")

if __name__ == "__main__":
    asyncio.run(check())
