from typing import Optional, List
from pydantic import BaseModel as PydanticBaseModel
from datetime import datetime
import uuid

# TARGETS
class PolicyTargetBase(PydanticBaseModel):
    indicator_id: uuid.UUID
    target_name: str
    target_value: float
    target_unit: str
    target_period: str
    target_source: str
    target_document: Optional[str] = None
    responsible_institution: Optional[str] = None
    methodology: Optional[str] = None
    source_citation: Optional[str] = None
    higher_is_better: bool = True
    importance_weight: float = 1.0
    target_confidence: float = 1.0
    neutral_tolerance_percent: float = 1.0

class PolicyTargetCreate(PolicyTargetBase):
    pass

class PolicyTargetResponse(PolicyTargetBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ACTUALS
class PolicyActualBase(PydanticBaseModel):
    target_id: uuid.UUID
    actual_value: float
    actual_period: str
    actual_source: str
    data_quality_status: float = 1.0

class PolicyActualCreate(PolicyActualBase):
    pass

class PolicyActualResponse(PolicyActualBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# GAPS
class PolicyGapBase(PydanticBaseModel):
    target_id: uuid.UUID
    actual_id: uuid.UUID
    gap_value: float
    gap_percentage: float
    gap_status: str
    engine_score: float
    magnitude_score: float
    persistence_score: float
    analysis_notes: Optional[str] = None

class PolicyGapResponse(PolicyGapBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    target: Optional[PolicyTargetResponse] = None
    actual: Optional[PolicyActualResponse] = None

    class Config:
        from_attributes = True
