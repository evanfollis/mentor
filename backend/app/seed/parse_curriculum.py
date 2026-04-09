"""
Parse curriculum.md into structured database records.

Extracts phases, weeks, learning objectives, checkpoints, and gate questions
from the markdown curriculum document.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, engine, Base
from app.models.curriculum import Checkpoint, CurriculumPhase, CurriculumWeek, LearningObjective


# Structured curriculum data extracted from curriculum.md
PHASES = [
    {"name": "Control surfaces and mental models", "description": "Understand runtime surfaces, prompt contracts, tool boundaries, and coding-agent harness fundamentals.", "order": 1},
    {"name": "Orchestration and long-horizon work", "description": "Choosing orchestration patterns, managing context budgets, autonomous loops, and cross-runtime comparison.", "order": 2},
    {"name": "Evaluation, reliability, security", "description": "Eval as a subsystem, durable execution, security boundaries, governance and policy-as-code.", "order": 3},
    {"name": "Platform architecture and portfolio-quality proof", "description": "Cloud platform architecture, deployment patterns, capstone implementation, and presentation.", "order": 4},
]

WEEKS = [
    {
        "week_number": 1, "phase_order": 1, "title": "Modern AI system anatomy",
        "focus": "Understand current runtime surfaces: stateless calls, stateful responses, durable conversations, long-running background tasks, local coding agents, cloud agents, and where state actually lives.",
        "required_resources": {
            "items": [
                "OpenAI Responses migration guide",
                "OpenAI conversation-state guide",
                "OpenAI background-mode guide",
                "GPT-5.4 prompt guidance",
                "Claude Code overview",
                "Cursor Cloud Agents overview",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build the smallest possible system twice: once with manually chained state and once with platform-managed state."
            ]
        },
        "artifact_spec": {
            "name": "state_and_control_surfaces.md",
            "description": "A memo explaining where state, permissions, tools, and progress tracking live in each implementation."
        },
        "gate_questions": {
            "questions": [
                "Explain the difference between 'the model remembers,' 'the runtime persists,' and 'the app stores state,' with examples."
            ]
        },
        "estimated_hours": 9, "is_high_roi": False,
    },
    {
        "week_number": 2, "phase_order": 1, "title": "Prompt contracts, structure, and completion criteria",
        "focus": "Output contracts, variable separation, XML or structured sectioning, reasoning-effort selection, and completion criteria.",
        "required_resources": {
            "items": [
                "Anthropic prompt engineering materials",
                "Anthropic Console prompting tools",
                "OpenAI GPT-5.4 prompt guidance",
                "OpenAI prompt caching guide",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build one extraction/classification workflow in three versions: free-form, schema/structured-output, and prompt-plus-eval."
            ]
        },
        "artifact_spec": {
            "name": "prompt_contracts_and_failure_modes.md",
            "description": "Before/after prompts and observed failure classes."
        },
        "gate_questions": {
            "questions": [
                "Show one failure that looked like a prompt problem but was actually a missing completion contract.",
                "Show one failure that prompting alone could not solve."
            ]
        },
        "estimated_hours": 9, "is_high_roi": False,
    },
    {
        "week_number": 3, "phase_order": 1, "title": "Tool use versus retrieval versus MCP",
        "focus": "Internalize the difference between context, tools, resources, and prompts/workflows in MCP.",
        "required_resources": {
            "items": [
                "MCP intro/spec overview",
                "Anthropic tool-use docs",
                "OpenAI remote MCP guide",
                "Cursor MCP documentation map",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build the same research assistant twice: once with direct tool calls and once with MCP."
            ]
        },
        "artifact_spec": {
            "name": "tool_vs_mcp_decision_record.md",
            "description": "Document which capabilities should be plain app code, tool calls, MCP tools, MCP resources, or prompt templates."
        },
        "gate_questions": {
            "questions": [
                "Defend why each external capability belongs on one boundary and not the others."
            ]
        },
        "estimated_hours": 9, "is_high_roi": False,
    },
    {
        "week_number": 4, "phase_order": 1, "title": "Coding-agent harness fundamentals",
        "focus": "See how each runtime externalizes policy. Configure a single repo in Codex, Claude Code, and Cursor.",
        "required_resources": {
            "items": [
                "Codex CLI docs", "Codex config basics", "Codex skills", "Codex best practices",
                "Claude Code memory/settings/permissions/modes",
                "Cursor Rules/Skills/Hooks",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Configure a single repo in all three ecosystems with explicit policy, reusable skills, and at least one enforced post-action check."
            ]
        },
        "artifact_spec": {
            "name": "repo_agent_operating_model/",
            "description": "AGENTS.md or equivalent, at least one skill, at least one rule/instruction file, and at least one hook per environment."
        },
        "gate_questions": {
            "questions": [
                "Explain how Codex config.toml, Claude CLAUDE.md plus permission modes, and Cursor Rules/Hooks differ as control planes."
            ]
        },
        "estimated_hours": 10, "is_high_roi": True,
    },
    {
        "week_number": 5, "phase_order": 2, "title": "Choosing the right orchestration pattern",
        "focus": "Sequential, concurrent, group-chat/maker-checker, and handoff patterns. Use the lowest complexity that reliably solves the task.",
        "required_resources": {
            "items": [
                "Azure AI agent orchestration patterns",
                "OpenAI Agents SDK overview",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build one problem in increasing complexity: direct model call, single agent with tools, then one multi-agent pattern."
            ]
        },
        "artifact_spec": {
            "name": "orchestration_pattern_tradeoffs.md",
            "description": "Latency, complexity, failure modes, and why the more complex version did or did not earn its cost."
        },
        "gate_questions": {
            "questions": [
                "Identify one situation where multi-agent design is architectural theater.",
                "Identify one situation where multi-agent design is justified by specialization, security boundaries, or parallelism."
            ]
        },
        "estimated_hours": 9, "is_high_roi": False,
    },
    {
        "week_number": 6, "phase_order": 2, "title": "Context budgets, compaction, memory, and long-running trajectories",
        "focus": "Decide what gets cached, summarized, compacted, persisted externally, or discarded for long-running tasks.",
        "required_resources": {
            "items": [
                "OpenAI conversation-state and background-mode materials",
                "OpenAI compaction-related materials",
                "Anthropic prompt caching and extended-thinking docs",
                "Cursor dynamic-context-discovery post",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build a long-running task that exceeds one context window. Decide what gets cached, summarized, compacted, persisted, or discarded."
            ]
        },
        "artifact_spec": {
            "name": "context_budget_plan.md",
            "description": "Token budget, compaction rules, memory strategy, and explicit loss modes."
        },
        "gate_questions": {
            "questions": [
                "Explain what information must survive compression, what can be regenerated, and what should never have been in the live context."
            ]
        },
        "estimated_hours": 10, "is_high_roi": True,
    },
    {
        "week_number": 7, "phase_order": 2, "title": "Long-horizon coding agents and autonomous loops",
        "focus": "Making an agent persist, verify, retry, and stop only when 'done' is truly defined.",
        "required_resources": {
            "items": [
                "Codex prompting guide",
                "GPT-5.4 prompt guidance",
                "Claude Code subagents and hooks",
                "Cursor Cloud Agents and Automations",
                "CursorBench",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build a coding task requiring planning, editing, running, fixing, and reporting. Run it locally and in cloud/background."
            ]
        },
        "artifact_spec": {
            "name": "autonomous_loop_design.md",
            "description": "Design document plus trace logs from at least two runs."
        },
        "gate_questions": {
            "questions": [
                "Show how you prevented premature stopping, infinite tool loops, and silent failure."
            ]
        },
        "estimated_hours": 9, "is_high_roi": False,
    },
    {
        "week_number": 8, "phase_order": 2, "title": "Cross-runtime comparison capstone",
        "focus": "Run the same nontrivial repo task in Claude Code, Codex, and Cursor. Score each runtime.",
        "required_resources": {
            "items": [
                "All prior runtime documentation",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Run the same nontrivial repo task in all three runtimes. Score on correctness, iteration behavior, observability, recovery, effort, and harness overhead."
            ]
        },
        "artifact_spec": {
            "name": "runtime_comparison_report.md",
            "description": "Comparative report across runtimes with evidence-based conclusions."
        },
        "gate_questions": {
            "questions": [
                "Which runtime would you use for solo coding, team coding, secure internal execution, and unattended maintenance? Support with evidence."
            ]
        },
        "estimated_hours": 10, "is_high_roi": False,
    },
    {
        "week_number": 9, "phase_order": 3, "title": "Evaluation as a first-class subsystem",
        "focus": "Build an eval set that scores final outputs, intermediate tool choices, and policy compliance separately.",
        "required_resources": {
            "items": [
                "OpenAI eval guides and best practices",
                "OpenAI eval cookbook materials",
                "Anthropic eval-oriented docs",
                "CursorBench",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build an eval set for one of your earlier systems with dataset, graders, pass/fail thresholds, and regression report."
            ]
        },
        "artifact_spec": {
            "name": "eval_harness/",
            "description": "Dataset, graders, pass/fail thresholds, and a regression report."
        },
        "gate_questions": {
            "questions": [
                "Demonstrate a regression you would have missed with spot checks."
            ]
        },
        "estimated_hours": 10, "is_high_roi": True,
    },
    {
        "week_number": 10, "phase_order": 3, "title": "Reliability engineering and durable execution",
        "focus": "Redesign one agent to survive retries, external failures, and long delays without losing progress.",
        "required_resources": {
            "items": [
                "AWS Generative AI Lens (reliability and cost sections)",
                "Google well-architected core principles",
                "Temporal workflow/durable execution docs",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Redesign one agent with Temporal. Build a working prototype that survives an induced failure."
            ]
        },
        "artifact_spec": {
            "name": "durable_agent_blueprint.md",
            "description": "Blueprint plus working prototype surviving induced failure."
        },
        "gate_questions": {
            "questions": [
                "Explain which failures are handled by the model, the agent harness, the workflow engine, and the platform."
            ]
        },
        "estimated_hours": 10, "is_high_roi": False,
    },
    {
        "week_number": 11, "phase_order": 3, "title": "Security boundaries and adversarial reality",
        "focus": "Threat-model an agent system against prompt injection, over-permissioned tools, supply-chain compromise, data exfiltration, and memory poisoning.",
        "required_resources": {
            "items": [
                "OWASP LLM/GenAI Top 10",
                "OWASP prompt-injection guidance",
                "Cursor agent security guide",
                "Claude Code permission guidance",
                "AWS controlled-autonomy principle",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Threat-model one of your agent systems. Include concrete mitigations and one live red-team test."
            ]
        },
        "artifact_spec": {
            "name": "agent_threat_model.md",
            "description": "Threat model with concrete mitigations and one live red-team test."
        },
        "gate_questions": {
            "questions": [
                "Show where deterministic controls sit outside the model and why."
            ]
        },
        "estimated_hours": 10, "is_high_roi": True,
    },
    {
        "week_number": 12, "phase_order": 3, "title": "Governance, policy-as-code, and enterprise readiness",
        "focus": "Build a minimal governance package: risk tiering, approval gates, data-use policy, logging, eval thresholds, incident response, rollback.",
        "required_resources": {
            "items": [
                "NIST AI RMF + Generative AI Profile",
                "Microsoft AI-agent adoption/governance guidance",
                "OpenAI governed-agents cookbook",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build a governance package with risk tiering, approval gates, data-use policy, logging requirements, eval thresholds, incident response, and rollback criteria."
            ]
        },
        "artifact_spec": {
            "name": "governed_agent_playbook/",
            "description": "Complete governance package with all required components."
        },
        "gate_questions": {
            "questions": [
                "What evidence would legal, security, or an audit function ask for before approving this system? Point to files, not intentions."
            ]
        },
        "estimated_hours": 10, "is_high_roi": False,
    },
    {
        "week_number": 13, "phase_order": 4, "title": "Cloud and platform architecture for AI systems",
        "focus": "Design a multi-tenant AI platform supporting chat/research, coding agent, governed workflow, and retrieval-heavy analyst workloads.",
        "required_resources": {
            "items": [
                "AWS Generative AI Lens",
                "Google Well-Architected Framework + AI/ML perspective",
                "Azure AI strategy/adoption material",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Design a multi-tenant AI platform supporting at least four workloads."
            ]
        },
        "artifact_spec": {
            "name": "ai_platform_reference_architecture.md",
            "description": "Identity boundaries, model gateway, tool registry, state store, vector/retrieval layer, observability, and policy layer."
        },
        "gate_questions": {
            "questions": [
                "Explain how the platform survives model churn and vendor churn."
            ]
        },
        "estimated_hours": 10, "is_high_roi": True,
    },
    {
        "week_number": 14, "phase_order": 4, "title": "Deployment patterns: local, managed, self-hosted, Kubernetes",
        "focus": "Deployment decision memo covering local agent, vendor-managed, hybrid remote tool execution, and self-hosted worker pool.",
        "required_resources": {
            "items": [
                "Kubernetes production guidance",
                "AI Gateway Working Group announcement",
                "Cursor self-hosted pools and security docs",
                "Claude Managed Agents",
                "OpenAI background/computer-use guidance",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Create a deployment decision memo covering all four deployment patterns."
            ]
        },
        "artifact_spec": {
            "name": "deployment_decision_matrix.md",
            "description": "Where code, secrets, tool execution, model inference, and audit logs live in each pattern."
        },
        "gate_questions": {
            "questions": [
                "Answer where code, secrets, tool execution, model inference, and audit logs live in each deployment pattern."
            ]
        },
        "estimated_hours": 9, "is_high_roi": False,
    },
    {
        "week_number": 15, "phase_order": 4, "title": "Capstone implementation",
        "focus": "Build a capstone with explicit state, tools, policy, evals, and observability. Architecturally legible.",
        "required_resources": {
            "items": [
                "All prior vendor docs and frameworks as design review checklist",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Build a capstone system: governed investment-research agent, coding-agent platform layer, internal knowledge copilot, or durable document intelligence workflow."
            ]
        },
        "artifact_spec": {
            "name": "capstone_system/",
            "description": "Working system that someone else can run, inspect, and understand its constraints."
        },
        "gate_questions": {
            "questions": [
                "Can someone else run, inspect, and understand the constraints of your system?"
            ]
        },
        "estimated_hours": 12, "is_high_roi": False,
    },
    {
        "week_number": 16, "phase_order": 4, "title": "Hardening, teardown, and presentation",
        "focus": "Teardown of capstone: re-run evals, threat-model updates, cost estimates, operational runbooks, two presentations.",
        "required_resources": {
            "items": [
                "Cloud architecture frameworks",
                "AI governance frameworks",
            ]
        },
        "build_tasks": {
            "tasks": [
                "Teardown capstone. Re-run evals, update threat model, estimate costs, write runbooks.",
                "Produce technical architecture review and executive narrative presentations."
            ]
        },
        "artifact_spec": {
            "name": "final_architecture_review.md",
            "description": "Architecture review document and short slide outline."
        },
        "gate_questions": {
            "questions": [
                "Can you explain this system differently to an engineer, a platform lead, and a risk/governance stakeholder without changing the underlying truth?"
            ]
        },
        "estimated_hours": 10, "is_high_roi": False,
    },
]

CHECKPOINTS = [
    {
        "after_week_number": 4,
        "description": "You should have one repo workable by Claude Code, Codex, and Cursor with explicit local policy, reusable skills, and at least one enforced post-action check.",
        "success_criteria": {
            "criteria": [
                "Repo configured for all three runtimes",
                "Explicit local policy in each",
                "At least one reusable skill",
                "At least one enforced post-action check",
            ]
        },
    },
    {
        "after_week_number": 8,
        "description": "You should have a genuine view on harness design: what belongs in prompt, skills, hooks, rules, config, environment, and workflow engine.",
        "success_criteria": {
            "criteria": [
                "Can articulate harness design principles",
                "Understands prompt vs. skills vs. hooks vs. rules vs. config boundaries",
                "Has evidence-based runtime preferences",
            ]
        },
    },
    {
        "after_week_number": 12,
        "description": "You should be able to explain why most AI safety failures in practice are solved by architecture, not model alignment alone.",
        "success_criteria": {
            "criteria": [
                "Can explain architectural solutions to safety failures",
                "Understands scoped permissions, workflow design, evaluation, monitoring, and policy enforcement",
                "Has a working governance package",
            ]
        },
    },
]

LEARNING_OBJECTIVES = [
    # Week 1
    {"week_number": 1, "description": "Understand stateless vs stateful vs durable conversation patterns", "bloom_level": "understand", "concept_tags": ["state", "runtime", "conversations"]},
    {"week_number": 1, "description": "Build a system with manually chained state", "bloom_level": "apply", "concept_tags": ["state", "implementation"]},
    {"week_number": 1, "description": "Compare platform-managed vs application-managed state", "bloom_level": "analyze", "concept_tags": ["state", "architecture"]},
    # Week 2
    {"week_number": 2, "description": "Design effective prompt contracts with output schemas", "bloom_level": "create", "concept_tags": ["prompts", "contracts", "structured-output"]},
    {"week_number": 2, "description": "Identify prompt failures vs system failures", "bloom_level": "analyze", "concept_tags": ["prompts", "debugging", "failure-modes"]},
    # Week 3
    {"week_number": 3, "description": "Distinguish between tools, resources, and prompts in MCP", "bloom_level": "understand", "concept_tags": ["MCP", "tools", "resources"]},
    {"week_number": 3, "description": "Make boundary decisions for external capabilities", "bloom_level": "evaluate", "concept_tags": ["MCP", "architecture", "boundaries"]},
    # Week 4
    {"week_number": 4, "description": "Configure coding agent policy across runtimes", "bloom_level": "apply", "concept_tags": ["codex", "claude-code", "cursor", "policy"]},
    {"week_number": 4, "description": "Compare control plane approaches across runtimes", "bloom_level": "evaluate", "concept_tags": ["control-planes", "comparison"]},
    # Week 5
    {"week_number": 5, "description": "Select appropriate orchestration complexity", "bloom_level": "evaluate", "concept_tags": ["orchestration", "complexity", "patterns"]},
    {"week_number": 5, "description": "Identify architectural theater vs justified complexity", "bloom_level": "analyze", "concept_tags": ["orchestration", "multi-agent"]},
    # Week 6
    {"week_number": 6, "description": "Design context budget strategies for long-running tasks", "bloom_level": "create", "concept_tags": ["context", "compaction", "memory"]},
    {"week_number": 6, "description": "Classify information by survival requirements", "bloom_level": "analyze", "concept_tags": ["context", "compression", "persistence"]},
    # Week 7
    {"week_number": 7, "description": "Build autonomous agent loops with proper termination", "bloom_level": "create", "concept_tags": ["autonomous", "loops", "agents"]},
    {"week_number": 7, "description": "Prevent premature stopping and infinite loops", "bloom_level": "apply", "concept_tags": ["reliability", "termination", "safety"]},
    # Week 8
    {"week_number": 8, "description": "Conduct evidence-based runtime comparison", "bloom_level": "evaluate", "concept_tags": ["comparison", "runtimes", "evidence"]},
    # Week 9
    {"week_number": 9, "description": "Build evaluation harnesses with graders and regression detection", "bloom_level": "create", "concept_tags": ["evaluation", "testing", "regression"]},
    # Week 10
    {"week_number": 10, "description": "Design durable agent workflows that survive failures", "bloom_level": "create", "concept_tags": ["durability", "temporal", "reliability"]},
    # Week 11
    {"week_number": 11, "description": "Threat-model AI agent systems", "bloom_level": "analyze", "concept_tags": ["security", "threat-modeling", "adversarial"]},
    {"week_number": 11, "description": "Implement deterministic controls outside the model", "bloom_level": "apply", "concept_tags": ["security", "guardrails", "permissions"]},
    # Week 12
    {"week_number": 12, "description": "Build governance packages for enterprise AI systems", "bloom_level": "create", "concept_tags": ["governance", "policy", "compliance"]},
    # Week 13
    {"week_number": 13, "description": "Design multi-tenant AI platform architectures", "bloom_level": "create", "concept_tags": ["platform", "multi-tenant", "architecture"]},
    # Week 14
    {"week_number": 14, "description": "Create deployment decision frameworks", "bloom_level": "evaluate", "concept_tags": ["deployment", "kubernetes", "infrastructure"]},
    # Week 15
    {"week_number": 15, "description": "Build a portfolio-quality capstone system", "bloom_level": "create", "concept_tags": ["capstone", "portfolio", "integration"]},
    # Week 16
    {"week_number": 16, "description": "Present systems to different stakeholder audiences", "bloom_level": "evaluate", "concept_tags": ["communication", "presentation", "stakeholders"]},
]


async def seed_curriculum():
    """Seed the database with the full curriculum."""
    async with async_session() as db:
        # Check if already seeded
        existing = await db.scalar(select(CurriculumPhase).limit(1))
        if existing:
            print("Curriculum already seeded, skipping.")
            return

        # Create phases
        phase_map = {}
        for p in PHASES:
            phase = CurriculumPhase(**p)
            db.add(phase)
            await db.flush()
            phase_map[p["order"]] = phase.id

        # Create weeks
        week_map = {}
        for w in WEEKS:
            week = CurriculumWeek(
                phase_id=phase_map[w["phase_order"]],
                week_number=w["week_number"],
                title=w["title"],
                focus=w["focus"],
                required_resources=w["required_resources"],
                build_tasks=w["build_tasks"],
                artifact_spec=w["artifact_spec"],
                gate_questions=w["gate_questions"],
                estimated_hours=w["estimated_hours"],
                is_high_roi=w["is_high_roi"],
            )
            db.add(week)
            await db.flush()
            week_map[w["week_number"]] = week.id

        # Create checkpoints
        for c in CHECKPOINTS:
            checkpoint = Checkpoint(**c)
            db.add(checkpoint)

        # Create learning objectives
        for obj in LEARNING_OBJECTIVES:
            lo = LearningObjective(
                week_id=week_map[obj["week_number"]],
                description=obj["description"],
                bloom_level=obj["bloom_level"],
                concept_tags=obj["concept_tags"],
            )
            db.add(lo)

        await db.commit()
        print(f"Seeded {len(PHASES)} phases, {len(WEEKS)} weeks, {len(CHECKPOINTS)} checkpoints, {len(LEARNING_OBJECTIVES)} learning objectives.")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_curriculum()


if __name__ == "__main__":
    asyncio.run(main())
