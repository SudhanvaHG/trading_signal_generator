"""
Application Configuration
All settings loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────────
    APP_NAME: str = "PropAlgo Trading Dashboard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"

    # ─── API ──────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80", "http://frontend:3000"]

    # ─── Trading Engine ───────────────────────────────────────
    INITIAL_BALANCE: float = 10000.0
    DEFAULT_ASSETS: List[str] = ["XAUUSD", "BTCUSD", "XRPUSD", "EURUSD"]
    LIVE_SCAN_INTERVAL: int = 60          # seconds between live scans
    DATA_PERIOD_LIVE: str = "3mo"
    DATA_PERIOD_BACKTEST: str = "1y"
    DATA_INTERVAL: str = "1d"

    # ─── Telegram ─────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_ENABLED: bool = False

    # ─── Email (SMTP) ─────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    EMAIL_RECIPIENTS: List[str] = []
    EMAIL_ENABLED: bool = False

    # ─── SMS (Twilio) ─────────────────────────────────────────
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    SMS_RECIPIENTS: List[str] = []
    SMS_ENABLED: bool = False

    # ─── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    USE_REDIS: bool = True

    # ─── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./prop_algo.db"

    # ─── Auth ─────────────────────────────────────────────────
    DASHBOARD_USERNAME: str = "admin"
    DASHBOARD_PASSWORD: str = "admin123"   # Change in production!
    JWT_EXPIRE_MINUTES: int = 1440         # 24 hours

    # ─── Notifications ────────────────────────────────────────
    NOTIFY_ON_SIGNAL: bool = True
    NOTIFY_ON_RISK_ALERT: bool = True
    MIN_CONFIDENCE_NOTIFY: float = 0.65   # Only notify high-confidence signals

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
