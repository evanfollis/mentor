import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import auth, chat, curriculum, gates, progress, quiz

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — launch the scheduler
    from app.scheduler.daily_agenda import start_scheduler
    scheduler_task = asyncio.create_task(start_scheduler())
    logger.info("Scheduler started")
    yield
    # Shutdown
    scheduler_task.cancel()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(curriculum.router, prefix="/api/curriculum", tags=["curriculum"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(gates.router, prefix="/api/gates", tags=["gates"])


# Slack event endpoint
if settings.slack_bot_token and settings.slack_signing_secret:
    from app.integrations.slack_bot import handler as slack_handler

    @app.post("/slack/events")
    async def slack_events(request: Request):
        return await slack_handler.handle(request)

    @app.post("/slack/interactions")
    async def slack_interactions(request: Request):
        return await slack_handler.handle(request)

    logger.info("Slack bot endpoints registered")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
