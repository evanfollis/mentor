from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models.curriculum import Checkpoint, CurriculumPhase, CurriculumWeek

router = APIRouter()


class WeekSummary(BaseModel):
    id: int
    week_number: int
    title: str
    focus: str
    estimated_hours: int
    is_high_roi: bool

    model_config = {"from_attributes": True}


class WeekDetail(BaseModel):
    id: int
    week_number: int
    title: str
    focus: str
    required_resources: dict
    build_tasks: dict
    artifact_spec: dict
    gate_questions: dict
    estimated_hours: int
    is_high_roi: bool
    phase_name: str

    model_config = {"from_attributes": True}


class PhaseResponse(BaseModel):
    id: int
    name: str
    description: str
    order: int
    weeks: list[WeekSummary]

    model_config = {"from_attributes": True}


@router.get("/phases", response_model=list[PhaseResponse])
async def list_phases(db: DbSession):
    result = await db.execute(
        select(CurriculumPhase)
        .options(selectinload(CurriculumPhase.weeks))
        .order_by(CurriculumPhase.order)
    )
    return result.scalars().all()


@router.get("/weeks/{week_number}", response_model=WeekDetail)
async def get_week(week_number: int, db: DbSession):
    result = await db.execute(
        select(CurriculumWeek)
        .options(selectinload(CurriculumWeek.phase))
        .where(CurriculumWeek.week_number == week_number)
    )
    week = result.scalar_one()
    return WeekDetail(
        id=week.id,
        week_number=week.week_number,
        title=week.title,
        focus=week.focus,
        required_resources=week.required_resources,
        build_tasks=week.build_tasks,
        artifact_spec=week.artifact_spec,
        gate_questions=week.gate_questions,
        estimated_hours=week.estimated_hours,
        is_high_roi=week.is_high_roi,
        phase_name=week.phase.name,
    )


@router.get("/checkpoints")
async def list_checkpoints(db: DbSession):
    result = await db.execute(select(Checkpoint).order_by(Checkpoint.after_week_number))
    return result.scalars().all()
