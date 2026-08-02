from pydantic import BaseModel
from typing import Dict, Any, Literal

class HealthResponse(BaseModel):
    status: str
    service: str
    details: Dict[str, Any] = {}

class SystemHealthResponse(BaseModel):
    overall_status: Literal['HEALTHY', 'WARNING', 'CRITICAL']
    database_status: str
    vector_db_status: str
    ai_gateway_status: str
    active_jobs: int
    uptime_seconds: int
