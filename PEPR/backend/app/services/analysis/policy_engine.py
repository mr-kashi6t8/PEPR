from typing import Dict, Any, List
from app.models.policy import PolicyTarget, PolicyActual, PolicyGap

class PolicyEngine:
    """
    Mathematical engine that evaluates actual economic performance against official government policy targets,
    scoring the gap dynamically based on configurable rules.
    """
    
    @staticmethod
    def calculate_gap(target: PolicyTarget, actual: PolicyActual, historical_gaps: List[PolicyGap] = None) -> PolicyGap:
        """
        Calculates gap value, percentage, status (POSITIVE/NEGATIVE/NEUTRAL), and engine score.
        Uses Economist Logic for tolerances.
        """
        if historical_gaps is None:
            historical_gaps = []
            
        gap_value = actual.actual_value - target.target_value
        
        if target.target_value == 0:
            # Handle divide by zero edge case
            gap_percentage = 0.0 if gap_value == 0 else (100.0 if gap_value > 0 else -100.0)
        else:
            # Formula strictly as requested: ((Actual - Target) / Target) * 100
            gap_percentage = (gap_value / target.target_value) * 100.0
            
        # Determine Status (Economist Logic: allow a neutral tolerance band)
        if abs(gap_percentage) <= target.neutral_tolerance_percent:
            gap_status = "NEUTRAL"
        else:
            if target.higher_is_better:
                gap_status = "POSITIVE" if gap_percentage > 0 else "NEGATIVE"
            else:
                gap_status = "NEGATIVE" if gap_percentage > 0 else "POSITIVE"
                
        # Calculate Magnitude Score (0 to 10 scale based on percentage)
        magnitude_score = min(abs(gap_percentage) / 5.0, 10.0)
        
        # Calculate Persistence Score (does this target historically miss?)
        # A simple model: add 1.0 for every consecutive historical miss in the same direction
        persistence_score = 0.0
        if gap_status == "NEGATIVE":
            for hg in reversed(historical_gaps):
                if hg.gap_status == "NEGATIVE":
                    persistence_score += 1.0
                else:
                    break
        persistence_score = min(persistence_score, 5.0)
        
        # Engine Score Calculation
        confidence_multiplier = actual.data_quality_status * target.target_confidence
        
        # Base score formula incorporating all required dimensions
        engine_score = (magnitude_score + persistence_score) * target.importance_weight * confidence_multiplier
        
        # For negative gaps, the score indicates severity of the problem
        # For positive gaps, it indicates a success.
        if gap_status == "NEGATIVE":
            engine_score = engine_score # High score = Severe problem
        elif gap_status == "POSITIVE":
            engine_score = -engine_score # Negative score = Good (No problem)
        else:
            engine_score = 0.0 # Neutral
            
        return PolicyGap(
            target_id=target.id,
            actual_id=actual.id,
            gap_value=gap_value,
            gap_percentage=gap_percentage,
            gap_status=gap_status,
            engine_score=engine_score,
            magnitude_score=magnitude_score,
            persistence_score=persistence_score,
            analysis_notes=f"Calculated gap of {gap_percentage:.2f}%. Status: {gap_status}. Engine Score: {engine_score:.2f} (Confidence: {confidence_multiplier:.2f})"
        )
