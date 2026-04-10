from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.engine.mentor import MentorEngine
from app.engine.progress_tracker import (
    compute_mastery_score,
    update_streak,
    update_strengths_weaknesses,
)
from app.models.curriculum import CurriculumWeek
from app.models.progress import QuizAttempt
from app.models.user import LearnerState

router = APIRouter()

engine = MentorEngine()


class QuizRequest(BaseModel):
    user_id: int
    week_number: int | None = None  # None = current week
    question_type: str = "micro_quiz"  # micro_quiz/spaced_repetition


class QuizQuestion(BaseModel):
    question: str
    week_number: int
    question_type: str
    difficulty: float


class QuizAnswer(BaseModel):
    user_id: int
    week_number: int
    question: str
    answer: str
    question_type: str = "micro_quiz"


class QuizEvaluation(BaseModel):
    score: float
    feedback: str
    misconceptions: list[str]
    correct: bool


@router.post("/generate", response_model=QuizQuestion)
async def generate_quiz(req: QuizRequest, db: DbSession):
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == req.user_id))
    week_num = req.week_number or state.current_week

    week = await db.scalar(
        select(CurriculumWeek).where(CurriculumWeek.week_number == week_num)
    )

    question = await engine.generate_quiz(
        week=week,
        learner_state=state,
        question_type=req.question_type,
    )

    return QuizQuestion(
        question=question,
        week_number=week_num,
        question_type=req.question_type,
        difficulty=state.adaptive_difficulty,
    )


@router.post("/evaluate", response_model=QuizEvaluation)
async def evaluate_answer(req: QuizAnswer, db: DbSession):
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == req.user_id))

    week = await db.scalar(
        select(CurriculumWeek).where(CurriculumWeek.week_number == req.week_number)
    )

    evaluation = await engine.evaluate_quiz_answer(
        question=req.question,
        answer=req.answer,
        week=week,
        learner_state=state,
    )

    # Save attempt
    attempt = QuizAttempt(
        user_id=req.user_id,
        week_id=week.id,
        question_text=req.question,
        user_answer=req.answer,
        ai_evaluation=evaluation,
        question_type=req.question_type,
    )
    db.add(attempt)

    # Update misconceptions in learner state
    if evaluation.get("misconceptions"):
        existing = state.misconceptions or {}
        for m in evaluation["misconceptions"]:
            key = m.lower().replace(" ", "_")[:50]
            existing[key] = {
                "description": m,
                "week": req.week_number,
                "count": existing.get(key, {}).get("count", 0) + 1,
            }
        state.misconceptions = existing

    # Update progress tracking
    update_streak(state)
    state.overall_mastery_score = await compute_mastery_score(db, req.user_id)
    await update_strengths_weaknesses(db, state)

    await db.commit()

    return QuizEvaluation(
        score=evaluation["score"],
        feedback=evaluation["feedback"],
        misconceptions=evaluation.get("misconceptions", []),
        correct=evaluation["score"] >= 0.7,
    )
