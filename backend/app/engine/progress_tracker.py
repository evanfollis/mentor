"""
Progress tracking utilities — mastery score, streaks, velocity, strengths/weaknesses.

Called from quiz, gate, and progress endpoints to keep LearnerState up to date.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import CurriculumWeek
from app.models.progress import QuizAttempt, WeekProgress
from app.models.user import LearnerState


def update_streak(state: LearnerState) -> None:
    """Increment or reset streak based on last_active_at."""
    now = datetime.now(timezone.utc)

    if state.last_active_at is None:
        state.streak_days = 1
    else:
        days_gap = (now.date() - state.last_active_at.date()).days
        if days_gap == 0:
            pass  # same day
        elif days_gap == 1:
            state.streak_days += 1
        else:
            state.streak_days = 1  # reset

    state.last_active_at = now


async def compute_mastery_score(db: AsyncSession, user_id: int) -> float:
    """
    Weighted average of gate scores (60%) and quiz scores (40%).
    Uses all available data. Returns 0.0 if no data.
    """
    # Gate scores
    gate_result = await db.execute(
        select(func.avg(WeekProgress.gate_score)).where(
            WeekProgress.user_id == user_id,
            WeekProgress.gate_score.is_not(None),
        )
    )
    gate_avg = gate_result.scalar()

    # Quiz scores — stored as JSON, extract score field
    quiz_result = await db.execute(
        select(
            func.avg(cast(QuizAttempt.ai_evaluation["score"].astext, Float))
        ).where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.ai_evaluation["score"] != None,  # noqa: E711
        )
    )
    quiz_avg = quiz_result.scalar()

    if gate_avg is None and quiz_avg is None:
        return 0.0

    if gate_avg is None:
        return float(quiz_avg) * 100
    if quiz_avg is None:
        return float(gate_avg) * 100

    return (float(gate_avg) * 0.6 + float(quiz_avg) * 0.4) * 100


async def compute_study_velocity(db: AsyncSession, user_id: int) -> float:
    """Rolling average hours/week over the last 28 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=28)
    result = await db.execute(
        select(func.sum(WeekProgress.time_spent_minutes)).where(
            WeekProgress.user_id == user_id,
            WeekProgress.started_at >= cutoff,
        )
    )
    total_minutes = result.scalar() or 0
    return round(total_minutes / 60 / 4, 1)  # hours per week over 4 weeks


async def update_strengths_weaknesses(db: AsyncSession, state: LearnerState) -> None:
    """Derive strengths/weaknesses from quiz performance by week focus area."""
    # Get quiz scores joined with week focus
    result = await db.execute(
        select(
            CurriculumWeek.focus,
            func.avg(cast(QuizAttempt.ai_evaluation["score"].astext, Float)).label("avg_score"),
            func.count(QuizAttempt.id).label("count"),
        )
        .join(CurriculumWeek, CurriculumWeek.id == QuizAttempt.week_id)
        .where(QuizAttempt.user_id == state.user_id)
        .group_by(CurriculumWeek.focus)
        .having(func.count(QuizAttempt.id) >= 2)  # need at least 2 attempts
    )

    strengths = []
    weaknesses = []
    for row in result:
        if row.avg_score >= 0.8:
            strengths.append(row.focus)
        elif row.avg_score < 0.6:
            weaknesses.append(row.focus)

    # Also factor in gate scores
    gate_result = await db.execute(
        select(
            CurriculumWeek.focus,
            WeekProgress.gate_score,
        )
        .join(CurriculumWeek, CurriculumWeek.id == WeekProgress.week_id)
        .where(
            WeekProgress.user_id == state.user_id,
            WeekProgress.gate_score.is_not(None),
        )
    )

    for row in gate_result:
        if row.gate_score >= 0.85 and row.focus not in strengths:
            strengths.append(row.focus)
        elif row.gate_score < 0.6 and row.focus not in weaknesses:
            weaknesses.append(row.focus)

    state.strengths = strengths
    state.weaknesses = weaknesses
