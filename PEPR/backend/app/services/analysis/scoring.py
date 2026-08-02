from typing import Dict, Any, Optional

def _normalize(val: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.0
    # Bound value
    val = max(min(val, max_val), min_val)
    return (val - min_val) / (max_val - min_val)

def deterministic_problem_score(
    severity: str,
    magnitude: float, 
    persistence: int, # in weeks
    affected_population: float, # e.g. millions
    indicator_importance: float, # 0 to 1
    news_acceleration: float, # 0 to 1
    policy_gap_magnitude: float,
    confidence: float, # 0 to 1
    data_quality: float # 0 to 1
) -> float:
    """
    Computes a deterministic priority score between 0 and 100 based on multiple factors.
    Weights are distributed as follows:
    - Severity Base (Categorical): 20%
    - Magnitude & Persistence: 20%
    - Affected Area / Population: 15%
    - Policy Gap Magnitude: 15%
    - Indicator Importance: 10%
    - News Acceleration: 10%
    - Data Confidence / Quality modifier: acts as a multiplier (up to 10% boost or penalty)
    """
    
    # Base Severity Score (0-20)
    severity_map = {
        "CRITICAL": 20.0,
        "HIGH": 15.0,
        "MEDIUM": 10.0,
        "LOW": 5.0
    }
    severity_score = severity_map.get(severity.upper(), 5.0)
    
    # Magnitude & Persistence (0-20)
    # Assume magnitude is normalized between 0-100 elsewhere, but if not we cap it
    mag_norm = _normalize(abs(magnitude), 0, 100) # assuming max 100% change
    pers_norm = _normalize(persistence, 0, 52) # up to 52 weeks (1 year)
    mag_pers_score = (mag_norm * 0.6 + pers_norm * 0.4) * 20.0
    
    # Affected Area (0-15)
    # Assume pop is in millions, normalize to max 240M (Pakistan approx pop)
    pop_norm = _normalize(affected_population, 0, 240)
    pop_score = pop_norm * 15.0
    
    # Policy Gap (0-15)
    gap_norm = _normalize(abs(policy_gap_magnitude), 0, 100) # % gap
    gap_score = gap_norm * 15.0
    
    # Indicator Importance (0-10)
    ind_score = _normalize(indicator_importance, 0, 1) * 10.0
    
    # News Acceleration (0-10)
    news_score = _normalize(news_acceleration, 0, 1) * 10.0
    
    # Base Total (Out of 90)
    base_total = severity_score + mag_pers_score + pop_score + gap_score + ind_score + news_score
    
    # Quality / Confidence Modifier (0-10)
    # Average of confidence and data quality
    quality_modifier = (confidence + data_quality) / 2.0
    quality_score = quality_modifier * 10.0
    
    final_score = base_total + quality_score
    
    # Ensure it's capped strictly 0 to 100
    return max(0.0, min(100.0, final_score))
