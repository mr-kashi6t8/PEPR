import instructor
from openai import AsyncOpenAI
import logging
from datetime import datetime, timezone
from typing import List, Any, TypeVar, Type

from app.core.config import settings
from app.schemas.ai import (
    ProblemAnalysis,
    TrendSummary,
    PolicyGapExplanation,
    ResearchRecommendation,
    WeeklyEconomicReport
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

class AIGateway:
    """
    Centralized OpenRouter AI Gateway.
    Uses instructor for strictly validated JSON schema outputs.
    Supports model fallback, tracking, and metadata injection.
    """
    def __init__(self):
        # Create base async OpenAI client pointing to OpenRouter
        self.client = AsyncOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY or "dummy", # Prevent init errors if empty
        )
        # Patch client with instructor for Pydantic support
        # Using MD_JSON mode which is best for OpenRouter / Gemini / Claude fallback compatibility
        self.instructor_client = instructor.from_openai(self.client, mode=instructor.Mode.MD_JSON)
        self.primary_model = settings.OPENROUTER_PRIMARY_MODEL
        self.fallback_model = settings.OPENROUTER_FALLBACK_MODEL
        self.prompt_version = "v1.0.0"

    async def _call_with_fallback(
        self,
        response_model: Type[T],
        messages: List[dict],
        evidence_ids: List[str],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> T:
        """
        Executes a call against the primary model. If it fails (timeout, validation),
        falls back to the secondary model.
        Injects metadata into the final validated model before returning.
        """
        for model in [self.primary_model, self.fallback_model]:
            try:
                logger.info(f"Generating with model {model}. Evidence IDs: {evidence_ids}")
                
                # Log without exposing full sensitive content (message content)
                logger.info(f"Sending request to {model} for evidence IDs: {evidence_ids}")
                
                # Instructor will parse and validate the JSON output automatically
                response, raw_completion = await self.instructor_client.chat.completions.create_with_completion(
                    model=model,
                    response_model=response_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    max_retries=2, # Instructor handles Pydantic validation retries natively
                )
                
                # Inject mandatory metadata post-generation
                response.model = model
                response.model_version = model # Detailed version if supplied by API
                response.prompt_version = self.prompt_version
                response.timestamp = datetime.now(timezone.utc)
                response.input_evidence_ids = evidence_ids
                response.output_validation_status = "VALIDATED"
                
                # Token Tracking
                if raw_completion.usage:
                    response.prompt_tokens = raw_completion.usage.prompt_tokens
                    response.completion_tokens = raw_completion.usage.completion_tokens
                else:
                    response.prompt_tokens = 0
                    response.completion_tokens = 0
                
                response.total_cost = 0.0 # Standard openrouter cost tracking is in headers, which async_openai drops
                
                logger.info(f"Successful generation from {model}. Prompt tokens: {response.prompt_tokens}, Completion tokens: {response.completion_tokens}")
                
                return response
                
            except Exception as e:
                logger.warning(f"Model {model} failed. Error: {str(e)}")
                if model == self.fallback_model:
                    logger.error("All models failed. Throwing exception.")
                    raise RuntimeError(f"AI generation failed across all models: {str(e)}")
                logger.info(f"Falling back to {self.fallback_model}")

    async def analyze_problem(self, problem_description: str, evidence_ids: List[str], evidence_text: str) -> ProblemAnalysis:
        messages = [
            {"role": "system", "content": "You are a senior economist. Analyze the emerging problem based solely on the provided evidence."},
            {"role": "user", "content": f"Problem: {problem_description}\n\nEvidence:\n{evidence_text}"}
        ]
        return await self._call_with_fallback(ProblemAnalysis, messages, evidence_ids)

    async def summarize_trends(self, context: str, evidence_ids: List[str]) -> TrendSummary:
        messages = [
            {"role": "system", "content": "You are a data analyst. Summarize the economic trends using only the provided context."},
            {"role": "user", "content": f"Context:\n{context}"}
        ]
        return await self._call_with_fallback(TrendSummary, messages, evidence_ids)

    async def explain_policy_gap(self, policy_name: str, gap_details: str, evidence_ids: List[str]) -> PolicyGapExplanation:
        messages = [
            {"role": "system", "content": "You are a public policy expert. Explain why the policy target was missed based solely on the evidence."},
            {"role": "user", "content": f"Policy: {policy_name}\nDetails:\n{gap_details}"}
        ]
        return await self._call_with_fallback(PolicyGapExplanation, messages, evidence_ids)

    async def synthesize_research(self, problem_statement: str, evidence_ids: List[str], evidence_text: str) -> ResearchRecommendation:
        messages = [
            {"role": "system", "content": "You are a research synthesis engine. Provide solutions based solely on the provided PIDE working papers."},
            {"role": "user", "content": f"Problem: {problem_statement}\n\nResearch Evidence:\n{evidence_text}"}
        ]
        return await self._call_with_fallback(ResearchRecommendation, messages, evidence_ids)
        
    async def generate_weekly_report(self, consolidated_data: str, evidence_ids: List[str]) -> WeeklyEconomicReport:
        messages = [
            {"role": "system", "content": "You are the chief editor of the Pakistan Economics Problem Radar. Generate the weekly report from the data."},
            {"role": "user", "content": f"Data:\n{consolidated_data}"}
        ]
        return await self._call_with_fallback(WeeklyEconomicReport, messages, evidence_ids, max_tokens=2048)
        
gateway = AIGateway()
