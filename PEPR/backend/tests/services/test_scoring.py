import pytest
from app.services.analysis.scoring import deterministic_problem_score

def test_deterministic_problem_score_critical():
    score = deterministic_problem_score(
        severity="CRITICAL", # 20
        magnitude=100.0, # (1*0.6) * 20 = 12
        persistence=52, # (1*0.4) * 20 = 8 -> Total mag_pers = 20
        affected_population=240, # 15
        indicator_importance=1.0, # 10
        news_acceleration=1.0, # 10
        policy_gap_magnitude=100.0, # 15
        confidence=1.0, # avg=1 -> quality = 10
        data_quality=1.0 
    )
    assert score == 100.0

def test_deterministic_problem_score_low():
    score = deterministic_problem_score(
        severity="LOW", # 5
        magnitude=0.0, # 0
        persistence=0, # 0
        affected_population=0, # 0
        indicator_importance=0.0, # 0
        news_acceleration=0.0, # 0
        policy_gap_magnitude=0.0, # 0
        confidence=0.0, # 0
        data_quality=0.0 
    )
    assert score == 5.0

def test_deterministic_problem_score_medium():
    score = deterministic_problem_score(
        severity="MEDIUM", # 10
        magnitude=50.0, # (0.5*0.6) * 20 = 6
        persistence=26, # (0.5*0.4) * 20 = 4 -> Total = 10
        affected_population=120, # 7.5
        indicator_importance=0.5, # 5
        news_acceleration=0.5, # 5
        policy_gap_magnitude=50.0, # 7.5
        confidence=0.5,
        data_quality=0.5 # quality = 5
    )
    assert score == 50.0

def test_deterministic_problem_score_bounds():
    # Should strictly be bounded 0-100
    score = deterministic_problem_score(
        severity="CRITICAL", 
        magnitude=9999.0, 
        persistence=999, 
        affected_population=9999, 
        indicator_importance=99.0, 
        news_acceleration=99.0, 
        policy_gap_magnitude=999.0, 
        confidence=9.0, 
        data_quality=9.0 
    )
    assert score == 100.0
