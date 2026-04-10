# AI Mentor

Personal AI-powered architecture learning system. Converts a 16-week AI Architect curriculum into an interactive mentor that teaches, quizzes, tracks progress, and delivers proactive outreach across web and Slack.

## Architecture

```
Next.js Web App (dashboard, chat, quizzes, gate reviews)
        │
FastAPI Backend (mentor engine, scheduler, spaced repetition)
        │
   Claude API (Sonnet for routine, Opus for evaluations)
        │
PostgreSQL + Redis
        │
   Slack Bot (slash commands, daily briefings)
```

**Mentor Engine modes**: Socratic teaching, concept explanation, quiz generation, gate evaluation, artifact review, micro-lessons, freeform Q&A.

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Anthropic API key and Slack credentials

# 2. Start all services
docker compose up --build -d

# 3. Seed the curriculum
docker exec mentor-backend-1 python -m app.seed.parse_curriculum

# 4. Register a user
curl http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Your Name", "email": "you@example.com"}'
```

- **Web app**: http://localhost:3000
- **API**: http://localhost:8000
- **API docs**: http://localhost:8000/docs

## Project Structure

```
backend/
  app/
    api/routes/     — REST endpoints (auth, chat, quiz, gates, progress, curriculum)
    engine/         — Mentor AI engine, prompt routing, spaced repetition (SM-2)
    models/         — SQLAlchemy models (curriculum, user, progress, conversation)
    integrations/   — Slack bot (slash commands, interactive messages)
    scheduler/      — Daily agenda, spaced rep card generation
    seed/           — Curriculum database seeder
frontend/
  src/app/          — Next.js pages (dashboard, chat, progress, gate-review)
  src/lib/api.ts    — TypeScript API client
```

## Slack Commands

| Command | Description |
|---------|-------------|
| `/study` | Current week overview and next steps |
| `/quiz` | Generate and take a calibrated quiz |
| `/progress` | View stats (week, mastery, streak) |
| `/ask <question>` | Ask the mentor anything |
| `/gate` | View gate review questions |

## Key Concepts

- **Adaptive difficulty**: 0.0-1.0 scalar adjusted by quiz/gate performance, calibrates question difficulty
- **Spaced repetition**: SM-2 algorithm generates concept cards after each completed week
- **Gate reviews**: Must score 75%+ to advance to the next week (evaluated by Claude Opus)
- **Bloom progression**: Questions escalate from knowledge/comprehension early in a week to analysis/evaluation/creation at gate time
- **Proactive scheduling**: Morning briefings and evening reviews via Slack at 8am/8pm ET

## Deployment

Running on Hetzner CPX31 with Cloudflare Tunnel:
- `mentor.synaplex.ai` — Web dashboard
- `api.synaplex.ai` — Backend API

## Tech Stack

FastAPI, Next.js 14, PostgreSQL 16, Redis 7, Anthropic Claude API, slack-bolt, Docker Compose, Cloudflare Tunnel
