from sqlalchemy import Column, String, ForeignKey, Integer, Float, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class AIAnalysisRun(BaseModel):
    __tablename__ = "ai_analysis_runs"
    
    model_name = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    purpose = Column(String(100)) # report_generation, sentiment, etc.

class GeneratedReport(BaseModel):
    __tablename__ = "generated_reports"
    
    title = Column(String(255), nullable=False)
    content_markdown = Column(Text, nullable=False)
    structured_data = Column(JSON)
    status = Column(String(50), default="PENDING") # PENDING, GENERATING, COMPLETED, FAILED
    report_date = Column(String(50), nullable=True) # ISO format or just string date
    version = Column(Integer, default=1)
    pdf_path = Column(String(500), nullable=True)
    html_path = Column(String(500), nullable=True)
    ai_run_id = Column(ForeignKey("ai_analysis_runs.id"), nullable=True)
    
    ai_run = relationship("AIAnalysisRun")
    citations = relationship("ReportCitation", back_populates="report")

class ReportCitation(BaseModel):
    __tablename__ = "report_citations"
    
    report_id = Column(ForeignKey("generated_reports.id"), nullable=False)
    citation_text = Column(String(500), nullable=False)
    reference_id = Column(String, nullable=False) # UUID of raw data or research
    reference_type = Column(String(50), nullable=False) # news, observation, research
    
    report = relationship("GeneratedReport", back_populates="citations")

class Alert(BaseModel):
    __tablename__ = "alerts"
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False) # critical, warning, info
    is_read = Column(Boolean, default=False)
    related_entity_id = Column(String) # UUID of anomaly, gap, problem
