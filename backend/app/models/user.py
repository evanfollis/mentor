from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(300), unique=True)
    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")
    slack_user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    learner_state: Mapped[LearnerState | None] = relationship(back_populates="user", uselist=False)


class LearnerState(Base):
    __tablename__ = "learner_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), unique=True)
    current_week: Mapped[int] = mapped_column(Integer, default=1)
    current_phase: Mapped[int] = mapped_column(Integer, default=1)
    overall_mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    adaptive_difficulty: Mapped[float] = mapped_column(Float, default=0.5)
    study_velocity: Mapped[float] = mapped_column(Float, default=0.0)  # hours/week rolling avg
    strengths: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    weaknesses: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    misconceptions: Mapped[dict] = mapped_column(JSONB, default=dict)  # tracked misconceptions

    user: Mapped[UserProfile] = relationship(back_populates="learner_state")
