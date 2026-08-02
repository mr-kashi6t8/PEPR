from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from .base import PEPRBaseSchema

class DetectedTrendCreate(BaseModel):
    indicator_id: str
    trend_direction: str
    confidence_score: Optional[float] = None
    ai_model_version: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class DetectedTrendResponse(PEPRBaseSchema, DetectedTrendCreate):
    pass

class DetectedAnomalyCreate(BaseModel):
    observation_id: str
    anomaly_score: float
    algorithm_used: str

class DetectedAnomalyResponse(PEPRBaseSchema, DetectedAnomalyCreate):
    pass

class EmergingProblemCreate(BaseModel):
    title: str
    description: str
    severity: str
    status: str = "open"

class EmergingProblemResponse(PEPRBaseSchema, EmergingProblemCreate):
    pass

class ProblemEvidenceCreate(BaseModel):
    problem_id: str
    evidence_type: str
    reference_id: str
    relevance_score: Optional[float] = None

class ProblemEvidenceResponse(PEPRBaseSchema, ProblemEvidenceCreate):
    pass
