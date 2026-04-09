"""
SM-2 Spaced Repetition Algorithm implementation.

After each review, the ease factor and interval are adjusted based on
the student's response quality (0-5 scale, mapped from quiz scores).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import ConceptCard


def sm2_update(card: ConceptCard, quality: int) -> ConceptCard:
    """
    Apply SM-2 algorithm to update card scheduling.

    quality: 0-5 rating
        0-1: complete blackout
        2: incorrect but recognized correct answer
        3: correct with serious difficulty
        4: correct with some hesitation
        5: perfect response
    """
    if quality < 3:
        # Reset on failure
        card.repetitions = 0
        card.interval_days = 1
    else:
        if card.repetitions == 0:
            card.interval_days = 1
        elif card.repetitions == 1:
            card.interval_days = 6
        else:
            card.interval_days = round(card.interval_days * card.ease_factor)

        card.repetitions += 1

    # Update ease factor (minimum 1.3)
    card.ease_factor = max(
        1.3,
        card.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02),
    )

    card.last_reviewed_at = datetime.now(timezone.utc)
    card.next_review_at = datetime.now(timezone.utc) + timedelta(days=card.interval_days)

    return card


def score_to_quality(score: float) -> int:
    """Convert a 0.0-1.0 quiz score to SM-2 quality rating (0-5)."""
    if score >= 0.95:
        return 5
    elif score >= 0.8:
        return 4
    elif score >= 0.6:
        return 3
    elif score >= 0.4:
        return 2
    elif score >= 0.2:
        return 1
    return 0


async def get_due_cards(db: AsyncSession, user_id: int, limit: int = 10) -> list[ConceptCard]:
    """Get concept cards due for review."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ConceptCard)
        .where(
            ConceptCard.user_id == user_id,
            ConceptCard.next_review_at <= now,
        )
        .order_by(ConceptCard.next_review_at)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_concept_cards(
    db: AsyncSession,
    user_id: int,
    week_id: int,
    concepts: list[dict],
) -> list[ConceptCard]:
    """
    Create concept cards for a completed week.

    concepts: list of {"concept": str, "question": str, "ideal_answer": str}
    """
    cards = []
    now = datetime.now(timezone.utc)
    for c in concepts:
        card = ConceptCard(
            user_id=user_id,
            week_id=week_id,
            concept=c["concept"],
            question=c["question"],
            ideal_answer=c["ideal_answer"],
            next_review_at=now + timedelta(days=1),
        )
        db.add(card)
        cards.append(card)

    await db.flush()
    return cards
