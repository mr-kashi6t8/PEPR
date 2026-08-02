from sqlalchemy import Column, String, ForeignKey, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel

class ResearchDocument(BaseModel):
    __tablename__ = "research_documents"
    
    title = Column(String(500), nullable=False, index=True)
    authors = Column(String(500))
    published_date = Column(DateTime(timezone=True))
    document_type = Column(String(100)) # e.g. "Working Paper", "Policy Brief"
    original_url = Column(String(1000), unique=True)
    document_identifier = Column(String(100), unique=True) # e.g. "PIDE-WP-2023-01"
    
    chunks = relationship("ResearchChunk", back_populates="document")

class ResearchChunk(BaseModel):
    __tablename__ = "research_chunks"
    
    document_id = Column(ForeignKey("research_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer) # Page number where available
    section = Column(String(200)) # Section or heading where available
    content = Column(Text, nullable=False)
    qdrant_point_id = Column(String(100), nullable=False, unique=True) # links to vector db
    
    document = relationship("ResearchDocument", back_populates="chunks")

class ResearchCitation(BaseModel):
    __tablename__ = "research_citations"
    
    chunk_id = Column(ForeignKey("research_chunks.id"), nullable=False)
    context_type = Column(String(50), nullable=False) # report, problem
    context_id = Column(String, nullable=False) # UUID of report or problem
    
    chunk = relationship("ResearchChunk")
