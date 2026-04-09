from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.user import LearnerState, UserProfile

router = APIRouter()


class UserCreate(BaseModel):
    name: str
    email: str
    timezone: str = "America/New_York"
    slack_user_id: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    timezone: str
    current_week: int
    current_phase: int

    model_config = {"from_attributes": True}


@router.post("/register", response_model=UserResponse)
async def register(data: UserCreate, db: DbSession):
    user = UserProfile(
        name=data.name,
        email=data.email,
        timezone=data.timezone,
        slack_user_id=data.slack_user_id,
    )
    db.add(user)
    await db.flush()

    state = LearnerState(user_id=user.id)
    db.add(state)
    await db.commit()
    await db.refresh(user)
    await db.refresh(state)

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        timezone=user.timezone,
        current_week=state.current_week,
        current_phase=state.current_phase,
    )


@router.get("/me/{user_id}", response_model=UserResponse)
async def get_me(user_id: int, db: DbSession):
    user = await db.get(UserProfile, user_id)
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == user_id))
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        timezone=user.timezone,
        current_week=state.current_week,
        current_phase=state.current_phase,
    )
