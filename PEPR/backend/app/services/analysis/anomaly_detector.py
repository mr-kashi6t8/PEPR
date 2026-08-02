from typing import List, Dict, Any
import uuid
from app.services.analysis.statistical_engine import StatisticalEngine
from datetime import datetime

class AnomalyDetector:
    def __init__(self, indicator_id: str):
        self.indicator_id = indicator_id

    def analyze(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze observations for anomalies using multiple algorithms.
        Returns list of detected anomalies with observation tracking.
        """
        if len(observations) < 2:
            return []
        
        # Create a timestamp->observation_id mapping for later reference
        obs_map = {
            obs.get('timestamp'): obs.get('id') 
            for obs in observations
        }
            
        raw_anomalies = []
        # Algorithm 1: Z-Score Statistical Outlier Engine
        z_anoms = StatisticalEngine.detect_anomalies_zscore(observations)
        raw_anomalies.extend(z_anoms)

        # Algorithm 2: IsolationForest Machine Learning Engine
        if len(observations) >= 5:
            iso_anoms = StatisticalEngine.detect_anomalies_isolation_forest(observations)
            raw_anomalies.extend(iso_anoms)
            
        results = []
        for anomaly in raw_anomalies:
            confidence = min(abs(anomaly["anomaly_score"]) / 10.0, 1.0)
            
            # Get observation ID from timestamp
            anom_timestamp = anomaly.get("timestamp")
            if isinstance(anom_timestamp, str):
                try:
                    anom_timestamp = datetime.fromisoformat(anom_timestamp)
                except:
                    pass
            
            obs_id = None
            for obs in observations:
                obs_ts = obs.get('timestamp')
                if isinstance(obs_ts, str):
                    try:
                        obs_ts = datetime.fromisoformat(obs_ts)
                    except:
                        pass
                
                if obs_ts == anom_timestamp:
                    obs_id = obs.get('id')
                    break
            
            results.append({
                "anomaly_score": abs(anomaly["anomaly_score"]),
                "baseline": anomaly.get("baseline_median", 0.0),
                "observed_value": anomaly["observed_value"],
                "expected_range": anomaly.get("expected_range", "N/A"),
                "detection_method": anomaly["method"],
                "confidence": confidence,
                "evidence": f"Observed value {anomaly['observed_value']} deviated significantly from baseline.",
                "observation_id": obs_id,
                "timestamp": anom_timestamp
            })
            
        return results
