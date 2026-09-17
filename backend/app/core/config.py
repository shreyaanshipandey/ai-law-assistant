"""
Centralized application configuration.
Loaded once as a singleton `settings` object, sourced from environment
variables / .env file via pydantic-settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Law Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_law_assistant"

    # JWT
    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI / LLM
    # Using Google Gemini via its OpenAI-compatible endpoint by default (free tier).
    # To switch back to real OpenAI, set OPENAI_BASE_URL="" and use an OpenAI key/model.
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    OPENAI_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"
    BNS_CSV_PATH: str = "./app/data/bns_sections.csv"

    # Admin bootstrap
    FIRST_ADMIN_EMAIL: str = "admin@ailaw.in"
    FIRST_ADMIN_PASSWORD: str = "ChangeMe123!"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
