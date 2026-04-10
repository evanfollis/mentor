"""
Scheduling engine for proactive mentor outreach.

Runs as a background asyncio task inside the FastAPI process.
Computes a daily agenda for each user and dispatches via Slack.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.engine.mentor import MentorEngine
from app.engine.spaced_repetition import get_due_cards
from app.models.curriculum import CurriculumWeek
from app.models.progress import WeekProgress
from app.models.user import LearnerState, UserProfile

logger = logging.getLogger(__name__)

mentor = MentorEngine()

# Track whether today's agenda has been sent
_last_briefing_date: str | None = None
_last_evening_date: str | None = None


async def send_slack_message(channel: str, text: str, blocks: list | None = None):
    """Send a message via Slack Web API."""
    if not settings.slack_bot_token:
        logger.info(f"Slack not configured. Would send: {text[:100]}")
        return

    import httpx
    async with httpx.AsyncClient() as client:
        payload = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
            json=payload,
        )


async def compute_daily_agenda(user_id: int) -> list[dict]:
    """Compute today's agenda items for a user."""
    agenda = []

    async with async_session() as db:
        state = await db.scalar(
            select(LearnerState).where(LearnerState.user_id == user_id)
        )
        if not state:
            return agenda

        user = await db.get(UserProfile, user_id)
        week = await db.scalar(
            select(CurriculumWeek).where(
                CurriculumWeek.week_number == state.current_week
            )
        )

        # 1. Spaced repetition cards due
        due_cards = await get_due_cards(db, user_id, limit=5)
        if due_cards:
            agenda.append({
                "type": "spaced_rep",
                "text": f"You have {len(due_cards)} concept cards due for review.",
                "cards": [{"concept": c.concept, "question": c.question} for c in due_cards],
            })

        # 2. Behind-schedule detection
        if user.created_at:
            days_elapsed = (datetime.now(timezone.utc) - user.created_at).days
            expected_week = min(16, (days_elapsed // 7) + 1)
            if state.current_week < expected_week:
                behind_by = expected_week - state.current_week
                agenda.append({
                    "type": "behind_schedule",
                    "text": f"You're {behind_by} week(s) behind the suggested pace. Consider dedicating extra time this week.",
                })

        # 3. Current week status
        wp = await db.scalar(
            select(WeekProgress).where(
                WeekProgress.user_id == user_id,
                WeekProgress.week_id == week.id,
            )
        )

        if not wp:
            agenda.append({
                "type": "start_week",
                "text": f"Week {week.week_number}: *{week.title}* hasn't been started yet. Ready to begin?",
            })
        elif wp.status == "in_progress" and wp.artifact_status in ("not_started", "draft"):
            agenda.append({
                "type": "artifact_reminder",
                "text": f"Don't forget to work on your artifact: *{week.artifact_spec.get('name', 'N/A')}*",
            })
        elif wp.status == "in_progress" and wp.artifact_status in ("submitted", "reviewed", "approved") and not wp.gate_passed_at:
            agenda.append({
                "type": "gate_reminder",
                "text": f"Your artifact is ready! Time to attempt the gate review for Week {week.week_number}.",
            })

        # 4. Streak maintenance
        if state.streak_days > 0 and state.last_active_at:
            hours_since = (datetime.now(timezone.utc) - state.last_active_at).total_seconds() / 3600
            if hours_since > 20:
                agenda.append({
                    "type": "streak_warning",
                    "text": f"Your {state.streak_days}-day streak is at risk! A quick quiz keeps it alive.",
                })

        # 5. High-ROI week callout
        if week and week.is_high_roi:
            agenda.append({
                "type": "high_roi",
                "text": f"Week {week.week_number} is a high-ROI week. Over-index here — this material separates advanced users from architects.",
            })

    return agenda


async def send_morning_briefing():
    """Send morning briefing to all users via Slack."""
    async with async_session() as db:
        result = await db.execute(select(UserProfile))
        users = result.scalars().all()

    for user in users:
        if not user.slack_user_id:
            continue

        agenda = await compute_daily_agenda(user.id)
        if not agenda:
            continue

        lines = ["*Good morning! Here's your AI Architect study agenda:*\n"]
        for item in agenda:
            lines.append(f"• {item['text']}")

        # Add a micro-lesson teaser
        async with async_session() as db:
            state = await db.scalar(
                select(LearnerState).where(LearnerState.user_id == user.id)
            )
            week = await db.scalar(
                select(CurriculumWeek).where(
                    CurriculumWeek.week_number == state.current_week
                )
            )

        try:
            micro_lesson = await mentor.respond(
                mode="micro_lesson",
                message=f"Write a 5-minute micro-lesson on a key concept from Week {week.week_number}: {week.title}. Focus: {week.focus}",
                history=[],
                learner_state=state,
                db=None,
                week=week,
            )
            lines.append(f"\n---\n*Today's Micro-Lesson:*\n{micro_lesson[:1500]}")
        except Exception as e:
            logger.error(f"Failed to generate micro-lesson: {e}")

        await send_slack_message(
            channel=user.slack_user_id,
            text="\n".join(lines),
        )
        logger.info(f"Sent morning briefing to user {user.id}")


async def send_evening_review():
    """Send evening review prompt."""
    async with async_session() as db:
        result = await db.execute(select(UserProfile))
        users = result.scalars().all()

    for user in users:
        if not user.slack_user_id:
            continue

        async with async_session() as db:
            state = await db.scalar(
                select(LearnerState).where(LearnerState.user_id == user.id)
            )

        text = (
            f"*Evening check-in:*\n"
            f"How did studying go today? Quick summary:\n"
            f"• Current: Week {state.current_week}\n"
            f"• Streak: {state.streak_days} days\n\n"
            f"Use `/quiz` for a quick review before bed, or `/study` to see what's next."
        )

        await send_slack_message(channel=user.slack_user_id, text=text)


async def start_scheduler():
    """
    Main scheduler loop. Runs inside the FastAPI process.

    Checks every 5 minutes. Sends morning briefing at ~8am and evening review at ~8pm
    in the user's timezone (defaulting to America/New_York for now).
    """
    global _last_briefing_date, _last_evening_date

    logger.info("Scheduler loop started")

    while True:
        try:
            now = datetime.now(timezone.utc)
            # Simple timezone offset for Eastern Time (UTC-4 or -5)
            eastern_hour = (now.hour - 4) % 24
            today = now.strftime("%Y-%m-%d")

            # Morning briefing: 8-9 AM Eastern
            if 8 <= eastern_hour < 9 and _last_briefing_date != today:
                logger.info("Sending morning briefings")
                await send_morning_briefing()
                _last_briefing_date = today

            # Evening review: 8-9 PM Eastern
            if 20 <= eastern_hour < 21 and _last_evening_date != today:
                logger.info("Sending evening reviews")
                await send_evening_review()
                _last_evening_date = today

        except Exception as e:
            logger.error(f"Scheduler error: {e}")

        await asyncio.sleep(300)  # Check every 5 minutes
