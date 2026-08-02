from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from .base import PEPRBaseSchema

class NewsArticleCreate(BaseModel):
    source_id: str
    title: str
    url: str
    published_at: Optional[datetime] = None
    content: Optional[str] = None

class NewsArticleResponse(PEPRBaseSchema, NewsArticleCreate):
    pass

class NewsTopicCreate(BaseModel):
    article_id: str
    topic_label: str
    confidence_score: Optional[float] = None
    ai_model_version: Optional[str] = None

class NewsTopicResponse(PEPRBaseSchema, NewsTopicCreate):
    pass

class SentimentAnalysisResultCreate(BaseModel):
    article_id: str
    score: float
    label: str
    ai_model_version: Optional[str] = None

class SentimentAnalysisResultResponse(PEPRBaseSchema, SentimentAnalysisResultCreate):
    pass
