import asyncio
from sqlalchemy import select, func
from app.infrastructure.database import AsyncSessionLocal
from app.models import DataSource, EconomicIndicator, IndicatorObservation, NewsArticle, ResearchDocument

async def main():
    async with AsyncSessionLocal() as db:
        ds_cnt = (await db.execute(select(func.count(DataSource.id)))).scalar()
        ind_cnt = (await db.execute(select(func.count(EconomicIndicator.id)))).scalar()
        obs_cnt = (await db.execute(select(func.count(IndicatorObservation.id)))).scalar()
        news_cnt = (await db.execute(select(func.count(NewsArticle.id)))).scalar()
        pide_cnt = (await db.execute(select(func.count(ResearchDocument.id)))).scalar()
        
        print("\n=========================================================================")
        print("          PEPR LIVE DATA INGESTION & PIPELINE STATUS REPORT             ")
        print("=========================================================================")
        print(f"  • Registered Data Sources    : {ds_cnt}")
        print(f"  • Active Economic Indicators  : {ind_cnt}")
        print(f"  • Live Time-Series Data Points: {obs_cnt}")
        print(f"  • News & YouTube Transcripts  : {news_cnt}")
        print(f"  • PIDE Research Showcase Papers: {pide_cnt}")
        print("=========================================================================\n")

if __name__ == "__main__":
    asyncio.run(main())
