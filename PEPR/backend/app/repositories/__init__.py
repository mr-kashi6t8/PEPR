from .base import BaseRepository
from app.models import (
    User, Role, AuditLog,
    DataSource, DataSourceConfig, IngestionJob, IngestionRun, RawDataRecord,
    EconomicIndicator, IndicatorMetadata, IndicatorObservation,
    DetectedTrend, DetectedAnomaly, EmergingProblem, ProblemEvidence,
    NewsArticle, NewsTopic, SentimentAnalysisResult,
    PolicyTarget, PolicyActual, PolicyGap,
    ResearchDocument, ResearchChunk, ResearchCitation,
    AIAnalysisRun, GeneratedReport, ReportCitation, Alert
)

# Auth Repositories
user_repo = BaseRepository(User)
role_repo = BaseRepository(Role)
audit_log_repo = BaseRepository(AuditLog)

# Ingestion Repositories
data_source_repo = BaseRepository(DataSource)
data_source_config_repo = BaseRepository(DataSourceConfig)
ingestion_job_repo = BaseRepository(IngestionJob)
ingestion_run_repo = BaseRepository(IngestionRun)
raw_data_record_repo = BaseRepository(RawDataRecord)

# Economy Repositories
economic_indicator_repo = BaseRepository(EconomicIndicator)
indicator_metadata_repo = BaseRepository(IndicatorMetadata)
indicator_observation_repo = BaseRepository(IndicatorObservation)

# Analysis Repositories
detected_trend_repo = BaseRepository(DetectedTrend)
detected_anomaly_repo = BaseRepository(DetectedAnomaly)
emerging_problem_repo = BaseRepository(EmergingProblem)
problem_evidence_repo = BaseRepository(ProblemEvidence)

# News Repositories
news_article_repo = BaseRepository(NewsArticle)
news_topic_repo = BaseRepository(NewsTopic)
sentiment_analysis_result_repo = BaseRepository(SentimentAnalysisResult)

# Policy Repositories
policy_target_repo = BaseRepository(PolicyTarget)
policy_actual_repo = BaseRepository(PolicyActual)
policy_gap_repo = BaseRepository(PolicyGap)

# Research Repositories
research_document_repo = BaseRepository(ResearchDocument)
research_chunk_repo = BaseRepository(ResearchChunk)
research_citation_repo = BaseRepository(ResearchCitation)

# Reports Repositories
ai_analysis_run_repo = BaseRepository(AIAnalysisRun)
generated_report_repo = BaseRepository(GeneratedReport)
report_citation_repo = BaseRepository(ReportCitation)
alert_repo = BaseRepository(Alert)
