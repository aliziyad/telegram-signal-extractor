import os
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Telegram Configuration
    TELEGRAM_API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_PHONE: str = os.getenv("TELEGRAM_PHONE", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/signal_extractor"
    )
    
    # Supabase Webhook Configuration
    SUPABASE_INGEST_URL: str = os.getenv(
        "SUPABASE_INGEST_URL",
        "https://zcdggtjwrtrqhqrngfau.supabase.co/functions/v1/ingest-copy-signal"
    )
    SUPABASE_API_KEY: str = os.getenv("SUPABASE_API_KEY", "")
    COPY_SIGNAL_API_KEY: str = os.getenv("COPY_SIGNAL_API_KEY", "")
    
    # AI API Keys
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Parsing Configuration
    REGEX_ENABLED: bool = os.getenv("REGEX_ENABLED", "true").lower() == "true"
    CLAUDE_ENABLED: bool = os.getenv("CLAUDE_ENABLED", "true").lower() == "true"
    GEMINI_ENABLED: bool = os.getenv("GEMINI_ENABLED", "false").lower() == "true"
    OPENAI_ENABLED: bool = os.getenv("OPENAI_ENABLED", "false").lower() == "true"
    
    # API Parsing Priority (order of fallback)
    PARSING_PRIORITY: List[str] = [
        "regex",
        "claude",
        "gemini",
        "openai"
    ]
    
    # Schedule Configuration (Maldives Time: UTC+4)
    SCHEDULE_START: str = os.getenv("SCHEDULE_START", "04:00")  # Sunday 4 AM
    SCHEDULE_END: str = os.getenv("SCHEDULE_END", "22:00")  # Friday 10 PM
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Male")  # Maldives timezone
    
    # Flask Configuration
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    
    # Extraction Configuration
    MAX_CHANNELS: int = int(os.getenv("MAX_CHANNELS", "100"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    EXTRACTION_TIMEOUT: int = int(os.getenv("EXTRACTION_TIMEOUT", "30"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/signal_extractor.log")
    
    # Admin Authentication
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
