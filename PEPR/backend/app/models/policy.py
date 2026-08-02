from sqlalchemy import Column, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class PolicyTarget(BaseModel):
    __tablename__ = "policy_targets"
    
    # Required relations
    indicator_id = Column(ForeignKey("economic_indicators.id"), nullable=False, index=True)
    
    # Required Fields from M4 prompt
    target_name = Column(String(255), nullable=False)
    target_value = Column(Float, nullable=False)
    target_unit = Column(String(50), nullable=False)
    target_period = Column(String(100), nullable=False) # e.g. "FY24", "Q1 2024"
    target_source = Column(String(255), nullable=False)
    target_document = Column(String(1000))
    responsible_institution = Column(String(255))
    methodology = Column(String(2000))
    source_citation = Column(String(1000))
    
    # Scoring Configuration
    higher_is_better = Column(Boolean, nullable=False, default=True)
    importance_weight = Column(Float, nullable=False, default=1.0)
    target_confidence = Column(Float, nullable=False, default=1.0) # Used in engine
    neutral_tolerance_percent = Column(Float, nullable=False, default=1.0) # Economist Logic: +/- 1% is neutral by default
    
    indicator = relationship("EconomicIndicator")
    gaps = relationship("PolicyGap", back_populates="target")

class PolicyActual(BaseModel):
    __tablename__ = "policy_actuals"
    
    target_id = Column(ForeignKey("policy_targets.id"), nullable=False)
    
    # Required Fields
    actual_value = Column(Float, nullable=False)
    actual_period = Column(String(100), nullable=False)
    actual_source = Column(String(255), nullable=False)
    data_quality_status = Column(Float, nullable=False, default=1.0) # 0.0 to 1.0
    
    target = relationship("PolicyTarget")

class PolicyGap(BaseModel):
    __tablename__ = "policy_gaps"
    
    target_id = Column(ForeignKey("policy_targets.id"), nullable=False)
    actual_id = Column(ForeignKey("policy_actuals.id"), nullable=False)
    
    # Calculated Fields
    gap_value = Column(Float, nullable=False)
    gap_percentage = Column(Float, nullable=False)
    gap_status = Column(String(50), nullable=False) # POSITIVE, NEGATIVE, NEUTRAL
    
    # Engine Score
    engine_score = Column(Float, nullable=False)
    magnitude_score = Column(Float, nullable=False)
    persistence_score = Column(Float, nullable=False)
    
    analysis_notes = Column(String)
    
    target = relationship("PolicyTarget", back_populates="gaps")
    actual = relationship("PolicyActual")
