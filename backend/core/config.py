"""Application settings loaded from environment."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://EverAI:password@localhost:5432/EverAI_db"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # App
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    secret_key: str = "dev-secret-change-me"
    environment: str = "development"
    log_level: str = "INFO"

    # Rate limiting
    rate_limit_per_minute: int = 10
    max_concurrent_analyses: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
