import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.nlp.gateway import gateway, AIGateway
from app.schemas.ai import ProblemAnalysis
from datetime import datetime, timezone

@pytest.fixture
def mock_gateway():
    return AIGateway()

@pytest.mark.asyncio
async def test_gateway_analyze_problem_success(mock_gateway):
    """Test successful JSON parsing and metadata injection."""
    # Mock the instructor client response
    mock_response = ProblemAnalysis(
        model="mocked-model",
        prompt_version="1.0",
        timestamp=datetime.now(timezone.utc),
        input_evidence_ids=["E1"],
        output_validation_status="PENDING",
        problem_title="High Inflation",
        root_cause_analysis="Supply chain disruption",
        impact_assessment="Decreased purchasing power",
        severity_level="HIGH"
    )
    
    mock_raw_completion = MagicMock()
    mock_raw_completion.usage.prompt_tokens = 100
    mock_raw_completion.usage.completion_tokens = 50
    mock_gateway.instructor_client.chat.completions.create_with_completion = AsyncMock(return_value=(mock_response, mock_raw_completion))
    
    result = await mock_gateway.analyze_problem(
        "Inflation is up 10%", 
        ["E1"], 
        "CPI shows food prices increased."
    )
    
    assert result.problem_title == "High Inflation"
    assert result.model == mock_gateway.primary_model
    assert result.output_validation_status == "VALIDATED"
    assert result.input_evidence_ids == ["E1"]
    
@pytest.mark.asyncio
async def test_gateway_fallback_trigger(mock_gateway):
    """Test that it falls back to the secondary model if primary fails."""
    
    # First call fails, second call succeeds
    mock_response = ProblemAnalysis(
        model="mocked-model",
        prompt_version="1.0",
        timestamp=datetime.now(timezone.utc),
        input_evidence_ids=["E1"],
        output_validation_status="PENDING",
        problem_title="High Inflation",
        root_cause_analysis="Supply chain disruption",
        impact_assessment="Decreased purchasing power",
        severity_level="HIGH"
    )
    
    mock_raw_completion = MagicMock()
    mock_raw_completion.usage.prompt_tokens = 100
    mock_raw_completion.usage.completion_tokens = 50
    mock_gateway.instructor_client.chat.completions.create_with_completion = AsyncMock(side_effect=[Exception("API Timeout"), (mock_response, mock_raw_completion)])
    
    result = await mock_gateway.analyze_problem(
        "Inflation is up 10%", 
        ["E1"], 
        "CPI shows food prices increased."
    )
    
    # Verify it used the fallback model during injection
    assert result.model == mock_gateway.fallback_model
    assert mock_gateway.instructor_client.chat.completions.create_with_completion.call_count == 2
