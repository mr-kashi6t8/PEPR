from typing import Optional, Dict, Any
from pydantic import BaseModel
from .base import PEPRBaseSchema

class AIAnalysisRunCreate(BaseModel):
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    purpose: Optional[str] = None

class AIAnalysisRunResponse(PEPRBaseSchema, AIAnalysisRunCreate):
    pass

class GeneratedReportCreate(BaseModel):
    title: str
    content_markdown: str
    structured_data: Optional[Dict[str, Any]] = None
    ai_run_id: Optional[str] = None
    status: Optional[str] = "PENDING"
    report_date: Optional[str] = None
    version: Optional[int] = 1
    pdf_path: Optional[str] = None
    html_path: Optional[str] = None

class GeneratedReportResponse(PEPRBaseSchema, GeneratedReportCreate):
    pass

ReportResponse = GeneratedReportResponse
ReportDetail = GeneratedReportResponse

class ReportCitationCreate(BaseModel):

    report_id: str
    citation_text: str
    reference_id: str
    reference_type: str

class ReportCitationResponse(PEPRBaseSchema, ReportCitationCreate):
    pass

class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str
    related_entity_id: Optional[str] = None

class AlertResponse(PEPRBaseSchema, AlertCreate):
    is_read: bool
