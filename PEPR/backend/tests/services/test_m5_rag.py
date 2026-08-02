import pytest
import os
from unittest.mock import patch, MagicMock
from app.services.nlp.rag_engine import RAGEngine
from app.models.research import ResearchDocument

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    return session

@pytest.fixture
def mock_qdrant_client():
    with patch('app.infrastructure.qdrant.QdrantConnection.get_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client
        
@pytest.fixture
def mock_embedder():
    with patch('app.services.nlp.rag_engine.embedder.embed_text') as mock:
        mock.return_value = [0.1] * 384
        yield mock

@pytest.mark.asyncio
async def test_document_ingestion_and_chunking(mock_db_session, mock_qdrant_client, mock_embedder):
    """Test PDF text extraction, chunking, embedding and saving to Qdrant."""
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
    
    # We mock PyMuPDF to avoid needing a real PDF
    with patch('app.services.nlp.rag_engine.pymupdf.open') as mock_fitz:
        # Mock a PDF with 2 pages
        mock_pdf = MagicMock()
        mock_fitz.return_value = mock_pdf
        mock_pdf.__len__.return_value = 2
        
        mock_page_1 = MagicMock()
        mock_page_1.get_text.return_value = "Page 1 Content\n\nMore Content"
        
        mock_page_2 = MagicMock()
        mock_page_2.get_text.return_value = "Page 2 Content\n\nParagraph 2"
        
        mock_pdf.__getitem__.side_effect = [mock_page_1, mock_page_2]
        
        doc = await RAGEngine.ingest_pdf(
            file_path="dummy.pdf",
            title="Economic Survey",
            authors="PIDE",
            document_type="Report",
            document_identifier="PIDE-2024",
            original_url="http://pide.org/report",
            db=mock_db_session
        )
        
        assert doc.title == "Economic Survey"
        assert doc.document_identifier == "PIDE-2024"
        
        # Verify it created chunks and uploaded to Qdrant
        assert mock_qdrant_client.upsert.called
        args, kwargs = mock_qdrant_client.upsert.call_args
        
        # Should have 4 points (2 pages * 2 paragraphs)
        points = kwargs['points']
        assert len(points) == 4
        assert points[0].payload['page_number'] == 1
        assert points[2].payload['page_number'] == 2
        assert "Content" in points[0].payload['content']

@pytest.mark.asyncio
async def test_get_recommendations_for_problem(mock_qdrant_client, mock_embedder):
    """Test retrieving citations for an emerging problem."""
    
    # Mock search results
    mock_point_1 = MagicMock()
    mock_point_1.id = "uuid1"
    mock_point_1.score = 0.85
    mock_point_1.payload = {
        "document_identifier": "PIDE-2024",
        "title": "Economic Survey",
        "authors": "PIDE",
        "page_number": 14,
        "content": "Inflation is rising."
    }
    
    # Duplicate page to test deduplication
    mock_point_2 = MagicMock()
    mock_point_2.id = "uuid2"
    mock_point_2.score = 0.82
    mock_point_2.payload = {
        "document_identifier": "PIDE-2024",
        "title": "Economic Survey",
        "authors": "PIDE",
        "page_number": 14, 
        "content": "Food prices are high."
    }
    
    mock_qdrant_client.search.return_value = [mock_point_1, mock_point_2]
    
    with patch('app.services.nlp.rag_engine.gateway.synthesize_research') as mock_llm:
        mock_rec = MagicMock()
        mock_rec.suggested_solution = "Mocked LLM Solution"
        mock_rec.model = "mock-model"
        mock_rec.timestamp = MagicMock()
        mock_rec.timestamp.isoformat.return_value = "2024-01-01T00:00:00Z"
        mock_rec.confidence_score = 0.9
        mock_rec.key_interventions = ["Action 1"]
        mock_rec.output_validation_status = "VALIDATED"
        mock_llm.return_value = mock_rec
        
        result = await RAGEngine.get_recommendations_for_problem("High Inflation")
    
    assert result["problem"] == "High Inflation"
    assert result["relevant_research"] == "Mocked LLM Solution"
    assert result["relevance_score"] == 0.85
    assert len(result["evidence"]) == 2
    
    # Should deduplicate citations from the same page
    assert len(result["citations"]) == 1
    assert result["citations"][0]["document_identifier"] == "PIDE-2024"
    assert result["citations"][0]["page"] == 14

@pytest.mark.asyncio
async def test_ingest_duplicate_document(mock_db_session):
    """Test that ingesting the same document identifier raises an error."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = ResearchDocument(
        id="duplicate-doc",
        title="Duplicate",
        authors="PIDE",
        document_type="Report",
        document_identifier="PIDE-DUP-1",
        original_url=None,
    )
    mock_db_session.execute.return_value = mock_result
    
    with pytest.raises(ValueError, match="already exists"):
        await RAGEngine.ingest_pdf(
            file_path="dummy.pdf",
            title="Duplicate",
            authors="PIDE",
            document_type="Report",
            document_identifier="PIDE-DUP-1",
            original_url=None,
            db=mock_db_session
        )

@pytest.mark.asyncio
async def test_get_recommendations_with_metadata_filter(mock_qdrant_client, mock_embedder):
    """Test retrieving citations with metadata filters."""
    mock_point = MagicMock()
    mock_point.id = "uuid-filtered"
    mock_point.score = 0.90
    mock_point.payload = {
        "document_identifier": "PIDE-FILTER",
        "title": "Filtered Survey",
        "authors": "PIDE",
        "page_number": 1,
        "content": "Filtered content."
    }
    
    mock_qdrant_client.search.return_value = [mock_point]
    
    with patch("app.services.nlp.rag_engine.gateway.synthesize_research") as mock_llm:
        mock_rec = MagicMock()
        mock_rec.suggested_solution = "Filtered Solution"
        mock_rec.model = "mock-model"
        mock_rec.timestamp = MagicMock()
        mock_rec.timestamp.isoformat.return_value = "2024-01-01T00:00:00Z"
        mock_rec.confidence_score = 0.9
        mock_rec.key_interventions = ["Action 1"]
        mock_rec.output_validation_status = "VALIDATED"
        mock_llm.return_value = mock_rec
        
        result = await RAGEngine.get_recommendations_for_problem(
            "High Inflation", 
            filters={"document_type": "Report"}
        )
        
    # Check that search was called with a filter
    args, kwargs = mock_qdrant_client.search.call_args
    assert kwargs.get("query_filter") is not None
    
    assert result["relevant_research"] == "Filtered Solution"
    assert result["citations"][0]["document_identifier"] == "PIDE-FILTER"