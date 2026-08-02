from fastapi import APIRouter
from app.api.v1.endpoints import health, ingestion, trends, anomalies, indicators, policy, news, research, reports, problems, alerts, auth

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(ingestion.router, prefix="/admin/ingestion", tags=["admin_ingestion"])
api_router.include_router(trends.router, prefix="/trends", tags=["trends"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(indicators.router, prefix="/indicators", tags=["indicators"])
api_router.include_router(problems.router, prefix="/problems", tags=["problems"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(policy.router, tags=["policy"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
