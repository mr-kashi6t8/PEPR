import pytest
import numpy as np
from datetime import datetime, timedelta, timezone
from app.services.analysis.trend_detector import TrendDetector
from app.services.analysis.anomaly_detector import AnomalyDetector
from app.services.analysis.statistical_engine import StatisticalEngine

def _generate_synthetic_data(num_points: int, baseline: float = 100.0, trend: float = 0.0, spike_index: int = -1, spike_value: float = 0.0):
    """Generates deterministic synthetic time-series data."""
    base_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
    observations = []
    
    for i in range(num_points):
        val = baseline + (i * trend)
        if i == spike_index:
            val = spike_value
            
        observations.append({
            "timestamp": (base_time + timedelta(days=i)).isoformat(),
            "value": val
        })
    return observations

def test_statistical_engine_changes():
    data = _generate_synthetic_data(5, baseline=100.0, trend=2.0)
    # values: 100, 102, 104, 106, 108
    # prev: 106, curr: 108
    
    changes = StatisticalEngine.calculate_changes(data)
    assert changes['current_value'] == 108.0
    assert changes['previous_value'] == 106.0
    assert changes['abs_change'] == 2.0
    assert round(changes['pct_change'], 2) == 1.89 # (2 / 106) * 100

def test_trend_detector_upward():
    data = _generate_synthetic_data(10, baseline=100.0, trend=5.0)
    detector = TrendDetector(indicator_id="ind_test")
    trend = detector.analyze(data)
    
    assert trend is not None
    assert trend['direction'] == "upward"
    assert trend['percentage_change'] > 0
    assert trend['confidence'] > 0 # based on length
    assert 'supporting_observations' in trend
    assert 'source_references' in trend

def test_anomaly_detector_zscore_small_data():
    # 10 points (Uses Z-Score)
    # Baseline 100, massive spike at index 5 to 500
    data = _generate_synthetic_data(10, baseline=100.0, spike_index=5, spike_value=500.0)
    detector = AnomalyDetector(indicator_id="ind_test")
    anomalies = detector.analyze(data)
    
    assert len(anomalies) == 1
    assert anomalies[0]['observed_value'] == 500.0
    assert anomalies[0]['detection_method'] == "Robust Z-Score"
    assert 'expected_range' in anomalies[0]
    assert 'evidence' in anomalies[0]

def test_anomaly_detector_isolation_forest_large_data():
    # 40 points (Uses Isolation Forest)
    # Baseline 100, massive spike at index 35 to 1000
    data = _generate_synthetic_data(40, baseline=100.0, spike_index=35, spike_value=1000.0)
    detector = AnomalyDetector(indicator_id="ind_test")
    anomalies = detector.analyze(data)
    
    assert len(anomalies) > 0
    
    spike_anomaly = next((a for a in anomalies if a['observed_value'] == 1000.0), None)
    assert spike_anomaly is not None
    assert spike_anomaly['detection_method'] == "Seasonal-aware Isolation Forest"
