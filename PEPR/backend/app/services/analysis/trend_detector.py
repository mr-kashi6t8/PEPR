from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from app.services.analysis.statistical_engine import StatisticalEngine
import numpy as np
import pandas as pd

class TrendDetector:
    def __init__(self, indicator_id: str):
        self.indicator_id = indicator_id

    def _calculate_trend_score(self, pct_change: float, history_len: int, volatility: float) -> float:
        """
        Trend Score = magnitude + persistence + historical unusualness + economic importance + data confidence
        """
        magnitude = min(abs(pct_change) / 5.0, 10.0) 
        persistence = min(history_len / 12.0, 5.0) 
        
        # Historical unusualness (using volatility as proxy: if change is much larger than normal volatility)
        unusualness = 0.0
        if volatility > 0 and abs(pct_change) > volatility:
            unusualness = min((abs(pct_change) / volatility) * 2.0, 5.0)
            
        economic_importance = 3.0 # Configurable per indicator metadata
        data_confidence = min(history_len / 24.0, 2.0) # More data = higher confidence
        
        return magnitude + persistence + unusualness + economic_importance + data_confidence

    def _calculate_forecast_corridor(self, observations: List[Dict[str, Any]], current_val: float, volatility: float) -> Dict[str, float]:
        if len(observations) < 2:
            return {
                "expected": round(current_val, 2),
                "min_corridor": round(current_val * 0.95, 2),
                "max_corridor": round(current_val * 1.05, 2),
            }
        vals = [float(o["value"]) for o in observations if o.get("value") is not None]
        alpha = 0.3
        smoothed = vals[0]
        for v in vals[1:]:
            smoothed = alpha * v + (1 - alpha) * smoothed

        std_err = float(np.std(vals)) if len(vals) > 2 else abs(current_val * 0.05)
        margin = max(std_err * 1.96, abs(current_val * 0.03))

        return {
            "expected": round(smoothed, 2),
            "min_corridor": round(smoothed - margin, 2),
            "max_corridor": round(smoothed + margin, 2),
        }

    def analyze(self, observations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if len(observations) < 1:
            return None

        # For single-observation indicators, manufacture a flat baseline trend
        if len(observations) == 1:
            ts = observations[0].get("timestamp")
            fmt = lambda t: t.strftime("%b %Y") if hasattr(t, 'strftime') else str(t)[:7]
            label = fmt(ts) if ts else "Latest"
            curr_val = observations[0]["value"]
            return {
                "indicator": self.indicator_id,
                "current_value": curr_val,
                "previous_value": curr_val,
                "percentage_change": 0.0,
                "period": f"{label} (First Observation)",
                "direction": "flat",
                "severity": "low",
                "confidence": min(1 / 24.0, 1.0),
                "detection_method": "Configurable Statistical Score (MoM/YoY)",
                "supporting_observations": {"mom_change": None, "qoq_change": None, "yoy_change": None, "volatility": 0.0},
                "forecast_30d": self._calculate_forecast_corridor(observations, curr_val, 0.0),
                "source_references": ["Derived from raw ingestion DB"],
                "trend_score": 3.0
            }

        changes = StatisticalEngine.calculate_changes(observations)
        if not changes:
            return None
            
        # Get volatility for scoring
        df_ma = StatisticalEngine.calculate_moving_average_and_volatility(observations, window=3)
        volatility = df_ma['volatility_3'].iloc[-1] if 'volatility_3' in df_ma.columns and not pd.isna(df_ma['volatility_3'].iloc[-1]) else 0.0
            
        pct_change = changes['pct_change']
        
        direction = "flat"
        if pct_change > 1.0:
            direction = "upward"
        elif pct_change < -1.0:
            direction = "downward"
            
        abs_pct = abs(pct_change)
        severity = "low"
        if abs_pct >= 3.0 or (volatility > 0 and abs_pct > volatility * 1.5):
            severity = "high"
        elif abs_pct >= 1.0 or (volatility > 0 and abs_pct > volatility * 0.8):
            severity = "medium"
            
        confidence_score = min(len(observations) / 24.0, 1.0)
        trend_score = self._calculate_trend_score(pct_change, len(observations), volatility)
        
        sorted_ts = sorted(
            [o["timestamp"] for o in observations if o.get("timestamp")],
            key=lambda t: t if hasattr(t, 'year') else pd.Timestamp(t)
        )
        first_time = sorted_ts[0] if sorted_ts else changes['period_start']
        last_time = sorted_ts[-1] if sorted_ts else changes['period_end']
        fmt = lambda t: t.strftime("%b %Y") if hasattr(t, 'strftime') else str(t)[:7]
        p_start, p_end = fmt(first_time), fmt(last_time)
        if p_start == p_end:
            period_str = f"{p_end} (Latest Ingestion)"
        else:
            period_str = f"{p_start} – {p_end} (Latest Ingestion)"

        forecast_30d = self._calculate_forecast_corridor(observations, changes['current_value'], volatility)

        return {
            "indicator": self.indicator_id,
            "current_value": changes['current_value'],
            "previous_value": changes['previous_value'],
            "percentage_change": pct_change,
            "period": period_str,
            "direction": direction,
            "severity": severity,
            "confidence": confidence_score,
            "detection_method": "Configurable Statistical Score (MoM/YoY)",
            "supporting_observations": {
                "mom_change": changes.get('mom_change'),
                "qoq_change": changes.get('qoq_change'),
                "yoy_change": changes.get('yoy_change'),
                "volatility": volatility
            },
            "forecast_30d": forecast_30d,
            "source_references": ["Derived from raw ingestion DB"],
            "trend_score": trend_score
        }
