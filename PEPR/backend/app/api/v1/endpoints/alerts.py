from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from app.infrastructure.database import get_db
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.models.news import SentimentAnalysisResult, NewsArticle
from app.models.ingestion import IngestionRun, IngestionJob, DataSource
from app.models.analysis import EmergingProblem
from app.models.policy import PolicyGap, PolicyTarget

router = APIRouter()

@router.get("/")
@router.get("")
async def get_system_alerts(db: AsyncSession = Depends(get_db)):
    """
    Generates 100% dynamic real-time system-wide alerts across ALL 5 PEPR components:
    1. System Ingestion Pipeline Runs & Connector Events
    2. Emerging Problems & Economic Radar Priorities
    3. Policy Target vs Actual Deviations
    4. Media Sentiment & YouTube Talkshow Transcript Shocks
    5. Macroeconomic Time-Series Observations & Trend Anomalies
    """
    alerts = []

    # 1. System Ingestion Pipeline Runs & Connector Events
    try:
        run_stmt = (
            select(IngestionRun, IngestionJob, DataSource)
            .join(IngestionJob, IngestionRun.job_id == IngestionJob.id)
            .join(DataSource, IngestionJob.source_id == DataSource.id)
            .order_by(IngestionRun.created_at.desc())
            .limit(8)
        )
        run_res = await db.execute(run_stmt)
        for r, job, ds in run_res:
            status = r.status or "UNKNOWN"
            severity = "INFO" if status == "SUCCESS" else ("CRITICAL" if status == "FAILED" else "WARNING")
            
            alerts.append({
                "id": f"alert_ingest_{r.id}",
                "title": f"Pipeline Run: {ds.name} ({status})",
                "message": f"Data ingestion run for source connector '{ds.name}' completed with status '{status}'. Ingested {r.records_fetched or 0} records.",
                "details": f"Job ID: {job.id}. Run ID: {r.id}. Created at: {r.created_at}. Source type: {ds.source_type}. Execution status: {status}. Log error: {r.error_message or 'None'}.",
                "content": f"Ingestion Run log record {r.id} for connector '{ds.name}'. Total records ingested: {r.records_fetched or 0}. Status code: {status}.",
                "url": "http://localhost:5173/admin/ingestion",
                "severity": severity,
                "category": "SYSTEM_INGESTION",
                "timestamp": r.created_at.strftime("%Y-%m-%d %H:%M UTC") if r.created_at else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "is_read": False,
            })
    except Exception as e:
        print(f"Error querying ingestion alerts: {e}")

    # 2. Emerging Problems & Economic Radar Priorities
    try:
        prob_stmt = select(EmergingProblem).order_by(EmergingProblem.created_at.desc()).limit(5)
        prob_res = await db.execute(prob_stmt)
        for prob in prob_res.scalars().all():
            alerts.append({
                "id": f"alert_prob_{prob.id}",
                "title": f"Emerging Problem Radar: {prob.title}",
                "message": f"High priority economic problem flagged by Evidence Aggregator with severity '{prob.severity}'.",
                "details": f"Problem Title: {prob.title}. Status: {prob.status}. Engine severity rating: {prob.severity.upper()}.",
                "content": prob.description or "Automated candidate problem synthesized by PEPR Evidence Aggregator.",
                "url": f"http://localhost:5173/problems/{prob.id}",
                "severity": "CRITICAL" if prob.severity.lower() in {"critical", "high"} else "HIGH",
                "category": "EMERGING_PROBLEM",
                "timestamp": prob.created_at.strftime("%Y-%m-%d %H:%M UTC") if prob.created_at else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "is_read": False,
            })
    except Exception as e:
        print(f"Error querying emerging problem alerts: {e}")

    # 3. Policy Target Gaps & Research Deviations
    try:
        gap_stmt = (
            select(PolicyGap, PolicyTarget)
            .join(PolicyTarget, PolicyGap.target_id == PolicyTarget.id)
            .limit(5)
        )
        gap_res = await db.execute(gap_stmt)
        for gap, target in gap_res:
            alerts.append({
                "id": f"alert_gap_{gap.id}",
                "title": f"Policy Target Gap: {target.target_name}",
                "message": f"Policy gap deviation of {gap.gap_percentage:+.1f}% identified against target benchmark ({target.target_value} {target.target_unit}).",
                "details": f"Target Name: {target.target_name}. Responsible Agency: {target.responsible_institution or 'Govt of Pakistan'}. Gap Status: {gap.gap_status}.",
                "content": f"Policy Gap Analysis: Target value = {target.target_value} {target.target_unit}. Engine magnitude score = {gap.magnitude_score:.2f}.",
                "url": "http://localhost:5173/trends",
                "severity": "HIGH",
                "category": "POLICY_GAP",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "is_read": False,
            })
    except Exception as e:
        print(f"Error querying policy gap alerts: {e}")

    # 4. Media Sentiment & Talkshow Transcripts from PostgreSQL news_articles
    try:
        sent_stmt = (
            select(NewsArticle, SentimentAnalysisResult)
            .join(SentimentAnalysisResult, NewsArticle.id == SentimentAnalysisResult.article_id)
            .order_by(NewsArticle.published_at.desc())
            .limit(10)
        )
        sent_res = await db.execute(sent_stmt)
        for art, sent in sent_res:
            score = sent.score or 0.0
            is_youtube = "youtube" in (art.url or "").lower() or "youtu.be" in (art.url or "").lower()
            category = "TALKSHOW_TRANSCRIPT" if is_youtube else "MEDIA_SENTIMENT"
            severity = "CRITICAL" if score < -0.4 else ("HIGH" if score < -0.15 else ("WARNING" if score < 0.0 else "INFO"))

            alerts.append({
                "id": f"alert_media_{art.id}",
                "title": f"Media Sentiment Shift: {art.title}",
                "message": f"NLP Sentiment score of {score:.2f} ({sent.label}) detected in live {category.replace('_', ' ').title()}.",
                "details": f"Analyzed by PEPR NLP Engine (Model: {sent.ai_model_version or 'pepr-nlp-v1'}). Persisted in news_articles database table.",
                "content": art.content or "Article/transcript content indexed in PostgreSQL database.",
                "url": art.url,
                "severity": severity,
                "category": category,
                "timestamp": art.published_at.strftime("%Y-%m-%d %H:%M UTC") if art.published_at else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "is_read": False,
            })
    except Exception as e:
        print(f"Error querying news alerts: {e}")

    # 5. Macroeconomic Indicator Observations from PostgreSQL
    try:
        obs_stmt = (
            select(IndicatorObservation, EconomicIndicator)
            .join(EconomicIndicator, IndicatorObservation.indicator_id == EconomicIndicator.id)
            .order_by(IndicatorObservation.timestamp.desc())
            .limit(8)
        )
        obs_res = await db.execute(obs_stmt)
        for obs, ind in obs_res:
            alerts.append({
                "id": f"alert_obs_{obs.id}",
                "title": f"Macro Economic Observation: {ind.name}",
                "message": f"Observation value of {obs.value} recorded for indicator {ind.code} ({ind.name}).",
                "details": f"Indicator Name: {ind.name}. Code: {ind.code}. Value: {obs.value}. Timestamp: {obs.timestamp}. Source: Live Database Ingestion.",
                "content": f"Observation record {obs.id} persisted in PostgreSQL indicator_observations table with value={obs.value} at timestamp {obs.timestamp}.",
                "url": "http://localhost:5173/indicators",
                "severity": "HIGH",
                "category": "MACRO_ANOMALY",
                "timestamp": obs.timestamp.strftime("%Y-%m-%d %H:%M UTC") if obs.timestamp else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "is_read": False,
            })
    except Exception as e:
        print(f"Error querying indicator alerts: {e}")

    # Sort all alerts by timestamp descending
    alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return alerts
