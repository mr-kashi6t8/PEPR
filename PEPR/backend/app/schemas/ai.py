from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class BaseAIPayload(BaseModel):
    """Base fields that must be present in every AI gateway response."""
    model: str = Field(description="The model name that generated this response (e.g. google/gemini-2.5-flash).")
    model_version: Optional[str] = Field(default=None, description="The specific model version, if available.")
    prompt_version: str = Field(description="The version of the prompt used to generate this response.")
    timestamp: datetime = Field(description="The timestamp when this response was generated.")
    input_evidence_ids: List[str] = Field(description="List of document/evidence IDs used as context for this generation.")
    output_validation_status: str = Field(description="Status of the validation (e.g. 'VALIDATED').")
    prompt_tokens: Optional[int] = Field(default=None, description="Number of tokens in the prompt.")
    completion_tokens: Optional[int] = Field(default=None, description="Number of tokens in the generated completion.")
    total_cost: Optional[float] = Field(default=None, description="Estimated or tracked cost of the generation.")

class ProblemAnalysis(BaseAIPayload):
    """Schema for explaining an emerging economic problem."""
    problem_title: str = Field(description="A concise, formal title for the problem.")
    root_cause_analysis: str = Field(description="Detailed explanation of the root cause based on evidence.")
    impact_assessment: str = Field(description="Assessment of the economic impact.")
    severity_level: str = Field(description="Severity level: LOW, MEDIUM, HIGH, or CRITICAL.")

class TrendSummary(BaseAIPayload):
    """Schema for summarizing economic trends."""
    trend_name: str = Field(description="Name or title of the trend.")
    direction: str = Field(description="Direction of the trend (e.g. INCREASING, DECREASING, STABLE).")
    key_drivers: List[str] = Field(description="List of key factors driving this trend.")
    historical_context: str = Field(description="Brief historical context explaining this trend.")

class PolicyGapExplanation(BaseAIPayload):
    """Schema for explaining gaps between policy targets and actuals."""
    policy_name: str = Field(description="Name of the policy or budget item.")
    gap_reasoning: str = Field(description="Explanation of why the gap exists based on evidence.")
    systemic_issues: List[str] = Field(description="Broader systemic issues contributing to the gap.")

class ResearchRecommendation(BaseAIPayload):
    """Schema for synthesizing solutions from past PIDE research."""
    problem_statement: str = Field(description="The problem being addressed.")
    suggested_solution: str = Field(description="The synthesized solution based solely on the provided research.")
    key_interventions: List[str] = Field(description="Actionable interventions extracted from the research.")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0 that the solution directly addresses the problem.")

class Citation(BaseModel):
    """Citation linking factual claims to exact sources."""
    text: str = Field(description="The citation or evidence text.")
    source_url: Optional[str] = Field(default=None, description="Original source URL if applicable.")
    source_document_id: Optional[str] = Field(default=None, description="ID of the research or policy document.")
    indicator_id: Optional[str] = Field(default=None, description="ID of the macroeconomic indicator observation.")
    research_paper_id: Optional[str] = Field(default=None, description="Specific ID of a PIDE research paper.")

class WeeklyEconomicReport(BaseAIPayload):
    """Schema for generating the final weekly report (10 strictly required sections)."""
    # 1. Executive Summary
    executive_summary: str = Field(description="High-level executive summary of the week's economic landscape.")
    
    # 2. Top 10 Problems
    top_10_problems: List[ProblemAnalysis] = Field(description="List of top 10 critical problems detected.")
    
    # 3. Economic Indicator Trends
    economic_indicator_trends: List[TrendSummary] = Field(description="List of notable trends.")
    
    # 4. Policy Gaps
    policy_gaps: List[PolicyGapExplanation] = Field(description="List of policy gaps.")
    
    # 5. Emerging News Topics
    emerging_news_topics: List[str] = Field(description="List of emerging news topics and narratives.")
    
    # 6. Relevant PIDE Research
    relevant_pide_research: List[ResearchRecommendation] = Field(description="List of recommended actions derived strictly from PIDE research.")
    
    # 7. Evidence and Citations
    evidence_and_citations: List[Citation] = Field(description="List of citations verifying factual claims.")
    
    # 8. Methodology
    methodology: str = Field(description="Explanation of the methodology used to rank and synthesize this report.")
    
    # 9. Data Quality Notes
    data_quality_notes: str = Field(description="Notes on data confidence, missing data, and quality.")
    
    # 10. AI Generation Metadata is inherited from BaseAIPayload
