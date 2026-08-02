import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import IsolationForest

class StatisticalEngine:
    """
    Core numerical engine. 
    Strictly performs Pandas/Numpy calculations without LLM involvement.
    """
    
    @staticmethod
    def _to_dataframe(observations: List[Dict[str, Any]]) -> pd.DataFrame:
        if not observations:
            return pd.DataFrame()
        df = pd.DataFrame(observations)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        # Set timestamp as index for time-based operations like YoY, MoM
        df.set_index('timestamp', inplace=True)
        return df

    @classmethod
    def calculate_changes(cls, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates absolute, percentage, MoM, QoQ, and YoY changes."""
        df = cls._to_dataframe(observations)
        if len(df) < 2:
            return {}
            
        current_val = df['value'].iloc[-1]
        current_time = df.index[-1]
        
        previous_val = df['value'].iloc[-2]
        previous_time = df.index[-2]
        
        abs_change = current_val - previous_val
        pct_change = (abs_change / previous_val) * 100 if previous_val != 0 else 0.0
        
        # Calculate Time-based changes if enough history exists
        mom_change = np.nan
        qoq_change = np.nan
        yoy_change = np.nan
        
        try:
            # Shift by time frequency if data is fairly regular
            # Resample to monthly to calculate MoM, QoQ, YoY safely
            monthly = df.resample('ME').mean()
            if len(monthly) >= 2:
                mom_change = monthly['value'].pct_change(periods=1).iloc[-1] * 100
            if len(monthly) >= 4:
                qoq_change = monthly['value'].pct_change(periods=3).iloc[-1] * 100
            if len(monthly) >= 13:
                yoy_change = monthly['value'].pct_change(periods=12).iloc[-1] * 100
        except Exception:
            pass # Data might be too sparse or irregular for time resampling
            
        return {
            "current_value": current_val,
            "previous_value": previous_val,
            "abs_change": abs_change,
            "pct_change": pct_change,
            "mom_change": mom_change,
            "qoq_change": qoq_change,
            "yoy_change": yoy_change,
            "period_start": previous_time,
            "period_end": current_time
        }

    @classmethod
    def calculate_moving_average_and_volatility(cls, observations: List[Dict[str, Any]], window: int = 3) -> pd.DataFrame:
        df = cls._to_dataframe(observations)
        if len(df) < window:
            return df
        
        df[f'ma_{window}'] = df['value'].rolling(window=window).mean()
        df[f'volatility_{window}'] = df['value'].rolling(window=window).std()
        return df

    @classmethod
    def detect_anomalies_zscore(cls, observations: List[Dict[str, Any]], threshold: float = 3.0) -> List[Dict[str, Any]]:
        """Uses robust median absolute deviation (MAD) to detect outliers in small datasets."""
        df = cls._to_dataframe(observations)
        if len(df) < 5:
            return []
            
        median = df['value'].median()
        mad = np.median(np.abs(df['value'] - median))
        
        if mad == 0:
            mad = 1e-6 # prevent division by zero
            
        # 0.6745 is the 75th percentile of the standard normal distribution
        modified_z_scores = 0.6745 * (df['value'] - median) / mad
        
        df['anomaly_score'] = modified_z_scores.abs()
        df['is_anomaly'] = df['anomaly_score'] > threshold
        
        anomalies = df[df['is_anomaly']]
        
        result = []
        for timestamp, row in anomalies.iterrows():
            expected_min = median - (threshold * mad / 0.6745)
            expected_max = median + (threshold * mad / 0.6745)
            result.append({
                "timestamp": timestamp.isoformat(),
                "observed_value": row['value'],
                "baseline_median": median,
                "expected_range": f"[{expected_min:.2f}, {expected_max:.2f}]",
                "anomaly_score": row['anomaly_score'],
                "method": "Robust Z-Score"
            })
        return result

    @classmethod
    def detect_anomalies_isolation_forest(cls, observations: List[Dict[str, Any]], contamination: float = 0.05) -> List[Dict[str, Any]]:
        """Uses Isolation Forest for datasets > 30 points."""
        df = cls._to_dataframe(observations)
        if len(df) < 30:
            return []
            
        # For seasonal-aware anomaly detection, we add month as a feature to the Isolation Forest
        df['month'] = df.index.month
        
        # We fill missing values via interpolation
        df['value'] = df['value'].interpolate()
        
        X = df[['value', 'month']].values
        clf = IsolationForest(contamination=contamination, random_state=42)
        preds = clf.fit_predict(X)
        scores = clf.decision_function(X) # lower means more anomalous
        
        df['is_anomaly'] = preds == -1
        df['anomaly_score'] = -scores # invert so higher = more anomalous
        
        anomalies = df[df['is_anomaly']]
        median = df['value'].median()
        
        result = []
        for timestamp, row in anomalies.iterrows():
            result.append({
                "timestamp": timestamp.isoformat(),
                "observed_value": row['value'],
                "baseline_median": median,
                "expected_range": "Non-linear Boundary (Isolation Forest)",
                "anomaly_score": row['anomaly_score'],
                "method": "Seasonal-aware Isolation Forest"
            })
        return result
