from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone
from app.services.nlp.topic_modeler import TopicModeler

# Mock historical data for trend detection
MOCK_HISTORICAL_TOPIC_VOLUMES = {
    "inflation": 5,
    "imf": 10,
    "tax": 2
}
from datetime import datetime, timezone
from app.services.nlp.topic_modeler import TopicModeler

class EvidenceAggregator:
    """
    Evidence Aggregation Layer (M3)
    Combines M2 anomalies with M3 news clusters to detect Emerging Problems.
    """
    
    def __init__(self, indicator_id: str):
        self.indicator_id = indicator_id

    def generate_candidate_problem(
        self, 
        anomalies: List[Dict[str, Any]], 
        trend: Optional[Dict[str, Any]], 
        recent_articles: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Runs continuously. Matches anomalies with news clusters.
        """
        if not anomalies and (not trend or trend.get('severity') == 'low'):
            # No strong quantitative signal
            return None
            
        # Cluster the recent news
        clusters = TopicModeler.cluster_articles(recent_articles)
        
        # Find if there is a dominant negative or high-volume news topic
        dominant_cluster = None
        highest_score = -999.0
        
        for cluster in clusters:
            if cluster["topic_id"] == -1:
                continue # ignore noise
                
            volume = len(cluster["articles"])
            avg_sentiment = sum(a.get("sentiment_score", 0) for a in cluster["articles"]) / volume if volume > 0 else 0
            
            # We look for high volume or very negative sentiment
            cluster_score = volume + (abs(avg_sentiment) * 10)
            if cluster_score > highest_score:
                highest_score = cluster_score
                dominant_cluster = cluster
                
        # If we have an anomaly AND a news cluster, we generate an Emerging Problem
        if dominant_cluster:
            avg_sentiment = sum(a.get("sentiment_score", 0) for a in dominant_cluster["articles"]) / len(dominant_cluster["articles"])
            keywords = ", ".join(dominant_cluster["keywords"])
            
            # Topic Growth / Keyword Trend Detection
            current_volume = len(dominant_cluster["articles"])
            past_volume = 1 # default to 1 to avoid division by zero
            for kw in dominant_cluster["keywords"]:
                if kw in MOCK_HISTORICAL_TOPIC_VOLUMES:
                    past_volume = MOCK_HISTORICAL_TOPIC_VOLUMES[kw]
            
            growth_rate = ((current_volume - past_volume) / past_volume) * 100
            topic_trend = f"Growing (+{growth_rate:.0f}%)" if growth_rate > 0 else "Stable"
            
            # Calculate severity based on anomaly score and news volume
            max_anomaly_score = max((a.get('anomaly_score', 0) for a in anomalies), default=0)
            severity = "high" if max_anomaly_score > 4.0 or current_volume > 10 else "medium"
            
            # Confidence based on multiple signals agreeing + source reliability
            avg_reliability = sum(a.get("source_reliability", 0.5) for a in dominant_cluster["articles"]) / current_volume
            confidence = min(0.3 + (current_volume / 20.0) + (max_anomaly_score / 20.0) + (avg_reliability * 0.3), 1.0)
            
            news_sources = list(set([a.get('url', '').split('/')[2] for a in dominant_cluster["articles"] if a.get('url')]))
            
            return {
                "id": str(uuid.uuid4()),
                "title": f"Emerging Problem detected in {self.indicator_id} related to: {keywords}",
                "description": f"Detected an anomaly score of {max_anomaly_score:.2f} coinciding with {current_volume} news articles.",
                "evidence": f"Combined {len(anomalies)} anomalies with negative news sentiment ({avg_sentiment:.2f}) across {current_volume} articles.",
                "affected_indicators": [self.indicator_id],
                "news_sources": news_sources,
                "topic_trend": topic_trend,
                "sentiment": avg_sentiment,
                "confidence": confidence,
                "severity": severity,
                "first_detected_date": datetime.now(timezone.utc).isoformat()
            }
            
        return None
