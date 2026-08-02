from sqlalchemy import Column, String, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class DetectedTrend(BaseModel):
    __tablename__ = "detected_trends"
    
    indicator_id = Column(ForeignKey("economic_indicators.id"), nullable=False, index=True)
    trend_direction = Column(String(50), nullable=False) # upward, downward, flat
    current_value = Column(Float, nullable=False, default=0.0)
    previous_value = Column(Float, nullable=False, default=0.0)
    pct_change = Column(Float, nullable=False, default=0.0)
    period = Column(String(100), nullable=False, default="unknown")
    severity = Column(String(50), nullable=False, default="medium")
    detection_method = Column(String(100), nullable=False, default="statistical")
    supporting_observations = Column(Text)
    source_references = Column(Text)
    
    confidence_score = Column(Float)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    indicator = relationship("EconomicIndicator")

class DetectedAnomaly(BaseModel):
    __tablename__ = "detected_anomalies"
    
    observation_id = Column(ForeignKey("indicator_observations.id"), nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    algorithm_used = Column(String(100), nullable=False) # e.g. IsolationForest, Robust Z-Score
    
    observation = relationship("IndicatorObservation")

class EmergingProblem(BaseModel):
    __tablename__ = "emerging_problems"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False) # high, medium, low
    status = Column(String(50), default="open")
    
    evidence = relationship("ProblemEvidence", back_populates="problem")

class ProblemEvidence(BaseModel):
    __tablename__ = "problem_evidence"
    
    problem_id = Column(ForeignKey("emerging_problems.id"), nullable=False)
    evidence_type = Column(String(50), nullable=False) # anomaly, trend, news, policy_gap
    reference_id = Column(String, nullable=False) # UUID of the referenced entity
    relevance_score = Column(Float)
    
    problem = relationship("EmergingProblem", back_populates="evidence")
