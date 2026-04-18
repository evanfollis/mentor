from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.telemetry import emit_telemetry
from app.models.curriculum import CurriculumWeek
from app.models.session import (
    LearningArtifact,
    LearningOutcome,
    LearningSession,
    LearningSessionEvent,
)
from app.models.user import LearnerState


def _truncate(text: str, limit: int = 140) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


async def get_or_create_learning_session(
    db: AsyncSession,
    *,
    user_id: int,
    session_type: str,
    channel: str,
    mode: str,
    goal: str,
    week_id: int | None = None,
    legacy_conversation_id: int | None = None,
) -> LearningSession:
    query = select(LearningSession).where(
        LearningSession.user_id == user_id,
        LearningSession.session_type == session_type,
        LearningSession.channel == channel,
        LearningSession.mode == mode,
        LearningSession.week_id == week_id,
        LearningSession.legacy_conversation_id == legacy_conversation_id,
        LearningSession.status == "active",
    )
    session = await db.scalar(query)
    if session:
        return session

    session = LearningSession(
        user_id=user_id,
        session_type=session_type,
        channel=channel,
        mode=mode,
        goal=goal,
        week_id=week_id,
        legacy_conversation_id=legacy_conversation_id,
    )
    db.add(session)
    await db.flush()
    emit_telemetry(
        project="mentor",
        source="mentor.session_store",
        event_type="learning_session.created",
        session_id=str(session.id),
        details={
            "session_type": session_type,
            "channel": channel,
            "mode": mode,
            "week_id": week_id,
        },
    )
    return session


async def append_session_event(
    db: AsyncSession,
    session: LearningSession,
    *,
    event_type: str,
    actor: str,
    summary: str,
    payload: dict | None = None,
) -> LearningSessionEvent:
    event = LearningSessionEvent(
        session_id=session.id,
        event_type=event_type,
        actor=actor,
        summary=_truncate(summary, 300),
        payload=payload or {},
    )
    db.add(event)
    session.last_event_at = datetime.now(timezone.utc)
    await db.flush()
    emit_telemetry(
        project="mentor",
        source="mentor.session_store",
        event_type=f"learning_session_event.{event_type}",
        session_id=str(session.id),
        details={
            "actor": actor,
            "summary": event.summary,
        },
    )
    return event


async def record_artifact(
    db: AsyncSession,
    session: LearningSession,
    *,
    artifact_type: str,
    title: str,
    storage_pointer: str | None = None,
    summary: str = "",
    payload: dict | None = None,
) -> LearningArtifact:
    artifact = LearningArtifact(
        session_id=session.id,
        artifact_type=artifact_type,
        title=title,
        storage_pointer=storage_pointer,
        summary=summary,
        payload=payload or {},
    )
    db.add(artifact)
    await db.flush()
    emit_telemetry(
        project="mentor",
        source="mentor.session_store",
        event_type=f"learning_artifact.{artifact_type}",
        session_id=str(session.id),
        details={
            "title": title,
            "storage_pointer": storage_pointer,
        },
    )
    return artifact


async def record_outcome(
    db: AsyncSession,
    session: LearningSession,
    *,
    outcome_type: str,
    summary: str,
    payload: dict | None = None,
    confidence: float | None = None,
) -> LearningOutcome:
    outcome = LearningOutcome(
        session_id=session.id,
        outcome_type=outcome_type,
        summary=summary,
        payload=payload or {},
        confidence=confidence,
    )
    db.add(outcome)
    await db.flush()
    emit_telemetry(
        project="mentor",
        source="mentor.session_store",
        event_type=f"learning_outcome.{outcome_type}",
        session_id=str(session.id),
        level="warn" if outcome_type in {"gate_result", "artifact_review"} else "info",
        details={
            "summary": summary,
            "confidence": confidence,
        },
    )
    return outcome


async def update_reentry_snapshot(
    session: LearningSession,
    *,
    current_thesis: str,
    next_action: str,
    relevant_artifacts: list[str] | None = None,
    unresolved_outcomes: list[str] | None = None,
) -> None:
    session.reentry_snapshot = {
        "current_thesis": current_thesis,
        "next_action": next_action,
        "relevant_artifacts": relevant_artifacts or [],
        "unresolved_outcomes": unresolved_outcomes or [],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    emit_telemetry(
        project="mentor",
        source="mentor.session_store",
        event_type="learning_session.reentry_updated",
        session_id=str(session.id),
        details={
            "current_thesis": current_thesis,
            "next_action": next_action,
            "unresolved_outcomes": unresolved_outcomes or [],
        },
    )


async def build_context_package(
    db: AsyncSession,
    *,
    session: LearningSession | None,
    learner_state: LearnerState | None,
    week: CurriculumWeek | None = None,
) -> dict:
    recent_events: list[str] = []
    if session:
        result = await db.execute(
            select(LearningSessionEvent)
            .where(LearningSessionEvent.session_id == session.id)
            .order_by(LearningSessionEvent.created_at.desc())
            .limit(8)
        )
        recent_events = [
            f"{event.event_type}: {event.summary}"
            for event in reversed(result.scalars().all())
        ]

    return {
        "session_goal": session.goal if session else "",
        "reentry_snapshot": session.reentry_snapshot if session else {},
        "recent_events": recent_events,
        "learner_state": {
            "current_week": learner_state.current_week if learner_state else None,
            "adaptive_difficulty": learner_state.adaptive_difficulty if learner_state else None,
            "strengths": learner_state.strengths if learner_state else [],
            "weaknesses": learner_state.weaknesses if learner_state else [],
            "misconceptions": learner_state.misconceptions if learner_state else {},
        },
        "week": {
            "week_number": week.week_number if week else None,
            "title": week.title if week else None,
            "focus": week.focus if week else None,
        },
    }
