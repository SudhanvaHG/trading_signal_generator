"""
Notifications API Routes
Configure and test Telegram, Email, SMS channels.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

from ...services.notification_service import (
    test_telegram, test_email, test_sms,
    broadcast_signal, broadcast_risk_alert,
    send_telegram_signal, send_email_signal, send_sms_signal,
)
from ...core.config import settings

router = APIRouter(prefix="/notifications", tags=["Notifications"])
logger = logging.getLogger(__name__)


# ─── Pydantic Models ──────────────────────────────────────────────────

class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str

class EmailConfig(BaseModel):
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: str
    password: str
    from_email: str
    to_email: str

class SmsConfig(BaseModel):
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str

class TestSignalPayload(BaseModel):
    channel: str   # telegram / email / sms / all


# ─── Status ───────────────────────────────────────────────────────────

@router.get("/status")
async def get_notification_status():
    """Return current notification channel status."""
    return {
        "telegram": {
            "enabled": settings.TELEGRAM_ENABLED,
            "configured": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
            "chat_id": settings.TELEGRAM_CHAT_ID,
        },
        "email": {
            "enabled": settings.EMAIL_ENABLED,
            "configured": bool(settings.SMTP_USERNAME),
            "smtp_host": settings.SMTP_HOST,
            "smtp_port": settings.SMTP_PORT,
            "recipients": settings.EMAIL_RECIPIENTS,
        },
        "sms": {
            "enabled": settings.SMS_ENABLED,
            "configured": bool(settings.TWILIO_ACCOUNT_SID),
            "recipients": settings.SMS_RECIPIENTS,
        },
        "min_confidence_threshold": settings.MIN_CONFIDENCE_NOTIFY,
        "notify_on_signal": settings.NOTIFY_ON_SIGNAL,
        "notify_on_risk_alert": settings.NOTIFY_ON_RISK_ALERT,
    }


# ─── Test Endpoints ───────────────────────────────────────────────────

@router.post("/test/telegram")
async def test_telegram_connection(config: TelegramConfig):
    """Test Telegram bot credentials."""
    result = await test_telegram(config.bot_token, config.chat_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/test/email")
async def test_email_connection(config: EmailConfig):
    """Test SMTP email credentials."""
    result = await test_email(
        config.smtp_host, config.smtp_port,
        config.username, config.password,
        config.from_email, config.to_email,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/test/sms")
async def test_sms_connection(config: SmsConfig):
    """Test Twilio SMS credentials."""
    result = await test_sms(
        config.account_sid, config.auth_token,
        config.from_number, config.to_number,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/test/signal")
async def send_test_signal(payload: TestSignalPayload):
    """Send a dummy signal through the chosen channel(s)."""
    dummy_signal = {
        "symbol": "XAUUSD",
        "signal": "BUY",
        "strategy": "Breakout_Retest",
        "entry": 2345.50,
        "stop_loss": 2330.00,
        "take_profit": 2376.50,
        "rr_ratio": 2.0,
        "confidence": 0.78,
        "volume_ok": True,
        "reason": "Test signal — Breakout above 20-bar high with volume confirmation.",
    }

    channel = payload.channel.lower()

    if channel == "telegram":
        ok = await send_telegram_signal(dummy_signal)
    elif channel == "email":
        ok = await send_email_signal(dummy_signal)
    elif channel == "sms":
        ok = await send_sms_signal(dummy_signal)
    elif channel == "all":
        await broadcast_signal(dummy_signal)
        ok = True
    else:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {channel}")

    return {"success": ok, "channel": channel, "signal": dummy_signal}


@router.post("/test/risk-alert")
async def send_test_risk_alert():
    """Send a test risk alert across all enabled channels."""
    await broadcast_risk_alert(
        "Daily Loss Cap",
        "Daily loss of 2.1% has exceeded the 2.0% daily cap. Trading is paused for today.",
    )
    return {"success": True, "message": "Risk alert sent to all enabled channels."}
