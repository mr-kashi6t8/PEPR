from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel

class DataSource(BaseModel):
    __tablename__ = "data_sources"
    
    name = Column(String(100), unique=True, index=True, nullable=False)
    source_type = Column(String(50), nullable=False) # api, rss, html
    base_url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    
    configurations = relationship("DataSourceConfig", back_populates="source")
    jobs = relationship("IngestionJob", back_populates="source")
    raw_records = relationship("RawDataRecord", back_populates="source")

class DataSourceConfig(BaseModel):
    __tablename__ = "data_source_configs"
    
    source_id = Column(ForeignKey("data_sources.id"), nullable=False)
    auth_type = Column(String(50))
    credentials = Column(JSON) # encrypted or keys
    parsing_rules = Column(JSON)
    
    source = relationship("DataSource", back_populates="configurations")

class IngestionJob(BaseModel):
    __tablename__ = "ingestion_jobs"
    
    source_id = Column(ForeignKey("data_sources.id"), nullable=False)
    name = Column(String(100), nullable=False)
    cron_schedule = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    source = relationship("DataSource", back_populates="jobs")
    runs = relationship("IngestionRun", back_populates="job")

class IngestionRun(BaseModel):
    __tablename__ = "ingestion_runs"
    
    job_id = Column(ForeignKey("ingestion_jobs.id"), nullable=False)
    status = Column(String(50), nullable=False, index=True) # pending, running, success, failed
    records_fetched = Column(Integer, default=0)
    error_message = Column(String)
    
    job = relationship("IngestionJob", back_populates="runs")

class RawDataRecord(BaseModel):
    __tablename__ = "raw_data_records"
    
    source_id = Column(ForeignKey("data_sources.id"), nullable=False)
    payload = Column(JSON, nullable=False)
    source_url = Column(String(1000))
    is_processed = Column(Boolean, default=False, index=True)
    
    source = relationship("DataSource", back_populates="raw_records")
