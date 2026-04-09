from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CurriculumPhase(Base):
    __tablename__ = "curriculum_phases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer)

    weeks: Mapped[list[CurriculumWeek]] = relationship(back_populates="phase")


class CurriculumWeek(Base):
    __tablename__ = "curriculum_weeks"

    id: Mapped[int] = mapped_column(primary_key=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("curriculum_phases.id"))
    week_number: Mapped[int] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(300))
    focus: Mapped[str] = mapped_column(Text)
    required_resources: Mapped[dict] = mapped_column(JSONB, default=dict)
    build_tasks: Mapped[dict] = mapped_column(JSONB, default=dict)
    artifact_spec: Mapped[dict] = mapped_column(JSONB, default=dict)
    gate_questions: Mapped[dict] = mapped_column(JSONB, default=dict)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=9)
    is_high_roi: Mapped[bool] = mapped_column(Boolean, default=False)

    phase: Mapped[CurriculumPhase] = relationship(back_populates="weeks")
    objectives: Mapped[list[LearningObjective]] = relationship(back_populates="week")


class LearningObjective(Base):
    __tablename__ = "learning_objectives"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("curriculum_weeks.id"))
    description: Mapped[str] = mapped_column(Text)
    bloom_level: Mapped[str] = mapped_column(String(20))  # remember/understand/apply/analyze/evaluate/create
    concept_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    week: Mapped[CurriculumWeek] = relationship(back_populates="objectives")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[int] = mapped_column(primary_key=True)
    after_week_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    success_criteria: Mapped[dict] = mapped_column(JSONB, default=dict)
