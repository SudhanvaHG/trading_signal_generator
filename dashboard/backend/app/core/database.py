"""
Database Setup — SQLAlchemy async with SQLite (easily swappable to PostgreSQL).
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from datetime import datetime
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ─── Models ───────────────────────────────────────────────────────────

class SignalRecord(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    signal_type = Column(String(4), nullable=False)          # BUY / SELL
    strategy = Column(String(50), nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    rr_ratio = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    trend = Column(Integer, default=0)
    volume_ok = Column(Boolean, default=False)
    reason = Column(Text, default="")
    atr_value = Column(Float, default=0.0)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestRecord(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    run_at = Column(DateTime, default=datetime.utcnow, index=True)
    period = Column(String(10), nullable=False)
    timeframe = Column(String(5), nullable=False)
    initial_balance = Column(Float, nullable=False)
    final_balance = Column(Float, nullable=False)
    total_return_pct = Column(Float, nullable=False)
    total_trades = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_rate_pct = Column(Float, default=0.0)
    max_drawdown_pct = Column(Float, default=0.0)
    challenge_passed = Column(Boolean, default=False)
    trade_log = Column(JSON, default=list)
    summary = Column(JSON, default=dict)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    channel = Column(String(20), nullable=False)             # telegram / email / sms
    recipient = Column(String(200), default="")
    subject = Column(String(200), default="")
    message = Column(Text, nullable=False)
    success = Column(Boolean, default=True)
    error = Column(Text, default="")


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    channel = Column(String(20), nullable=False)
    enabled = Column(Boolean, default=True)
    config_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── Dependency ───────────────────────────────────────────────────────

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
