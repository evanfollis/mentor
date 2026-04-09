from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.progress import WeekProgress
from app.models.user import LearnerState

router = APIRouter()


class ProgressResponse(BaseModel):
    week_number: int
    status: str
    artifact_status: str
    gate_score: float | None
    gate_attempts: int
    time_spent_minutes: int

    model_config = {"from_attributes": True}


class LearnerStateResponse(BaseModel):
    current_week: int
    current_phase: int
    overall_mastery_score: float
    streak_days: int
    adaptive_difficulty: float
    strengths: list[str]
    weaknesses: list[str]

    model_config = {"from_attributes": True}


@router.get("/{user_id}/state", response_model=LearnerStateResponse)
async def get_learner_state(user_id: int, db: DbSession):
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == user_id))
    return state


@router.get("/{user_id}/weeks", response_model=list[ProgressResponse])
async def get_week_progress(user_id: int, db: DbSession):
    result = await db.execute(
        select(WeekProgress).where(WeekProgress.user_id == user_id)
    )
    rows = result.scalars().all()
    return rows


@router.post("/{user_id}/weeks/{week_number}/start")
async def start_week(user_id: int, week_number: int, db: DbSession):
    """Mark a week as in-progress."""
    from app.models.curriculum import CurriculumWeek

    week = await db.scalar(
        select(CurriculumWeek).where(CurriculumWeek.week_number == week_number)
    )
    progress = WeekProgress(
        user_id=user_id,
        week_id=week.id,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.add(progress)

    # Update learner state
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == user_id))
    state.current_week = week_number
    state.last_active_at = datetime.now(timezone.utc)

    await db.commit()
    return {"status": "started", "week": week_number}


@router.post("/{user_id}/log-time")
async def log_study_time(user_id: int, minutes: int, db: DbSession):
    """Log study time for the current week."""
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == user_id))
    state.last_active_at = datetime.now(timezone.utc)

    progress = await db.scalar(
        select(WeekProgress).where(
            WeekProgress.user_id == user_id,
            WeekProgress.status == "in_progress",
        )
    )
    if progress:
        progress.time_spent_minutes += minutes

    await db.commit()
    return {"logged": minutes}
