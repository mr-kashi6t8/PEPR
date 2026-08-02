from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Dict, Any, List, Optional

from app.infrastructure.database import get_db
from app.models.news import NewsTopic, SentimentAnalysisResult, NewsArticle

router = APIRouter()

@router.get("/trending")
async def get_trending_topics(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    """
    Returns the top trending topics extracted from news/media, 
    along with their average sentiment score (M3 Requirement).
    """
    
    # We want to group by topic_label, count the frequency (volume),
    # and calculate the average sentiment score for that topic.
    query = (
        select(
            NewsTopic.topic_label,
            func.count(NewsTopic.id).label("volume"),
            func.avg(SentimentAnalysisResult.score).label("avg_sentiment")
        )
        .join(NewsArticle, NewsTopic.article_id == NewsArticle.id)
        .join(SentimentAnalysisResult, NewsArticle.id == SentimentAnalysisResult.article_id)
        .group_by(NewsTopic.topic_label)
        .order_by(desc("volume"))
        .limit(limit)
    )
    
    result = await db.execute(query)
    
    trending = []
    for row in result:
        topic_label, volume, avg_sentiment = row
        trending.append({
            "topic": topic_label,
            "volume": volume,
            "sentiment_score": float(avg_sentiment) if avg_sentiment is not None else 0.0,
            "sentiment_label": "positive" if avg_sentiment and avg_sentiment > 0.2 else ("negative" if avg_sentiment and avg_sentiment < -0.2 else "neutral")
        })
        
    return {"trending_topics": trending}

@router.get("/articles")
@router.get("/")
@router.get("")
async def get_articles(limit: Optional[int] = Query(None), db: AsyncSession = Depends(get_db)):
    """Fetch all processed news articles and YouTube talkshow transcripts date-wise."""
    query = select(NewsArticle).order_by(NewsArticle.published_at.desc())
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()
    
    response = []
    for a in articles:
        response.append({
            "id": str(a.id),
            "title": a.title,
            "url": a.url,
            "content": a.content[:300] if a.content else "",
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "source_id": str(a.source_id) if a.source_id else None,
        })
    return {"articles": response}
