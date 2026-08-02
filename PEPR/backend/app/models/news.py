from sqlalchemy import Column, String, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class NewsArticle(BaseModel):
    __tablename__ = "news_articles"
    
    source_id = Column(ForeignKey("data_sources.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False)
    published_at = Column(DateTime(timezone=True), index=True)
    content = Column(Text)
    
    source = relationship("DataSource")
    topics = relationship("NewsTopic", back_populates="article")
    sentiment = relationship("SentimentAnalysisResult", back_populates="article", uselist=False)

class NewsTopic(BaseModel):
    __tablename__ = "news_topics"
    
    article_id = Column(ForeignKey("news_articles.id"), nullable=False)
    topic_label = Column(String(200), nullable=False, index=True)
    confidence_score = Column(Float)
    ai_model_version = Column(String(100))
    
    article = relationship("NewsArticle", back_populates="topics")

class SentimentAnalysisResult(BaseModel):
    __tablename__ = "sentiment_analysis_results"
    
    article_id = Column(ForeignKey("news_articles.id"), nullable=False, unique=True)
    score = Column(Float, nullable=False) # -1.0 to 1.0
    label = Column(String(50), nullable=False) # positive, negative, neutral
    ai_model_version = Column(String(100))
    
    article = relationship("NewsArticle", back_populates="sentiment")
