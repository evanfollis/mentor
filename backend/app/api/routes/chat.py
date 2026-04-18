from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.engine.mentor import MentorEngine
from app.engine.session_store import (
    append_session_event,
    build_context_package,
    get_or_create_learning_session,
    update_reentry_snapshot,
)
from app.models.conversation import Conversation, Message
from app.models.user import LearnerState

router = APIRouter()

engine = MentorEngine()


class ChatRequest(BaseModel):
    user_id: int
    message: str
    conversation_id: int | None = None
    mode: str = "freeform"  # socratic/explain/quiz/freeform/gate_review


class ChatResponse(BaseModel):
    conversation_id: int
    response: str


class MessageResponse(BaseModel):
    role: str
    content: str

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: int
    mode: str
    channel: str
    preview: str
    message_count: int
    started_at: str
    last_message_at: str

    model_config = {"from_attributes": True}


class ConversationDetail(BaseModel):
    id: int
    mode: str
    channel: str
    messages: list[MessageResponse]

    model_config = {"from_attributes": True}


@router.get("/{user_id}/conversations", response_model=list[ConversationSummary])
async def list_conversations(user_id: int, db: DbSession):
    """List all conversations for a user, most recent first."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.last_message_at.desc())
    )
    conversations = result.scalars().all()

    summaries = []
    for conv in conversations:
        first_user_msg = next((m for m in conv.messages if m.role == "user"), None)
        preview = (first_user_msg.content[:80] + "...") if first_user_msg and len(first_user_msg.content) > 80 else (first_user_msg.content if first_user_msg else "")
        summaries.append(ConversationSummary(
            id=conv.id,
            mode=conv.mode,
            channel=conv.channel,
            preview=preview,
            message_count=len(conv.messages),
            started_at=conv.started_at.isoformat(),
            last_message_at=conv.last_message_at.isoformat(),
        ))
    return summaries


@router.get("/conversation/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: int, db: DbSession):
    """Load a full conversation with all messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one()
    return ConversationDetail(
        id=conv.id,
        mode=conv.mode,
        channel=conv.channel,
        messages=[MessageResponse(role=m.role, content=m.content) for m in conv.messages],
    )


@router.post("/send", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: DbSession):
    # Get or create conversation
    if req.conversation_id:
        conversation = await db.get(Conversation, req.conversation_id)
    else:
        conversation = Conversation(
            user_id=req.user_id,
            channel="web",
            mode=req.mode,
        )
        db.add(conversation)
        await db.flush()

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    await db.flush()

    # Get learner state for context
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == req.user_id))
    session = await get_or_create_learning_session(
        db,
        user_id=req.user_id,
        session_type="conversation",
        channel=conversation.channel,
        mode=req.mode,
        goal=f"Support mentor {req.mode} interaction",
        legacy_conversation_id=conversation.id,
    )
    await append_session_event(
        db,
        session,
        event_type="user_input",
        actor="user",
        summary=req.message,
        payload={"conversation_id": conversation.id},
    )

    # Get conversation history
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    history = result.scalars().all()

    context_package = await build_context_package(
        db,
        session=session,
        learner_state=state,
    )

    # Generate response
    response_text = await engine.respond(
        mode=req.mode,
        message=req.message,
        history=[(m.role, m.content) for m in history[:-1]],  # exclude the just-added message
        learner_state=state,
        db=db,
        context_package=context_package,
    )

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
    )
    db.add(assistant_msg)
    await append_session_event(
        db,
        session,
        event_type="assistant_response",
        actor="assistant",
        summary=response_text,
        payload={"conversation_id": conversation.id, "mode": req.mode},
    )
    await update_reentry_snapshot(
        session,
        current_thesis=f"Continue mentor interaction in {req.mode} mode for week {state.current_week if state else 'unknown'}.",
        next_action="Respond to the learner's most recent question or continue the active learning thread.",
    )

    # Update conversation timestamp
    from datetime import datetime, timezone
    conversation.last_message_at = datetime.now(timezone.utc)

    await db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        response=response_text,
    )


@router.post("/stream")
async def stream_message(req: ChatRequest, db: DbSession):
    """Stream a chat response using SSE."""
    state = await db.scalar(select(LearnerState).where(LearnerState.user_id == req.user_id))

    if req.conversation_id:
        conversation = await db.get(Conversation, req.conversation_id)
    else:
        conversation = Conversation(user_id=req.user_id, channel="web", mode=req.mode)
        db.add(conversation)
        await db.flush()

    user_msg = Message(conversation_id=conversation.id, role="user", content=req.message)
    db.add(user_msg)
    await db.commit()
    session = await get_or_create_learning_session(
        db,
        user_id=req.user_id,
        session_type="conversation",
        channel=conversation.channel,
        mode=req.mode,
        goal=f"Support mentor {req.mode} interaction",
        legacy_conversation_id=conversation.id,
    )
    await append_session_event(
        db,
        session,
        event_type="user_input",
        actor="user",
        summary=req.message,
        payload={"conversation_id": conversation.id},
    )
    await db.commit()
    context_package = await build_context_package(db, session=session, learner_state=state)

    async def generate():
        full_response = ""
        async for chunk in engine.stream_respond(
            mode=req.mode,
            message=req.message,
            history=[],
            learner_state=state,
            db=db,
            context_package=context_package,
        ):
            full_response += chunk
            yield f"data: {chunk}\n\n"

        # Save the full response
        async with db.begin():
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_response,
            )
            db.add(assistant_msg)
            await append_session_event(
                db,
                session,
                event_type="assistant_response",
                actor="assistant",
                summary=full_response,
                payload={"conversation_id": conversation.id, "mode": req.mode},
            )
            await update_reentry_snapshot(
                session,
                current_thesis=f"Continue mentor interaction in {req.mode} mode for week {state.current_week if state else 'unknown'}.",
                next_action="Resume the current conversation from the latest learner turn.",
            )

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
