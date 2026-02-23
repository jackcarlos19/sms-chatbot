from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    business_name: str = Field(default="Acme Services", alias="BUSINESS_NAME")
    admin_api_key: str = Field(default="change-admin-key", alias="ADMIN_API_KEY")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="change-this-admin-password", alias="ADMIN_PASSWORD")
    support_phone_number: str = Field(
        default="+10000000000",
        alias="SUPPORT_PHONE_NUMBER",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/sms_chatbot",
        alias="DATABASE_URL",
    )
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")

    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    twilio_account_sid: str = Field(default="", alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(default="", alias="TWILIO_PHONE_NUMBER")
    twilio_status_callback_url: str = Field(
        default="", alias="TWILIO_STATUS_CALLBACK_URL"
    )
    twilio_max_retries: int = Field(default=3, alias="TWILIO_MAX_RETRIES")
    twilio_max_sends_per_second: int = Field(
        default=1, alias="TWILIO_MAX_SENDS_PER_SECOND"
    )

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    vercel_ai_gateway_api_key: str = Field(
        default="", alias="VERCEL_AI_GATEWAY_API_KEY"
    )
    ai_provider: str = Field(default="openrouter", alias="AI_PROVIDER")
    ai_base_url: str = Field(default="", alias="AI_BASE_URL")
    ai_model: str = Field(
        default="anthropic/claude-sonnet-4-20250514",
        alias="AI_MODEL",
    )
    ai_max_tokens: int = Field(default=300, alias="AI_MAX_TOKENS")
    admin_session_secret: str = Field(
        default="change-this-session-secret",
        alias="ADMIN_SESSION_SECRET",
    )
    admin_session_max_age_seconds: int = Field(
        default=60 * 60 * 12,
        alias="ADMIN_SESSION_MAX_AGE_SECONDS",
    )

    default_quiet_hours_start: str = Field(
        default="21:00", alias="DEFAULT_QUIET_HOURS_START"
    )
    default_quiet_hours_end: str = Field(
        default="09:00", alias="DEFAULT_QUIET_HOURS_END"
    )

    ngrok_authtoken: str = Field(default="", alias="NGROK_AUTHTOKEN")


@lru_cache
def get_settings() -> Settings:
    return Settings()
