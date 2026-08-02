from typing import Optional, Dict, Any
from pydantic import BaseModel
from .base import PEPRBaseSchema

class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    base_url: str

class DataSourceResponse(PEPRBaseSchema, DataSourceCreate):
    is_active: bool

class DataSourceConfigCreate(BaseModel):
    source_id: str
    auth_type: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    parsing_rules: Optional[Dict[str, Any]] = None

class DataSourceConfigResponse(PEPRBaseSchema, DataSourceConfigCreate):
    pass

class IngestionJobCreate(BaseModel):
    source_id: str
    name: str
    cron_schedule: Optional[str] = None

class IngestionJobResponse(PEPRBaseSchema, IngestionJobCreate):
    is_active: bool

class IngestionRunCreate(BaseModel):
    job_id: str
    status: str
    records_fetched: int = 0
    error_message: Optional[str] = None

class IngestionRunResponse(PEPRBaseSchema, IngestionRunCreate):
    pass

class RawDataRecordCreate(BaseModel):
    source_id: str
    payload: Dict[str, Any]
    source_url: Optional[str] = None

class RawDataRecordResponse(PEPRBaseSchema, RawDataRecordCreate):
    is_processed: bool
