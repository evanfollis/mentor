import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.engine.mentor import MentorEngine
from app.engine.progress_tracker import compute_study_velocity, update_streak
from app.engine.session_store import (
    append_session_event,
    get_or_create_learning_session,
    record_artifact,
    record_outcome,
    update_reentry_snapshot,
)
from app.models.curriculum import CurriculumWeek
from app.models.progress import WeekProgress
from app.models.user import LearnerState

router = APIRouter()

engine = MentorEngine()


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
    update_streak(state)
    session = await get_or_create_learning_session(
        db,
        user_id=user_id,
        session_type="week_progress",
        channel="system",
        mode="week_progress",
        goal=f"Complete week {week_number}: {week.title}",
        week_id=week.id,
    )
    await append_session_event(
        db,
        session,
        event_type="observation",
        actor="system",
        summary=f"Started week {week_number}",
        payload={"week_number": week_number, "title": week.title},
    )
    await update_reentry_snapshot(
        session,
        current_thesis=f"Work through week {week_number}: {week.title}",
        next_action="Study the material and produce the required artifact.",
    )

    await db.commit()
    return {"status": "started", "week": week_number}


@router.post("/{user_id}/log-time")
async def log_study_time(user_id: int, minutes: int, db: DbSession):
    """Log study time for the current week."""
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == user_id))
    update_streak(state)

    progress = await db.scalar(
        select(WeekProgress).where(
            WeekProgress.user_id == user_id,
            WeekProgress.status == "in_progress",
        )
    )
    if progress:
        progress.time_spent_minutes += minutes
        session = await get_or_create_learning_session(
            db,
            user_id=user_id,
            session_type="week_progress",
            channel="system",
            mode="week_progress",
            goal=f"Complete week {state.current_week}",
            week_id=progress.week_id,
        )
        await append_session_event(
            db,
            session,
            event_type="observation",
            actor="user",
            summary=f"Logged {minutes} study minutes",
            payload={"minutes": minutes},
        )
        await record_outcome(
            db,
            session,
            outcome_type="study_time_logged",
            summary=f"Logged {minutes} study minutes",
            payload={"minutes": minutes},
        )

    state.study_velocity = await compute_study_velocity(db, user_id)

    await db.commit()
    return {"logged": minutes}


# --- Artifact endpoints ---

class ArtifactSubmission(BaseModel):
    url: str
    description: str = ""


class ArtifactReviewResponse(BaseModel):
    feedback: str
    artifact_status: str


class ArtifactStatusResponse(BaseModel):
    artifact_status: str
    artifact_url: str | None
    artifact_feedback: dict

    model_config = {"from_attributes": True}


@router.get("/{user_id}/weeks/{week_number}/artifact", response_model=ArtifactStatusResponse)
async def get_artifact_status(user_id: int, week_number: int, db: DbSession):
    week = await db.scalar(
        select(CurriculumWeek).where(CurriculumWeek.week_number == week_number)
    )
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")

    progress = await db.scalar(
        select(WeekProgress).where(
            WeekProgress.user_id == user_id,
            WeekProgress.week_id == week.id,
        )
    )
    if not progress:
        return ArtifactStatusResponse(
            artifact_status="not_started", artifact_url=None, artifact_feedback={}
        )

    return ArtifactStatusResponse(
        artifact_status=progress.artifact_status,
        artifact_url=progress.artifact_url,
        artifact_feedback=progress.artifact_feedback or {},
    )


@router.post("/{user_id}/weeks/{week_number}/artifact")
async def submit_artifact(user_id: int, week_number: int, req: ArtifactSubmission, db: DbSession):
    week = await db.scalar(
        select(CurriculumWeek).where(CurriculumWeek.week_number == week_number)
    )
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")

    progress = await db.scalar(
        select(WeekProgress).where(
            WeekProgress.user_id == user_id,
            WeekProgress.week_id == week.id,
        )
    )
    if not progress:
        raise HTTPException(status_code=400, detail="Week not started yet")

    progress.artifact_url = req.url
    progress.artifact_status = "submitted"
    progress.artifact_feedback = {"description": req.description} if req.description else {}
    session = await get_or_create_learning_session(
        db,
        user_id=user_id,
        session_type="artifact_review",
        channel="system",
        mode="artifact_review",
        goal=f"Submit and review the artifact for week {week_number}",
        week_id=week.id,
    )
    await append_session_event(
        db,
        session,
        event_type="artifact_created",
        actor="user",
        summary=f"Submitted artifact for week {week_number}",
        payload={"url": req.url, "description": req.description},
    )
    await record_artifact(
        db,
        session,
        artifact_type="submitted_artifact",
        title=f"Week {week_number} artifact",
        storage_pointer=req.url,
        summary=req.description,
        payload={"week_number": week_number},
    )
    await update_reentry_snapshot(
        session,
        current_thesis=f"Review artifact submission for week {week_number}.",
        next_action="Generate structured feedback for the submitted artifact.",
        relevant_artifacts=[req.url],
    )
    await db.commit()

    return {"status": "submitted", "artifact_url": req.url}


@router.post("/{user_id}/weeks/{week_number}/artifact/review", response_model=ArtifactReviewResponse)
async def review_artifact(user_id: int, week_number: int, db: DbSession):
    week = await db.scalar(
        select(CurriculumWeek).where(CurriculumWeek.week_number == week_number)
    )
    if not week:
        raise HTTPException(status_code=404, detail="Week not found")

    progress = await db.scalar(
        select(WeekProgress).where(
            WeekProgress.user_id == user_id,
            WeekProgress.week_id == week.id,
        )
    )
    if not progress or not progress.artifact_url:
        raise HTTPException(status_code=400, detail="No artifact submitted")

    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == user_id))

    artifact_spec = json.dumps(week.artifact_spec, indent=2) if week.artifact_spec else "No spec defined"
    description = (progress.artifact_feedback or {}).get("description", "")
    message = (
        f"Review this artifact for Week {week.week_number}: {week.title}.\n\n"
        f"## Artifact Specification\n{artifact_spec}\n\n"
        f"## Submitted Artifact\nURL: {progress.artifact_url}\n"
        + (f"Student's description: {description}\n\n" if description else "\n")
        + "Provide structured feedback covering: completeness, depth, accuracy, "
        f"and practicality. Include specific suggestions for improvement."
    )

    feedback = await engine.respond(
        mode="artifact_review",
        message=message,
        history=[],
        learner_state=state,
        db=db,
        week=week,
    )
    session = await get_or_create_learning_session(
        db,
        user_id=user_id,
        session_type="artifact_review",
        channel="system",
        mode="artifact_review",
        goal=f"Submit and review the artifact for week {week_number}",
        week_id=week.id,
    )

    progress.artifact_feedback = {
        "review": feedback,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    progress.artifact_status = "reviewed"
    await append_session_event(
        db,
        session,
        event_type="review_attached",
        actor="assistant",
        summary="Artifact review completed",
        payload={"feedback": feedback},
    )
    await record_outcome(
        db,
        session,
        outcome_type="artifact_review",
        summary="Artifact reviewed",
        payload={"feedback": feedback},
    )
    await update_reentry_snapshot(
        session,
        current_thesis=f"Artifact for week {week_number} has been reviewed.",
        next_action="Revise the artifact or move to gate preparation.",
        unresolved_outcomes=["Artifact revisions may still be needed"],
    )
    await db.commit()

    return ArtifactReviewResponse(feedback=feedback, artifact_status="reviewed")
