# AI Architect-level Mastery Plan

The main design choice is this: I am treating Claude Code, Codex, Cursor, MCP, and cloud agent stacks as **different surfaces over the same deeper problems**: state, tool boundaries, orchestration, context management, evaluation, governance, and systems reliability. That is the right abstraction in April 2026 because the platforms are converging on similar primitives even as their product surfaces keep changing. OpenAI has centered new agent builds on the Responses API, Conversations, built-in tools, remote MCPs, compaction, background execution, and the Agents SDK, while the Assistants API is deprecated and scheduled to shut down on August 26, 2026. Anthropic has pushed Claude Code to GA, expanded hooks/subagents/settings/SDK capabilities, and launched Claude Managed Agents in public beta on April 8, 2026. Cursor has expanded from editor assistance into Cloud Agents, Automations, self-hosted pools, Rules, Skills, Hooks, and MCP-backed long-running workflows. ([OpenAI Developers][1])

I designed this as a **16-week build-first syllabus** for roughly **8–10 focused hours per week**. The point is not to finish a reading list. The point is to produce a sequence of artifacts that prove you can architect real AI systems: one small reliable agent, one governed multi-tool system, one coding-agent operating model, and one enterprise platform blueprint. The backbone of the syllabus is current official documentation from OpenAI, Anthropic, Cursor, AWS, Google Cloud, Azure, NIST, OWASP, Temporal, Kubernetes, and MCP itself. ([OpenAI Developers][2])

## How to use this syllabus

Every week has five outputs: **focus**, **required resources**, **build**, **artifact**, and **gate**. Do not move on because you “read the docs.” Move on only when the artifact exists and you can answer the gate questions without bluffing. When you feel tempted to keep exploring, force one concrete implementation. When you feel tempted to overcommit early, run one comparative experiment first. That cadence is the real curriculum. It is also consistent with the current vendor guidance, which keeps pushing builders toward explicit evals, controlled tool use, structured context, and production discipline instead of prompt cleverness alone. ([OpenAI Developers][3])

## Phase 1 — Control surfaces and mental models

### Week 1 — Modern AI system anatomy

Read the OpenAI Responses migration guide, conversation-state guide, background-mode guide, and GPT-5.4 prompt guidance; pair those with Claude Code overview and Cursor’s Cloud Agents overview. The point this week is to understand the current runtime surfaces: stateless calls, stateful responses, durable conversations, long-running background tasks, local coding agents, cloud agents, and where state actually lives. Build the smallest possible system twice: once with manually chained state and once with platform-managed state. Artifact: a memo called `state_and_control_surfaces.md` explaining where state, permissions, tools, and progress tracking live in each implementation. Gate: explain the difference between “the model remembers,” “the runtime persists,” and “the app stores state,” with examples. ([OpenAI Developers][1])

### Week 2 — Prompt contracts, structure, and completion criteria

Read Anthropic’s prompt engineering materials and Console prompting tools, plus OpenAI’s GPT-5.4 prompt guidance and prompt caching guide. Focus on output contracts, variable separation, XML or structured sectioning, reasoning-effort selection, and completion criteria. Build one extraction or classification workflow in three versions: free-form prompting, schema/structured-output style prompting, and prompt-plus-eval. Artifact: `prompt_contracts_and_failure_modes.md` with before/after prompts and observed failure classes. Gate: show one failure that looked like a prompt problem but was actually a missing completion contract, and one failure that prompting alone could not solve. ([Claude API Docs][4])

### Week 3 — Tool use versus retrieval versus MCP

Read the MCP intro/spec overview, Anthropic tool-use docs, OpenAI remote MCP guide, and Cursor MCP documentation map. The aim is to internalize the difference between context, tools, resources, and prompts/workflows in MCP. Build the same research assistant twice: once with direct tool calls and once with MCP. Artifact: `tool_vs_mcp_decision_record.md` documenting which capabilities should be plain app code, tool calls, MCP tools, MCP resources, or prompt templates. Gate: defend why each external capability belongs on one boundary and not the others. ([Claude API Docs][5])

### Week 4 — Coding-agent harness fundamentals

Read Codex CLI, Codex config basics, Codex skills, Codex best practices, Claude Code memory/settings/permissions/modes, and Cursor Rules/Skills/Hooks. Then configure a single repo in all three ecosystems. The goal is not feature tourism; it is to see how each runtime externalizes policy. Artifact: `repo_agent_operating_model/` containing `AGENTS.md` or equivalent, at least one skill, at least one rule or persistent instruction file, and at least one hook in each environment where practical. Gate: explain how Codex `config.toml`, Claude `CLAUDE.md` plus permission modes, and Cursor Rules/Hooks differ as control planes. ([OpenAI Developers][6])

**Checkpoint 1:** By the end of Week 4 you should have one repo that can be worked by Claude Code, Codex, and Cursor with explicit local policy, reusable skills, and at least one enforced post-action check. If you do not, you are still studying interfaces instead of learning architecture. ([OpenAI Developers][7])

## Phase 2 — Orchestration and long-horizon work

### Week 5 — Choosing the right orchestration pattern

Read Azure’s AI agent orchestration patterns and the OpenAI Agents SDK overview. Study sequential, concurrent, group-chat/maker-checker, and handoff patterns, but start from the Azure warning: use the lowest level of complexity that reliably solves the task. Build one problem in increasing complexity: direct model call, single agent with tools, then one multi-agent pattern. Artifact: `orchestration_pattern_tradeoffs.md` with latency, complexity, failure modes, and why the more complex version did or did not earn its cost. Gate: identify one situation where multi-agent design is architectural theater and one where it is justified by specialization, security boundaries, or parallelism. ([Microsoft Learn][8])

### Week 6 — Context budgets, compaction, memory, and long-running trajectories

Read OpenAI’s conversation-state, background-mode, and compaction-related materials; read Anthropic’s prompt caching and extended-thinking docs; read Cursor’s dynamic-context-discovery post. Build a long-running task that can exceed one context window and force yourself to decide what gets cached, summarized, compacted, persisted externally, or discarded. Artifact: `context_budget_plan.md` with a token budget, compaction rules, memory strategy, and explicit loss modes. Gate: explain what information must survive compression, what can be regenerated, and what should never have been in the live context in the first place. ([OpenAI Developers][9])

### Week 7 — Long-horizon coding agents and autonomous loops

Read the Codex prompting guide, GPT-5.4 prompt guidance, Claude Code subagents and hooks guidance, Cursor Cloud Agents and Automations, and CursorBench. This week is about making an agent persist, verify, retry, and stop only when “done” is truly defined. Build a coding task that requires planning, editing, running, fixing, and reporting; then run it locally and in a cloud/background setting. Artifact: `autonomous_loop_design.md` plus trace logs from at least two runs. Gate: show how you prevented premature stopping, infinite tool loops, and silent failure. ([OpenAI Developers][10])

### Week 8 — Cross-runtime comparison capstone

Run the same nontrivial repo task in Claude Code, Codex, and Cursor. Keep the task constant. Change only the runtime and minimal policy files. Score each run on correctness, iteration behavior, observability, recovery from failure, effort to configure, and how much of the “harness” you had to build yourself. Artifact: `runtime_comparison_report.md`. Gate: answer “Which runtime would I use for solo coding, team coding, secure internal execution, and unattended maintenance, and why?” with evidence instead of preference. ([Claude API Docs][11])

**Checkpoint 2:** By the end of Week 8 you should have a genuine view on harness design: what belongs in prompt, skills, hooks, rules, config, environment, and workflow engine. If you still frame these tools mainly as “smart IDEs,” you are under-abstracting the problem. ([Cursor][12])

## Phase 3 — Evaluation, reliability, security

### Week 9 — Evaluation as a first-class subsystem

Read OpenAI’s eval guides, evaluation best practices, and recent eval cookbook materials; pair that with Anthropic’s eval-oriented docs and CursorBench. Build an eval set for one of your earlier systems that scores final outputs, intermediate tool choices, and policy compliance separately. Artifact: `eval_harness/` with dataset, graders, pass/fail thresholds, and a regression report. Gate: demonstrate a regression you would have missed with spot checks. ([OpenAI Developers][3])

### Week 10 — Reliability engineering and durable execution

Read the AWS Generative AI Lens sections on reliability and cost, Google’s well-architected core principles, and Temporal’s workflow/durable execution docs. Then redesign one agent so it can survive retries, external failures, and long delays without losing progress. Ideally use Temporal for this week, because it forces explicit treatment of workflow state, retries, and resumability. Artifact: `durable_agent_blueprint.md` plus a working prototype that survives an induced failure. Gate: explain exactly which failures are handled by the model, which by the agent harness, which by the workflow engine, and which by the platform. ([AWS Documentation][13])

### Week 11 — Security boundaries and adversarial reality

Read OWASP’s LLM/GenAI Top 10 and prompt-injection guidance, Cursor’s agent security guide, Claude Code permission guidance, and AWS’s controlled-autonomy principle. Then threat-model one of your agent systems against prompt injection, over-permissioned tools, supply-chain compromise, data exfiltration, and memory poisoning. Artifact: `agent_threat_model.md` with concrete mitigations and one live red-team test. Gate: show where deterministic controls sit outside the model and why. ([OWASP][14])

### Week 12 — Governance, policy-as-code, and enterprise readiness

Read NIST AI RMF + Generative AI Profile, Microsoft’s AI-agent adoption/governance guidance, and OpenAI’s governed-agents cookbook. Build a minimal governance package: risk tiering, approval gates, data-use policy, logging requirements, evaluation thresholds, incident response, and rollback criteria. Artifact: `governed_agent_playbook/`. Gate: answer “What evidence would legal, security, or an audit function ask for before approving this system?” and point to files, not intentions. ([NIST][15])

**Checkpoint 3:** By the end of Week 12 you should be able to explain why most “AI safety” failures in practice are not solved by model alignment alone. They are solved by architecture: scoped permissions, workflow design, evaluation, monitoring, and policy enforcement. ([OWASP][14])

## Phase 4 — Platform architecture and portfolio-quality proof

### Week 13 — Cloud and platform architecture for AI systems

Read AWS’s Generative AI Lens, Google’s Well-Architected Framework plus AI/ML perspective, and Azure’s AI strategy/adoption material. Design a multi-tenant AI platform that can support at least four workloads: chat/research assistant, coding agent, governed internal workflow agent, and retrieval-heavy analyst agent. Artifact: `ai_platform_reference_architecture.md` with identity boundaries, model gateway strategy, tool registry, state store, vector/retrieval layer, observability, and policy layer. Gate: explain how the platform survives model churn and vendor churn. ([AWS Documentation][13])

### Week 14 — Deployment patterns: local, managed, self-hosted, Kubernetes

Read Kubernetes production guidance and the new AI Gateway Working Group announcement; read Cursor self-hosted pools, Cloud Agents, and security-network materials; read Claude Managed Agents and OpenAI’s background/computer-use guidance. Then create a deployment decision memo covering local agent, vendor-managed agent, hybrid remote tool execution, and self-hosted worker pool. Artifact: `deployment_decision_matrix.md`. Gate: answer where code, secrets, tool execution, model inference, and audit logs live in each pattern. ([Kubernetes][16])

### Week 15 — Capstone implementation

Choose one capstone that is strategically aligned with the work you want to be hired for. For you, I would choose one of these: a governed investment-research agent, a coding-agent platform layer, an internal knowledge-and-action copilot, or a durable multi-step document intelligence workflow. Build it with explicit state, tools, policy, evals, and observability. Artifact: the working system. Gate: someone else should be able to run it, inspect it, and understand its constraints. The standard here is not novelty; it is architectural legibility. Use the vendor docs and frameworks you have studied as your design review checklist. ([AWS Documentation][13])

### Week 16 — Hardening, teardown, and presentation

Spend the final week doing a teardown of your own capstone. Re-run evals, threat-model updates, cost estimates, and operational runbooks. Then produce two presentations: one technical architecture review and one executive narrative focused on risk, leverage, and rollout path. Artifact: `final_architecture_review.md` and a short slide outline. Gate: can you explain this system differently to an engineer, a platform lead, and a risk/governance stakeholder without changing the underlying truth? The cloud architecture frameworks and AI governance frameworks are especially useful here because they force you to present the same system through different evaluation lenses. ([AWS Documentation][13])

## Portfolio outputs you should have by the end

By Week 16 you should have four portfolio-grade assets: a **runtime comparison report**, an **eval harness**, a **governed agent playbook**, and an **AI platform reference architecture**. Those four artifacts collectively demonstrate that you understand control surfaces, runtime design, evaluation, governance, and platform thinking. That is much stronger evidence than “I used Claude/Codex/Cursor a lot.” The current official docs increasingly reflect this same shift: the center of gravity is now orchestration, tools, state, guardrails, observability, and deployment discipline. ([OpenAI Developers][17])

## The resource stack I would prioritize

Use official docs first. For OpenAI, stay current on the Responses API, Conversations, background mode, prompt guidance, evals, Codex CLI/config/skills, and the Agents SDK. For Anthropic, stay current on Claude Code overview, memory, permissions, hooks, subagents, MCP, prompt caching, and release notes. For Cursor, watch Cloud Agents, Automations, Rules, Skills, Hooks, self-hosted pools, security docs, and changelog/research posts like CursorBench and dynamic-context-discovery. For systems architecture, anchor yourself in the AWS Generative AI Lens, Google Cloud Well-Architected Framework plus AI/ML perspective, Azure’s AI-agent orchestration/adoption guidance, NIST AI RMF + GenAI Profile, OWASP GenAI/LLM risks, Temporal durable-execution docs, Kubernetes production guidance, and the MCP spec. ([OpenAI Developers][1])

## What to over-index on

If you want the highest ROI, over-index on Weeks **4, 6, 9, 11, and 13**. Those are the weeks that most clearly separate an advanced user from an architect. Tool familiarity is common; durable control over long-horizon systems is not. The platforms themselves are moving in that direction: Codex now emphasizes skills over custom prompts, OpenAI is training mainline models for compaction and long-running workflows, Claude Code is exposing richer permission and automation surfaces, and Cursor is moving toward always-on cloud agents plus self-hosted enterprise execution. ([OpenAI Developers][18])

## Monthly refresh loop

Because the field is still moving quickly, keep one small monthly maintenance ritual. Review the OpenAI API changelog and Codex changelog, Anthropic platform/Claude Code release notes, Cursor changelog/blog, and one of AWS/Google/Azure’s AI architecture updates. Then update only three things in your own stack: your runtime assumptions, your guardrails, and your eval suite. This keeps you adaptive without becoming a changelog tourist. ([OpenAI Developers][19])


[1]: https://developers.openai.com/api/docs/guides/migrate-to-responses "Migrate to the Responses API | OpenAI API"
[2]: https://developers.openai.com/api/docs/guides/production-best-practices "Production best practices | OpenAI API"
[3]: https://developers.openai.com/api/docs/guides/evaluation-best-practices "Evaluation best practices | OpenAI API"
[4]: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-templates-and-variables "Console prompting tools - Claude API Docs"
[5]: https://docs.anthropic.com/en/docs/agents-and-tools/mcp "What is the Model Context Protocol (MCP)? - Model Context Protocol"
[6]: https://developers.openai.com/codex/cli "CLI – Codex | OpenAI Developers"
[7]: https://developers.openai.com/blog/skills-agents-sdk "Using skills to accelerate OSS maintenance | OpenAI Developers"
[8]: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns "AI Agent Orchestration Patterns - Azure Architecture Center | Microsoft Learn"
[9]: https://developers.openai.com/api/docs/guides/conversation-state "Conversation state | OpenAI API"
[10]: https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide?utm_source=chatgpt.com "Codex Prompting Guide"
[11]: https://docs.anthropic.com/en/docs/claude-code/overview "Claude Code overview - Claude Code Docs"
[12]: https://cursor.com/docs/rules.md "cursor.com"
[13]: https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html "Generative AI Lens - AWS Well-Architected Framework - Generative AI Lens"
[14]: https://owasp.org/www-project-top-10-for-large-language-model-applications/ "OWASP Top 10 for Large Language Model Applications | OWASP Foundation"
[15]: https://www.nist.gov/itl/ai-risk-management-framework "AI Risk Management Framework | NIST"
[16]: https://kubernetes.io/docs/setup/production-environment/ "Production environment | Kubernetes"
[17]: https://developers.openai.com/api/docs/guides/agents-sdk?utm_source=chatgpt.com "Agents SDK | OpenAI API"
[18]: https://developers.openai.com/codex/changelog?utm_source=chatgpt.com "Codex changelog"
[19]: https://developers.openai.com/api/docs/changelog?utm_source=chatgpt.com "Changelog | OpenAI API"
