"""
Slack bot integration using slack-bolt.

Provides:
- /study — start a study session, show current week info
- /quiz — get a quick quiz question
- /progress — show current stats
- /ask <question> — ask the mentor anything
- /gate — show gate questions for current week
- Interactive quiz buttons for answering
- Thread-based conversations
"""

from __future__ import annotations

import asyncio
import json
import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.starlette.async_handler import AsyncSlackRequestHandler
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.engine.mentor import MentorEngine
from app.models.conversation import Conversation, Message
from app.models.curriculum import CurriculumWeek
from app.models.progress import WeekProgress
from app.models.user import LearnerState, UserProfile

logger = logging.getLogger(__name__)

mentor = MentorEngine()

slack_app = AsyncApp(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret,
)

handler = AsyncSlackRequestHandler(slack_app)


def _get_user_id_sync():
    """For now, return user ID 1. Will be replaced with Slack user lookup."""
    return 1


# -------------------------------------------------------------------
# /study — Show current week info and start a session
# -------------------------------------------------------------------
@slack_app.command("/study")
async def handle_study(ack, respond, command):
    await ack()

    async with async_session() as db:
        state = await db.scalar(
            select(LearnerState).where(LearnerState.user_id == 1)
        )
        week = await db.scalar(
            select(CurriculumWeek).where(
                CurriculumWeek.week_number == state.current_week
            )
        )

        resources = week.required_resources.get("items", [])
        resources_text = "\n".join(f"  • {r}" for r in resources[:6])

        build_tasks = week.build_tasks.get("tasks", [])
        tasks_text = "\n".join(f"  • {t}" for t in build_tasks)

        artifact = week.artifact_spec
        artifact_text = f"*{artifact.get('name', 'N/A')}*: {artifact.get('description', '')}"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Week {week.week_number}: {week.title}"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Focus:* {week.focus}"},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Required Reading:*\n{resources_text}"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Build Tasks:*\n{tasks_text}"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Artifact:* {artifact_text}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Your Stats:* Mastery {state.overall_mastery_score:.0f}% | Streak {state.streak_days}d | Difficulty {state.adaptive_difficulty:.0%}",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Quick Quiz"},
                        "action_id": "slack_quiz_start",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Ask a Question"},
                        "action_id": "slack_ask_start",
                    },
                ],
            },
        ]

        await respond(blocks=blocks, response_type="ephemeral")


# -------------------------------------------------------------------
# /quiz — Generate and deliver a quiz question
# -------------------------------------------------------------------
@slack_app.command("/quiz")
async def handle_quiz(ack, respond, command):
    await ack()
    await _send_quiz(respond)


async def _send_quiz(respond):
    async with async_session() as db:
        state = await db.scalar(
            select(LearnerState).where(LearnerState.user_id == 1)
        )
        week = await db.scalar(
            select(CurriculumWeek).where(
                CurriculumWeek.week_number == state.current_week
            )
        )

        question = await mentor.generate_quiz(
            week=week,
            learner_state=state,
            question_type="micro_quiz",
        )

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Quiz — Week {week.week_number}: {week.title}"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": question},
            },
            {
                "type": "input",
                "block_id": "quiz_answer_block",
                "dispatch_action": False,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "quiz_answer_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "Type your answer..."},
                },
                "label": {"type": "plain_text", "text": "Your Answer"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Submit Answer"},
                        "action_id": "quiz_submit",
                        "style": "primary",
                        "value": json.dumps({
                            "question": question,
                            "week_number": week.week_number,
                        }),
                    },
                ],
            },
        ]

        await respond(blocks=blocks, response_type="ephemeral")


# -------------------------------------------------------------------
# /progress — Show current stats
# -------------------------------------------------------------------
@slack_app.command("/progress")
async def handle_progress(ack, respond, command):
    await ack()

    async with async_session() as db:
        state = await db.scalar(
            select(LearnerState).where(LearnerState.user_id == 1)
        )
        week = await db.scalar(
            select(CurriculumWeek).where(
                CurriculumWeek.week_number == state.current_week
            )
        )

        # Get completed weeks count
        result = await db.execute(
            select(WeekProgress).where(
                WeekProgress.user_id == 1,
                WeekProgress.status == "completed",
            )
        )
        completed = len(result.scalars().all())

        progress_bar = "█" * completed + "░" * (16 - completed)

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Your Progress"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Current:* Week {state.current_week} — {week.title}\n"
                        f"*Phase:* {state.current_phase} / 4\n"
                        f"*Completed:* {completed} / 16 weeks\n"
                        f"*Progress:* `{progress_bar}`\n"
                        f"*Mastery:* {state.overall_mastery_score:.0f}%\n"
                        f"*Streak:* {state.streak_days} days\n"
                        f"*Difficulty:* {state.adaptive_difficulty:.0%}"
                    ),
                },
            },
        ]

        if state.strengths:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Strengths:* {', '.join(state.strengths)}"},
            })

        if state.weaknesses:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Areas to improve:* {', '.join(state.weaknesses)}"},
            })

        await respond(blocks=blocks, response_type="ephemeral")


# -------------------------------------------------------------------
# /ask <question> — Ask the mentor a freeform question
# -------------------------------------------------------------------
@slack_app.command("/ask")
async def handle_ask(ack, respond, command):
    await ack()

    question = command.get("text", "").strip()
    if not question:
        await respond(text="Usage: `/ask <your question>`", response_type="ephemeral")
        return

    async with async_session() as db:
        state = await db.scalar(
            select(LearnerState).where(LearnerState.user_id == 1)
        )

        # Create a conversation record
        conv = Conversation(user_id=1, channel="slack", mode="freeform")
        db.add(conv)
        await db.flush()

        user_msg = Message(conversation_id=conv.id, role="user", content=question)
        db.add(user_msg)
        await db.flush()

        response_text = await mentor.respond(
            mode="freeform",
            message=question,
            history=[],
            learner_state=state,
            db=db,
        )

        assistant_msg = Message(conversation_id=conv.id, role="assistant", content=response_text)
        db.add(assistant_msg)
        await db.commit()

    # Truncate for Slack's 3000 char limit per section
    if len(response_text) > 2900:
        response_text = response_text[:2900] + "\n\n_...response truncated. Continue on the web app._"

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Q:* {question}"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": response_text},
        },
    ]

    await respond(blocks=blocks, response_type="ephemeral")


# -------------------------------------------------------------------
# /gate — Show gate questions for current week
# -------------------------------------------------------------------
@slack_app.command("/gate")
async def handle_gate(ack, respond, command):
    await ack()

    async with async_session() as db:
        state = await db.scalar(
            select(LearnerState).where(LearnerState.user_id == 1)
        )
        week = await db.scalar(
            select(CurriculumWeek).where(
                CurriculumWeek.week_number == state.current_week
            )
        )

        questions = week.gate_questions.get("questions", [])
        questions_text = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Gate Review — Week {week.week_number}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{week.title}*\n\nAnswer these questions to advance:\n\n{questions_text}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_Use the web app at http://localhost:3000/gate-review to submit your full gate review with detailed answers._",
                },
            },
        ]

        await respond(blocks=blocks, response_type="ephemeral")


# -------------------------------------------------------------------
# Interactive action handlers
# -------------------------------------------------------------------
@slack_app.action("slack_quiz_start")
async def handle_quiz_start(ack, respond):
    await ack()
    await _send_quiz(respond)


@slack_app.action("slack_ask_start")
async def handle_ask_start(ack, respond):
    await ack()
    await respond(
        text="Type `/ask <your question>` to ask the mentor anything!",
        response_type="ephemeral",
    )


@slack_app.action("quiz_answer_input")
async def handle_quiz_input(ack):
    await ack()


@slack_app.action("quiz_submit")
async def handle_quiz_submit(ack, body, respond):
    await ack()

    # Extract answer from the state
    state_values = body.get("state", {}).get("values", {})
    answer = ""
    for block_id, block_data in state_values.items():
        for action_id, action_data in block_data.items():
            if action_id == "quiz_answer_input":
                answer = action_data.get("value", "")

    if not answer:
        await respond(text="Please type an answer before submitting.", response_type="ephemeral")
        return

    # Parse the question from the button value
    action = body["actions"][0]
    quiz_data = json.loads(action["value"])
    question = quiz_data["question"]
    week_number = quiz_data["week_number"]

    async with async_session() as db:
        learner_state = await db.scalar(
            select(LearnerState).where(LearnerState.user_id == 1)
        )
        week = await db.scalar(
            select(CurriculumWeek).where(CurriculumWeek.week_number == week_number)
        )

        evaluation = await mentor.evaluate_quiz_answer(
            question=question,
            answer=answer,
            week=week,
            learner_state=learner_state,
        )

    score = evaluation.get("score", 0)
    feedback = evaluation.get("feedback", "")
    misconceptions = evaluation.get("misconceptions", [])

    score_emoji = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"

    result_text = f"{score_emoji} *Score: {score * 100:.0f}%*\n\n{feedback}"
    if misconceptions:
        result_text += "\n\n*Watch out for:*\n" + "\n".join(f"• {m}" for m in misconceptions)

    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Q:* {question[:200]}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Your answer:* {answer[:500]}"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": result_text},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Another Quiz"},
                    "action_id": "slack_quiz_start",
                },
            ],
        },
    ]

    await respond(blocks=blocks, response_type="ephemeral")
