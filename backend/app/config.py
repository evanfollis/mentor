from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://mentor:mentor_dev@localhost:5432/mentor"
    redis_url: str = "redis://localhost:6379/0"
    anthropic_api_key: str = ""
    slack_api_token: str = ""
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    # AI model selection
    model_routine: str = "claude-sonnet-4-20250514"
    model_evaluation: str = "claude-opus-4-20250514"

    # App settings
    app_name: str = "AI Mentor"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env"}


settings = Settings()
