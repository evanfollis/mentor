from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.engine.mentor import MentorEngine
from app.models.curriculum import CurriculumWeek
from app.models.progress import WeekProgress
from app.models.user import LearnerState

router = APIRouter()

engine = MentorEngine()


class GateAttemptRequest(BaseModel):
    user_id: int
    week_number: int
    answers: dict[str, str]  # {question_key: answer_text}


class GateResult(BaseModel):
    passed: bool
    overall_score: float
    question_scores: dict[str, dict]  # {question: {score, feedback}}
    feedback: str
    attempt_number: int


@router.get("/{user_id}/{week_number}/questions")
async def get_gate_questions(user_id: int, week_number: int, db: DbSession):
    week = await db.scalar(
        select(CurriculumWeek).where(CurriculumWeek.week_number == week_number)
    )
    return {"week": week_number, "questions": week.gate_questions}


@router.post("/attempt", response_model=GateResult)
async def attempt_gate(req: GateAttemptRequest, db: DbSession):
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == req.user_id))
    week = await db.scalar(
        select(CurriculumWeek).where(CurriculumWeek.week_number == req.week_number)
    )
    progress = await db.scalar(
        select(WeekProgress).where(
            WeekProgress.user_id == req.user_id,
            WeekProgress.week_id == week.id,
        )
    )

    # Evaluate via Claude
    result = await engine.evaluate_gate(
        week=week,
        answers=req.answers,
        learner_state=state,
    )

    # Update progress
    progress.gate_attempts += 1
    progress.gate_score = result["overall_score"]

    passed = result["overall_score"] >= 0.75

    if passed:
        progress.status = "completed"
        progress.gate_passed_at = datetime.now(timezone.utc)
        progress.completed_at = datetime.now(timezone.utc)

        # Advance learner state
        if state.current_week == req.week_number:
            state.current_week = req.week_number + 1

        # Adjust adaptive difficulty upward on pass
        state.adaptive_difficulty = min(1.0, state.adaptive_difficulty + 0.05)
    else:
        progress.status = "gate_pending"
        # Adjust adaptive difficulty downward on fail
        state.adaptive_difficulty = max(0.0, state.adaptive_difficulty - 0.05)

    await db.commit()

    return GateResult(
        passed=passed,
        overall_score=result["overall_score"],
        question_scores=result["question_scores"],
        feedback=result["feedback"],
        attempt_number=progress.gate_attempts,
    )
