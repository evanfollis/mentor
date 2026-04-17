# CURRENT_STATE — mentor

> This file is maintained by project tick sessions and reflection passes.
> Update it every time you complete a tick or significant attended session.
> **Accuracy over completeness.** A short honest file is worth more than a
> long stale one. If you don't know something, say "unknown" — don't omit it.

**Last updated**: 2026-04-17T19:09:40Z — executive attended session creating missing front door from repo evidence only

---

## Deployed / running state

- Repo docs (`README.md`, `CLAUDE.md`) claim a Docker Compose deployment on Hetzner behind Cloudflare Tunnel.
- Documented public URLs: `mentor.synaplex.ai` (frontend) and `api.synaplex.ai` (backend).
- Local run contract in the repo is `docker compose up --build -d`, then `python -m app.seed.parse_curriculum` inside the backend container.
- The currently deployed commit is unknown from this repo alone.

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
