"""
MentorEngine — the central AI routing layer.

Routes requests to specialized prompt modes and manages context injection.
Uses Claude Sonnet for routine interactions, Opus for evaluations.
"""

from __future__ import annotations

from typing import AsyncIterator

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.engine.prompts import system_prompts
from app.models.curriculum import CurriculumWeek
from app.models.user import LearnerState


class MentorEngine:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    def _build_system_prompt(self, mode: str, learner_state: LearnerState | None, week: CurriculumWeek | None = None) -> str:
        base = system_prompts.BASE_SYSTEM_PROMPT
        mode_prompt = system_prompts.MODE_PROMPTS.get(mode, system_prompts.MODE_PROMPTS["freeform"])

        context_parts = [base, mode_prompt]

        if learner_state:
            context_parts.append(
                f"\n## Current Learner State\n"
                f"- Current week: {learner_state.current_week}\n"
                f"- Current phase: {learner_state.current_phase}\n"
                f"- Mastery score: {learner_state.overall_mastery_score}/100\n"
                f"- Adaptive difficulty: {learner_state.adaptive_difficulty:.2f}\n"
                f"- Streak: {learner_state.streak_days} days\n"
                f"- Strengths: {', '.join(learner_state.strengths) if learner_state.strengths else 'Not yet assessed'}\n"
                f"- Weaknesses: {', '.join(learner_state.weaknesses) if learner_state.weaknesses else 'Not yet assessed'}\n"
            )

            if learner_state.misconceptions:
                misconception_list = "\n".join(
                    f"  - {v['description']} (from week {v['week']}, seen {v['count']}x)"
                    for v in learner_state.misconceptions.values()
                )
                context_parts.append(
                    f"\n## Known Misconceptions (probe these when relevant)\n{misconception_list}\n"
                )

        if week:
            context_parts.append(
                f"\n## Current Week Context\n"
                f"- Week {week.week_number}: {week.title}\n"
                f"- Focus: {week.focus}\n"
                f"- High ROI week: {'Yes' if week.is_high_roi else 'No'}\n"
            )

        return "\n".join(context_parts)

    def _select_model(self, mode: str) -> str:
        if mode in ("gate_review", "artifact_review", "checkpoint"):
            return settings.model_evaluation
        return settings.model_routine

    async def respond(
        self,
        mode: str,
        message: str,
        history: list[tuple[str, str]],
        learner_state: LearnerState | None,
        db: AsyncSession,
        week: CurriculumWeek | None = None,
    ) -> str:
        # Fetch current week if not provided
        if not week and learner_state:
            week = await db.scalar(
                select(CurriculumWeek).where(
                    CurriculumWeek.week_number == learner_state.current_week
                )
            )

        system_prompt = self._build_system_prompt(mode, learner_state, week)
        model = self._select_model(mode)

        messages = []
        for role, content in history:
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        response = await self.client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )

        return response.content[0].text

    async def stream_respond(
        self,
        mode: str,
        message: str,
        history: list[tuple[str, str]],
        learner_state: LearnerState | None,
        db: AsyncSession,
        week: CurriculumWeek | None = None,
    ) -> AsyncIterator[str]:
        if not week and learner_state:
            week = await db.scalar(
                select(CurriculumWeek).where(
                    CurriculumWeek.week_number == learner_state.current_week
                )
            )

        system_prompt = self._build_system_prompt(mode, learner_state, week)
        model = self._select_model(mode)

        messages = []
        for role, content in history:
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        async with self.client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def generate_quiz(
        self,
        week: CurriculumWeek,
        learner_state: LearnerState,
        question_type: str = "micro_quiz",
    ) -> str:
        system = self._build_system_prompt("quiz", learner_state, week)

        prompt = (
            f"Generate a single {question_type} question for Week {week.week_number}: {week.title}.\n"
            f"Difficulty level: {learner_state.adaptive_difficulty:.2f} (0=easy, 1=hard).\n"
            f"Focus area: {week.focus}\n\n"
            f"Return ONLY the question text, nothing else."
        )

        response = await self.client.messages.create(
            model=settings.model_routine,
            max_tokens=500,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    async def evaluate_quiz_answer(
        self,
        question: str,
        answer: str,
        week: CurriculumWeek,
        learner_state: LearnerState,
    ) -> dict:
        system = self._build_system_prompt("quiz", learner_state, week)

        prompt = (
            f"Evaluate this quiz answer.\n\n"
            f"Question: {question}\n\n"
            f"Student's answer: {answer}\n\n"
            f"Respond in this exact JSON format:\n"
            f'{{"score": 0.0-1.0, "feedback": "...", "misconceptions": ["...", "..."]}}\n'
            f"The misconceptions array should list specific conceptual errors, or be empty if none."
        )

        response = await self.client.messages.create(
            model=settings.model_routine,
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        import json
        text = response.content[0].text.strip()
        # Handle potential markdown code blocks
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    async def evaluate_gate(
        self,
        week: CurriculumWeek,
        answers: dict[str, str],
        learner_state: LearnerState,
    ) -> dict:
        system = self._build_system_prompt("gate_review", learner_state, week)

        answers_text = "\n\n".join(
            f"**Question:** {q}\n**Answer:** {a}" for q, a in answers.items()
        )

        prompt = (
            f"Evaluate this gate review for Week {week.week_number}: {week.title}.\n\n"
            f"Gate questions and student answers:\n\n{answers_text}\n\n"
            f"Expected gate criteria from curriculum:\n{week.gate_questions}\n\n"
            f"Respond in this exact JSON format:\n"
            f'{{"overall_score": 0.0-1.0, '
            f'"question_scores": {{"question_text": {{"score": 0.0-1.0, "feedback": "..."}}}}, '
            f'"feedback": "overall assessment"}}'
        )

        response = await self.client.messages.create(
            model=settings.model_evaluation,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        import json
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
