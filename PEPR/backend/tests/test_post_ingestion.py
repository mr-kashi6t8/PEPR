import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.services.analysis.post_ingestion import run_post_ingestion_analysis
from sqlalchemy import select, func
from app.models.news import NewsTopic, SentimentAnalysisResult

async def test():
    async with AsyncSessionLocal() as db:
        print("=== RUNNING POST-INGESTION NLP ANALYSIS ON ALL ARTICLES/TRANSCRIPTS ===")
        await run_post_ingestion_analysis(db, "youtube")
        await run_post_ingestion_analysis(db, "rss")

        # Verify counts in PostgreSQL
        sent_res = await db.execute(select(func.count(SentimentAnalysisResult.id)))
        sent_count = sent_res.scalar()

        topic_res = await db.execute(select(func.count(NewsTopic.id)))
        topic_count = topic_res.scalar()

        print(f"\nPostgreSQL NLP Sentiment Results: {sent_count}")
        print(f"PostgreSQL NLP Topic Labels     : {topic_count}")

        # Test GET /api/v1/news/trending output
        from app.api.v1.endpoints.news import get_trending_topics
        trending = await get_trending_topics(limit=10, db=db)
        print("\n=== TOP TRENDING MEDIA TOPICS FROM LIVE DATA ===")
        for t in trending.get("trending_topics", []):
            print(f"Topic: {t['topic']:<25} | Volume: {t['volume']} | Avg Sentiment: {t['sentiment_score']:.2f} ({t['sentiment_label']})")

if __name__ == "__main__":
    asyncio.run(test())
