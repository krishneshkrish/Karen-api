from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Karen API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "production"  # development | production
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5180",
        "https://karen-app.vercel.app",
    ]

    # Security
    secret_key: str                        # Used for HMAC user ID hashing
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str         # For server-side operations

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-3.6-flash"

    # ML Models (loaded lazily on first request)
    emotion_model_name: str = "j-hartmann/emotion-english-distilroberta-base"
    zeroshot_model_name: str = "facebook/bart-large-mnli"

    # Rate limiting
    rate_limit_per_minute: int = 10        # Matches Gemini free tier RPM
    rate_limit_per_day: int = 200          # Per user daily cap

    # Keep-alive (Render free tier)
    render_url: str = ""                   # Set in prod: https://karen-api.onrender.com
    keep_alive_interval_seconds: int = 840 # 14 minutes

    # Chat context window
    max_context_messages: int = 10         # Last N messages sent with each request

    # Severity thresholds
    severity_escalate_threshold: float = 0.65   # Above this → recommend professional help
    severity_crisis_threshold: float = 0.80     # Above this → crisis response


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
