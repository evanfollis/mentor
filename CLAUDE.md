# AI Mentor System

## Architecture
- **Backend**: FastAPI (Python 3.12+) with async SQLAlchemy + asyncpg
- **Frontend**: Next.js 14 (TypeScript, App Router)
- **Database**: PostgreSQL 16 + Redis 7
- **AI**: Anthropic Claude API (Sonnet for routine, Opus for evaluations)
- **Deployment**: Docker Compose on Hetzner, Cloudflare Tunnel

## Key Paths
- Backend API routes: `backend/app/api/routes/`
- Mentor engine + prompt modes: `backend/app/engine/`
- SQLAlchemy models: `backend/app/models/`
- Slack bot: `backend/app/integrations/slack_bot.py`
- Scheduler (daily agenda, spaced rep): `backend/app/scheduler/`
- Curriculum seed data: `backend/app/seed/parse_curriculum.py`
- Frontend pages: `frontend/src/app/`
- API client: `frontend/src/lib/api.ts`

## Commands
- Start locally: `docker compose up --build -d`
- Seed DB: `docker exec mentor-backend-1 python -m app.seed.parse_curriculum`
- Backend logs: `docker logs mentor-backend-1 --tail 50`
- Run on server: `ssh -i ~/.ssh/hetzner root@5.78.185.6`

## Code Conventions
- Python: ruff, line-length 100, Python 3.12+
- TypeScript: Next.js App Router conventions
- All DB access via async SQLAlchemy sessions
- Mentor engine modes: socratic, explain, quiz, gate_review, artifact_review, micro_lesson, freeform
- Gate pass threshold: 0.75

## Active Decisions

- **All DB access is async SQLAlchemy sessions.** Don't use raw SQL or synchronous queries. Every route gets `db: AsyncSession` from the dependency.
- **Engine modes are the AI interface.** All Claude API calls go through `engine.respond(mode=..., ...)`. Don't call the Anthropic SDK directly from routes.
- **Gate threshold is 0.75 and non-negotiable.** It's a pedagogical decision, not a tuning parameter.
- **Frontend uses App Router only.** No Pages Router patterns. Server components by default, `"use client"` only when you need interactivity.
- **API client is centralized.** All fetch calls go through `frontend/src/lib/api.ts`. Don't use raw fetch in components.
- **Spaced repetition uses SM-2.** The algorithm is implemented in `backend/app/engine/spaced_repetition.py`. Don't substitute or "improve" it.
- **Current priority: wire up existing backend logic.** Cards, artifacts, and progress tracking have backend implementations that need frontend pages and API routes. See the active plan.

## Deployment
- Server: Hetzner CPX31 (5.78.185.6)
- URLs: mentor.synaplex.ai (frontend), api.synaplex.ai (backend)
- Tunnel: cloudflared systemd service
- Docker containers auto-restart on boot
