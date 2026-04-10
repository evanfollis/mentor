from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.engine.progress_tracker import update_streak
from app.engine.spaced_repetition import get_due_cards, sm2_update
from app.models.progress import ConceptCard
from app.models.user import LearnerState

router = APIRouter()


class DueCard(BaseModel):
    id: int
    concept: str
    question: str

    model_config = {"from_attributes": True}


class DueCardsResponse(BaseModel):
    cards: list[DueCard]
    total_due: int


class CardReviewRequest(BaseModel):
    card_id: int
    self_score: int  # 0-5 SM-2 quality rating


class CardReviewResponse(BaseModel):
    ideal_answer: str
    next_review_at: str
    interval_days: int
    ease_factor: float


@router.get("/{user_id}/due", response_model=DueCardsResponse)
async def get_due(user_id: int, db: DbSession, limit: int = 10):
    cards = await get_due_cards(db, user_id, limit)

    now = datetime.now(timezone.utc)
    total_due = await db.scalar(
        select(func.count(ConceptCard.id)).where(
            ConceptCard.user_id == user_id,
            ConceptCard.next_review_at <= now,
        )
    )

    return DueCardsResponse(
        cards=[DueCard.model_validate(c) for c in cards],
        total_due=total_due or 0,
    )


@router.post("/{user_id}/review", response_model=CardReviewResponse)
async def review_card(user_id: int, req: CardReviewRequest, db: DbSession):
    card = await db.get(ConceptCard, req.card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")

    if not 0 <= req.self_score <= 5:
        raise HTTPException(status_code=400, detail="self_score must be 0-5")

    sm2_update(card, req.self_score)

    # Update streak
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == user_id))
    if state:
        update_streak(state)

    await db.commit()

    return CardReviewResponse(
        ideal_answer=card.ideal_answer,
        next_review_at=card.next_review_at.isoformat(),
        interval_days=card.interval_days,
        ease_factor=card.ease_factor,
    )
