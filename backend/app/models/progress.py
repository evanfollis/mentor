from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WeekProgress(Base):
    __tablename__ = "week_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))
    week_id: Mapped[int] = mapped_column(ForeignKey("curriculum_weeks.id"))
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started/in_progress/gate_pending/completed
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0)
    artifact_status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started/draft/submitted/reviewed/approved
    artifact_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    artifact_feedback: Mapped[dict] = mapped_column(JSONB, default=dict)
    gate_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    gate_attempts: Mapped[int] = mapped_column(Integer, default=0)
    gate_passed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))
    week_id: Mapped[int] = mapped_column(ForeignKey("curriculum_weeks.id"))
    question_text: Mapped[str] = mapped_column(Text)
    user_answer: Mapped[str] = mapped_column(Text)
    ai_evaluation: Mapped[dict] = mapped_column(JSONB, default=dict)  # {score, feedback, misconceptions}
    question_type: Mapped[str] = mapped_column(String(30))  # gate/spaced_repetition/micro_quiz/checkpoint
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConceptCard(Base):
    __tablename__ = "concept_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))
    week_id: Mapped[int] = mapped_column(ForeignKey("curriculum_weeks.id"))
    concept: Mapped[str] = mapped_column(String(300))
    question: Mapped[str] = mapped_column(Text)
    ideal_answer: Mapped[str] = mapped_column(Text)
    # SM-2 algorithm fields
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
