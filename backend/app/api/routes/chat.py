from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.engine.mentor import MentorEngine
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

    # Get conversation history
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    history = result.scalars().all()

    # Generate response
    response_text = await engine.respond(
        mode=req.mode,
        message=req.message,
        history=[(m.role, m.content) for m in history[:-1]],  # exclude the just-added message
        learner_state=state,
        db=db,
    )

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
    )
    db.add(assistant_msg)
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

    async def generate():
        full_response = ""
        async for chunk in engine.stream_respond(
            mode=req.mode,
            message=req.message,
            history=[],
            learner_state=state,
            db=db,
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

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
