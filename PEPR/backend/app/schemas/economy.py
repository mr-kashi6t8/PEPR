from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from .base import PEPRBaseSchema

class EconomicIndicatorCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class EconomicIndicatorResponse(PEPRBaseSchema, EconomicIndicatorCreate):
    is_active: bool

class IndicatorMetadataCreate(BaseModel):
    indicator_id: str
    unit: str
    frequency: str
    source_agency: Optional[str] = None

class IndicatorMetadataResponse(PEPRBaseSchema, IndicatorMetadataCreate):
    pass

class IndicatorObservationCreate(BaseModel):
    indicator_id: str
    timestamp: datetime
    value: float
    raw_record_id: Optional[str] = None

class IndicatorObservationResponse(PEPRBaseSchema, IndicatorObservationCreate):
    pass
