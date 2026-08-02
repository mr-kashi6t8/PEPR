import pytest
import uuid
from datetime import datetime, timezone
from app.models.policy import PolicyTarget, PolicyActual
from app.services.analysis.policy_engine import PolicyEngine

def test_policy_engine_gap_calculation_positive():
    # Tax collection - Higher is better
    target = PolicyTarget(
        id=uuid.uuid4(),
        target_value=100.0,
        higher_is_better=True,
        neutral_tolerance_percent=1.0,
        importance_weight=1.0,
        target_confidence=1.0
    )
    
    actual = PolicyActual(
        id=uuid.uuid4(),
        actual_value=110.0,
        data_quality_status=1.0
    )
    
    gap = PolicyEngine.calculate_gap(target, actual)
    assert gap.gap_value == 10.0
    assert gap.gap_percentage == 10.0
    assert gap.gap_status == "POSITIVE"
    assert gap.engine_score < 0 # Negative score means "Good" (no problem)

def test_policy_engine_gap_calculation_negative():
    # Inflation - Higher is worse (higher_is_better = False)
    target = PolicyTarget(
        id=uuid.uuid4(),
        target_value=5.0,
        higher_is_better=False,
        neutral_tolerance_percent=1.0,
        importance_weight=2.0,
        target_confidence=1.0
    )
    
    actual = PolicyActual(
        id=uuid.uuid4(),
        actual_value=6.0, # Missed target by 1 unit
        data_quality_status=1.0
    )
    
    gap = PolicyEngine.calculate_gap(target, actual)
    assert gap.gap_value == 1.0
    assert gap.gap_percentage == 20.0
    assert gap.gap_status == "NEGATIVE"
    assert gap.engine_score > 0 # Positive score means Severe Problem
    
    # Engine score = (Magnitude + Persistence) * Importance * Confidence
    # Magnitude = 20.0 / 5.0 = 4.0
    # Score = (4.0 + 0) * 2.0 * 1.0 = 8.0
    assert gap.engine_score == 8.0

def test_policy_engine_neutral_tolerance():
    target = PolicyTarget(
        id=uuid.uuid4(),
        target_value=100.0,
        higher_is_better=True,
        neutral_tolerance_percent=2.0, # Allow 2% miss
        importance_weight=1.0,
        target_confidence=1.0
    )
    
    actual = PolicyActual(
        id=uuid.uuid4(),
        actual_value=99.0, # 1% miss
        data_quality_status=1.0
    )
    
    gap = PolicyEngine.calculate_gap(target, actual)
    assert gap.gap_status == "NEUTRAL"
    assert gap.engine_score == 0.0

def test_policy_engine_divide_by_zero():
    # If target is 0, we can't divide by zero
    target = PolicyTarget(
        id=uuid.uuid4(),
        target_value=0.0,
        higher_is_better=True,
        neutral_tolerance_percent=1.0,
        importance_weight=1.0,
        target_confidence=1.0
    )
    
    actual = PolicyActual(
        id=uuid.uuid4(),
        actual_value=5.0, 
        data_quality_status=1.0
    )
    
    gap = PolicyEngine.calculate_gap(target, actual)
    assert gap.gap_value == 5.0
    assert gap.gap_percentage == 100.0
    assert gap.gap_status == "POSITIVE"

def test_policy_engine_persistence():
    target = PolicyTarget(
        id=uuid.uuid4(),
        target_value=100.0,
        higher_is_better=True,
        neutral_tolerance_percent=1.0,
        importance_weight=1.0,
        target_confidence=1.0
    )
    
    actual = PolicyActual(id=uuid.uuid4(), actual_value=90.0, data_quality_status=1.0)
    
    class MockGap:
        def __init__(self, status):
            self.gap_status = status
            
    historical_gaps = [MockGap("NEGATIVE"), MockGap("NEGATIVE")]
    
    gap = PolicyEngine.calculate_gap(target, actual, historical_gaps)
    # Base magnitude = 10% miss / 5 = 2.0
    # Persistence = 2 (two previous misses)
    # Total = (2.0 + 2.0) * 1.0 * 1.0 = 4.0
    assert gap.persistence_score == 2.0
    assert gap.engine_score == 4.0
