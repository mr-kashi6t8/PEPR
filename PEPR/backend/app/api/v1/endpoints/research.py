import os
import tempfile
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.models.research import ResearchDocument, ResearchChunk
from app.services.nlp.rag_engine import RAGEngine
from pydantic import BaseModel

router = APIRouter()

class RecommendationRequest(BaseModel):
    problem_description: str
    limit: int = 5

@router.get("/")
async def list_research_documents(
    query: Optional[str] = None,
    topic: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all ingested PIDE research documents from PostgreSQL.
    """
    stmt = select(ResearchDocument).order_by(ResearchDocument.created_at.desc())
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    output = []
    for doc in documents:
        # Grab first chunk text as abstract snippet
        chunk_stmt = select(ResearchChunk).where(ResearchChunk.document_id == doc.id).order_by(ResearchChunk.chunk_index.asc()).limit(1)
        chunk_res = await db.execute(chunk_stmt)
        first_chunk = chunk_res.scalars().first()
        abstract_snippet = first_chunk.content if first_chunk else "Indexed research document in PIDE RAG vector database."

        # Deduce topics from title & content
        title_lower = (doc.title + " " + abstract_snippet).lower()
        topics = []
        if "energy" in title_lower or "circular debt" in title_lower:
            topics.append("Energy Policy")
        if "tax" in title_lower or "fbr" in title_lower or "nfc" in title_lower:
            topics.append("Tax Reform")
        if "inflation" in title_lower or "cpi" in title_lower:
            topics.append("Macroeconomics")
        if "soe" in title_lower or "privatization" in title_lower:
            topics.append("Fiscal Policy")
        if "exchange rate" in title_lower or "export" in title_lower:
            topics.append("Exports")
        if not topics:
            topics = ["Economic Policy", "PIDE Research"]

        output.append({
            "id": str(doc.id),
            "title": doc.title,
            "authors": doc.authors,
            "document_type": doc.document_type,
            "document_identifier": doc.document_identifier,
            "published_date": doc.created_at.strftime("%Y") if doc.created_at else "2024",
            "year": doc.created_at.year if doc.created_at else 2024,
            "original_url": doc.original_url or "#",
            "abstract": abstract_snippet[:300] + "..." if len(abstract_snippet) > 300 else abstract_snippet,
            "topics": topics
        })
        
    return output

@router.post("/ingest")
async def ingest_research_document(
    title: str = Form(...),
    authors: str = Form(...),
    document_type: str = Form(...),
    document_identifier: str = Form(...),
    original_url: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests a PDF research document (e.g. from PIDE), chunks it, embeds it,
    and stores it in both Postgres and Qdrant for hybrid retrieval.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files (.pdf) are supported")
        
    # Save uploaded file to temp file
    fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        content = await file.read()
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
            
        doc = await RAGEngine.ingest_pdf(
            file_path=temp_path,
            title=title,
            authors=authors,
            document_type=document_type,
            document_identifier=document_identifier,
            original_url=original_url or f"https://pide.org.pk/research/{document_identifier}.pdf",
            db=db
        )
        
        return {
            "message": "Document ingested successfully",
            "document_id": str(doc.id),
            "document_identifier": doc.document_identifier
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion Error: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/recommendations")
async def get_research_recommendations(req: RecommendationRequest):
    """
    Given an emerging problem, queries the RAG engine to find relevant
    research documents, providing strict evidence and citations.
    """
    try:
        results = await RAGEngine.get_recommendations_for_problem(
            problem_description=req.problem_description,
            limit=req.limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
