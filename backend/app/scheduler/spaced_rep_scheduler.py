"""
Generates spaced repetition concept cards when a week is completed.

Called by the gate evaluation flow after a gate is passed.
Uses Claude to generate concept cards from the week's material.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.engine.mentor import MentorEngine
from app.engine.spaced_repetition import create_concept_cards
from app.models.curriculum import CurriculumWeek
from app.models.user import LearnerState

logger = logging.getLogger(__name__)

mentor = MentorEngine()


async def generate_week_concept_cards(
    db: AsyncSession,
    user_id: int,
    week: CurriculumWeek,
    learner_state: LearnerState,
) -> int:
    """
    Generate spaced repetition cards for a completed week.
    Returns the number of cards created.
    """
    prompt = (
        f"Generate 5-8 spaced repetition flashcards for Week {week.week_number}: {week.title}.\n"
        f"Focus: {week.focus}\n\n"
        f"Each card should test a distinct, important concept from this week.\n"
        f"Calibrate to the student's level (difficulty: {learner_state.adaptive_difficulty:.2f}).\n\n"
        f"Respond in this exact JSON format:\n"
        f'[{{"concept": "short concept name", "question": "the question to ask", "ideal_answer": "what a correct answer should contain"}}]\n'
        f"Return ONLY the JSON array."
    )

    try:
        response = await mentor.client.messages.create(
            model=settings.model_routine,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        concepts = json.loads(text)
        cards = await create_concept_cards(db, user_id, week.id, concepts)
        await db.commit()

        logger.info(f"Generated {len(cards)} concept cards for user {user_id}, week {week.week_number}")
        return len(cards)

    except Exception as e:
        logger.error(f"Failed to generate concept cards: {e}")
        return 0
