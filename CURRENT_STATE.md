# CURRENT_STATE — mentor

> This file is maintained by project tick sessions and reflection passes.
> Update it every time you complete a tick or significant attended session.
> **Accuracy over completeness.** A short honest file is worth more than a
> long stale one. If you don't know something, say "unknown" — don't omit it.

**Last updated**: 2026-04-17T19:30Z — mentor session verified deployed commit from host evidence

---

## Deployed / running state

- **Deployed repo**: `/opt/mentor/` — HEAD is `28bdee1` ("updated .env and .env.example to include SLACK_API_TOKEN").
- **Deployed repo has a dirty working tree.** Uncommitted changes to `backend/Dockerfile`, `backend/app/api/routes/chat.py`, `gates.py`, `backend/app/config.py`, `backend/app/main.py`, `backend/app/models/conversation.py`, `backend/pyproject.toml`, `docker-compose.yml`, `frontend/src/app/chat/page.tsx`; untracked files for `slack_bot.py`, `daily_agenda.py`, `spaced_rep_scheduler.py`, `gate-review/`, `progress/`. The running containers were built from this dirty tree.
- **Containers created**: 2026-04-10T01:35Z. All four containers (backend, frontend, db, redis) are up ~7 days.
- **Dev repo is 3 commits ahead of deployed**: `432eff2` (Complete MVP), `2c144d6` (Wire up spaced rep), `47f4fab` (Add current-state front door). Plus the dev repo has its own uncommitted working tree changes.
- **The deployed build includes MVP-era code as uncommitted changes**, not as committed history. The deployed repo never received the `432eff2` or later commits.
- Public URLs: `mentor.synaplex.ai` (frontend), `api.synaplex.ai` (backend).
- Docker image has no git-SHA label; deployed commit was determined from `/opt/mentor/.git` HEAD.

## What's in progress

- `main` is dirty against `origin/main`.
- Modified tracked files: `CLAUDE.md`, `backend/app/api/routes/cards.py`, `chat.py`, `gates.py`, `progress.py`, `quiz.py`, `backend/app/engine/mentor.py`, `backend/app/main.py`, `backend/app/models/__init__.py`.
- Untracked files: `backend/alembic/versions/20260410_0001_add_learning_sessions.py`, `backend/app/engine/session_store.py`, `backend/app/models/session.py`, `backend/app/telemetry.py`.
- The most recent committed work after MVP is `2c144d6` with message `Wire up spaced rep review, artifact submission, and progress tracking`.

## Known broken or degraded

- No repo-local test files were found during this inspection, so current behavior is unverified from the repo alone.
- Live deployment health and deployed commit are unknown from the repo alone.
- No specific failing route, page, or service is proven broken by the files inspected.

## Blocked on

- Nothing explicit is recorded in the repo as a blocker.
- If the project wants this file to state what is actually live rather than what the docs claim, a project session needs to verify the deployed containers or write the deployed commit into this front door.

## Recent decisions

- The documented architecture is FastAPI + Next.js + PostgreSQL + Redis + Slack, with Docker Compose as the run path.
- `CLAUDE.md` says all database access should stay on async SQLAlchemy sessions, and all Claude calls should go through the mentor engine modes rather than route-level SDK calls.
- `CLAUDE.md` fixes the gate pass threshold at `0.75`.
- `CLAUDE.md` also states the current priority: wire up existing backend logic for cards, artifacts, and progress tracking before adding new abstractions.
- Recent commit history shows a two-step arc: `432eff2` completed the MVP, then `2c144d6` moved into spaced repetition review, artifact submission, and progress tracking.

## What bit the last session

- The repo contains substantial uncommitted backend work, so any new session starts in a dirty tree and must avoid bundling unrelated changes.
- The repo documents public URLs but does not encode which commit is live.
- There is no visible repo-local test suite to use as a quick confidence check before or after backend edits.

## What the next agent must read first

- `CLAUDE.md`
- `README.md`
- `git status --short`
- The dirty backend files under `backend/app/api/routes/` plus `backend/app/engine/session_store.py` and `backend/app/models/session.py`
