from celery import shared_task
from typing import List, Dict, Any
from app.services.analysis.trend_detector import TrendDetector
from app.services.analysis.anomaly_detector import AnomalyDetector
from app.services.analysis.aggregator import EvidenceAggregator
import logging

logger = logging.getLogger("pepr.analysis")

@shared_task(name="analyze_indicator_timeseries")
def analyze_indicator_timeseries(indicator_id: str, observations: List[Dict[str, Any]]):
    """
    Celery task that runs Trend and Anomaly detection purely on the statistical engine.
    """
    logger.info(f"Starting analysis for indicator={indicator_id}")
    
    # 1. Trend Detection
    trend_detector = TrendDetector(indicator_id=indicator_id)
    trend_result = trend_detector.analyze(observations)
    if trend_result:
        logger.info(f"Detected trend for {indicator_id}: {trend_result['trend_direction']}")
        # Here we would persist trend_result via repository
        
    # 2. Anomaly Detection
    anomaly_detector = AnomalyDetector(indicator_id=indicator_id)
    anomalies = anomaly_detector.analyze(observations)
    
    if anomalies:
        logger.warning(f"Detected {len(anomalies)} anomalies for {indicator_id}")
        # Here we would persist anomalies via repository
        
    return {
        "indicator_id": indicator_id,
        "trend": trend_result,
        "anomalies_count": len(anomalies)
    }

@shared_task(name="app.services.analysis.tasks.trigger_continuous_aggregation")
def trigger_continuous_aggregation(source_id: str):
    """
    Runs continuously every time a new anomaly or news article is ingested.
    """
    logger.info(f"Running continuous Evidence Aggregation for source={source_id}")
    
    # In a real system, we'd query the DB for the last 24hrs of anomalies and news.
    # For this architecture proof, we instantiate the Aggregator to show the chain.
    aggregator = EvidenceAggregator(indicator_id="sys_aggregated")
    
    # Simulate DB fetch
    mock_anomalies = [{"anomaly_score": 5.5, "observed_value": 100}]
    mock_trend = {"severity": "high"}
    mock_articles = [
        {"title": "Inflation rises", "clean_text": "Prices are up.", "sentiment_score": -0.8, "url": "http://dawn.com/1"},
        {"title": "Economy bad", "clean_text": "Not looking good.", "sentiment_score": -0.9, "url": "http://dawn.com/2"}
    ]
    
    problem = aggregator.generate_candidate_problem(
        anomalies=mock_anomalies, 
        trend=mock_trend, 
        recent_articles=mock_articles
    )
    
    if problem:
        logger.warning(f"EMERGING PROBLEM DETECTED: {problem['title']}")
        # Here we would persist the problem to the EmergingProblem repository
        
    return problem
