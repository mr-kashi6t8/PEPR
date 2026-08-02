from sqlalchemy import Column, String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel

class EconomicIndicator(BaseModel):
    __tablename__ = "economic_indicators"
    
    name = Column(String(200), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    
    metadata_info = relationship("IndicatorMetadata", back_populates="indicator", uselist=False)
    observations = relationship("IndicatorObservation", back_populates="indicator")

class IndicatorMetadata(BaseModel):
    __tablename__ = "indicator_metadata"
    
    indicator_id = Column(ForeignKey("economic_indicators.id"), unique=True, nullable=False)
    unit = Column(String(50), nullable=False)
    frequency = Column(String(50), nullable=False) # daily, monthly, yearly
    source_agency = Column(String(100))
    
    indicator = relationship("EconomicIndicator", back_populates="metadata_info")

class IndicatorObservation(BaseModel):
    __tablename__ = "indicator_observations"
    
    indicator_id = Column(ForeignKey("economic_indicators.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Float, nullable=False)
    raw_record_id = Column(ForeignKey("raw_data_records.id"), nullable=True) # Provenance
    
    indicator = relationship("EconomicIndicator", back_populates="observations")
