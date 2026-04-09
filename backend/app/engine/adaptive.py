"""
Adaptive difficulty adjustment based on student performance.

The adaptive_difficulty scalar (0.0-1.0) is used by the quiz generator
and explainer to calibrate content depth.
"""

from __future__ import annotations

from app.models.user import LearnerState


def adjust_difficulty(
    state: LearnerState,
    score: float,
    context: str = "quiz",
) -> float:
    """
    Adjust adaptive_difficulty based on a score.

    Uses different rates for different contexts:
    - quiz: small adjustments (0.02)
    - gate: larger adjustments (0.05)
    - checkpoint: significant adjustments (0.10)
    """
    rates = {
        "quiz": 0.02,
        "gate": 0.05,
        "checkpoint": 0.10,
    }
    rate = rates.get(context, 0.02)

    if score >= 0.8:
        delta = rate
    elif score >= 0.6:
        delta = 0.0
    else:
        delta = -rate

    new_difficulty = max(0.0, min(1.0, state.adaptive_difficulty + delta))
    state.adaptive_difficulty = new_difficulty
    return new_difficulty


def compute_bloom_level(
    week_progress_pct: float,
    adaptive_difficulty: float,
) -> str:
    """
    Determine the appropriate Bloom's taxonomy level for questions.

    week_progress_pct: how far through the week (0.0-1.0)
    adaptive_difficulty: student's current difficulty level
    """
    # Combined signal: progress through week + overall difficulty
    combined = (week_progress_pct * 0.6) + (adaptive_difficulty * 0.4)

    if combined < 0.2:
        return "remember"
    elif combined < 0.35:
        return "understand"
    elif combined < 0.50:
        return "apply"
    elif combined < 0.70:
        return "analyze"
    elif combined < 0.85:
        return "evaluate"
    return "create"
