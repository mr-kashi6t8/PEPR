from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from .base import PEPRBaseSchema

class ResearchDocumentCreate(BaseModel):
    title: str
    authors: Optional[str] = None
    published_date: Optional[datetime] = None
    pdf_url: Optional[str] = None

class ResearchDocumentResponse(PEPRBaseSchema, ResearchDocumentCreate):
    pass

class ResearchChunkCreate(BaseModel):
    document_id: str
    chunk_index: int
    content: str
    qdrant_point_id: str

class ResearchChunkResponse(PEPRBaseSchema, ResearchChunkCreate):
    pass

class ResearchCitationCreate(BaseModel):
    chunk_id: str
    context_type: str
    context_id: str

class ResearchCitationResponse(PEPRBaseSchema, ResearchCitationCreate):
    pass
