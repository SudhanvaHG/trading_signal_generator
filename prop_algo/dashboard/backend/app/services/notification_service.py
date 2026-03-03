"""
Notification Service
Handles Telegram, Email (SMTP), and SMS (Twilio) alerts.
All channels are optional and controlled via environment variables.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List

import httpx
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..core.config import settings

logger = logging.getLogger(__name__)


# ─── Formatting Helpers ───────────────────────────────────────────────

def _signal_emoji(signal_type: str) -> str:
    return "🟢" if signal_type == "BUY" else "🔴"

def _confidence_bar(confidence: float) -> str:
    filled = int(confidence * 10)
    return "█" * filled + "░" * (10 - filled)

def _format_signal_telegram(signal: dict) -> str:
    emoji = _signal_emoji(signal.get("signal", ""))
    conf = signal.get("confidence", 0)
    rr = signal.get("rr_ratio", 0)
    return f"""
{emoji} *NEW SIGNAL — {signal.get('symbol', '')}*

*Direction:* {signal.get('signal', '')}
*Strategy:* {signal.get('strategy', '').replace('_', ' ')}
*Entry:* `{signal.get('entry', 0):.5f}`
*Stop Loss:* `{signal.get('stop_loss', 0):.5f}`
*Take Profit:* `{signal.get('take_profit', 0):.5f}`
*R:R Ratio:* 1:{rr:.1f}
*Confidence:* {_confidence_bar(conf)} {conf*100:.0f}%
*Volume:* {'✓ Confirmed' if signal.get('volume_ok') else '✗ Weak'}

_{signal.get('reason', '')}_{' '}
📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
""".strip()

def _format_signal_email_html(signal: dict) -> str:
    emoji = "▲" if signal.get("signal") == "BUY" else "▼"
    color = "#00C896" if signal.get("signal") == "BUY" else "#FF4757"
    return f"""
<html><body style="background:#0F1923;color:#E0E6ED;font-family:monospace;padding:24px;">
  <div style="max-width:520px;margin:auto;border:1px solid #1E2D3D;border-radius:8px;padding:24px;">
    <h2 style="color:{color};margin-bottom:4px;">{emoji} {signal.get('symbol','')} {signal.get('signal','')} Signal</h2>
    <p style="color:#64748B;margin-top:0;">{signal.get('strategy','').replace('_',' ')} &bull; {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px 0;color:#64748B;">Entry</td><td style="color:#E0E6ED;font-weight:bold;">{signal.get('entry',0):.5f}</td></tr>
      <tr><td style="padding:8px 0;color:#64748B;">Stop Loss</td><td style="color:#FF4757;">{signal.get('stop_loss',0):.5f}</td></tr>
      <tr><td style="padding:8px 0;color:#64748B;">Take Profit</td><td style="color:#00C896;">{signal.get('take_profit',0):.5f}</td></tr>
      <tr><td style="padding:8px 0;color:#64748B;">R:R Ratio</td><td style="color:#E0E6ED;">1:{signal.get('rr_ratio',0):.1f}</td></tr>
      <tr><td style="padding:8px 0;color:#64748B;">Confidence</td><td style="color:#E0E6ED;">{signal.get('confidence',0)*100:.0f}%</td></tr>
    </table>
    <p style="color:#64748B;font-size:12px;margin-top:16px;">{signal.get('reason','')}</p>
    <p style="color:#1E2D3D;font-size:10px;margin-top:24px;">PropAlgo Trading System &bull; Automated Alert</p>
  </div>
</body></html>
"""

def _format_signal_sms(signal: dict) -> str:
    emoji = "▲" if signal.get("signal") == "BUY" else "▼"
    return (
        f"PropAlgo {emoji} {signal.get('symbol','')} {signal.get('signal','')} | "
        f"Entry:{signal.get('entry',0):.4f} SL:{signal.get('stop_loss',0):.4f} "
        f"TP:{signal.get('take_profit',0):.4f} RR:1:{signal.get('rr_ratio',0):.1f} "
        f"Conf:{signal.get('confidence',0)*100:.0f}%"
    )

def _format_risk_alert_telegram(alert_type: str, message: str) -> str:
    return f"⚠️ *RISK ALERT — {alert_type.upper()}*\n\n{message}\n\n📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"


# ─── Telegram ─────────────────────────────────────────────────────────

async def send_telegram(text: str, parse_mode: str = "Markdown") -> bool:
    if not settings.TELEGRAM_ENABLED or not settings.TELEGRAM_BOT_TOKEN:
        logger.debug("Telegram disabled or not configured.")
        return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Telegram message sent.")
            return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False

async def send_telegram_signal(signal: dict) -> bool:
    return await send_telegram(_format_signal_telegram(signal))

async def send_telegram_risk_alert(alert_type: str, message: str) -> bool:
    return await send_telegram(_format_risk_alert_telegram(alert_type, message))

async def test_telegram(bot_token: str, chat_id: str) -> dict:
    """Test Telegram credentials without touching settings."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "✅ *PropAlgo* — Telegram connection test successful!",
        "parse_mode": "Markdown",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            if resp.status_code == 200 and data.get("ok"):
                return {"success": True, "message": "Telegram connected successfully."}
            return {"success": False, "message": data.get("description", "Unknown error")}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── Email ────────────────────────────────────────────────────────────

async def send_email(
    subject: str,
    html_body: str,
    recipients: Optional[List[str]] = None,
) -> bool:
    if not settings.EMAIL_ENABLED or not settings.SMTP_USERNAME:
        logger.debug("Email disabled or not configured.")
        return False

    to_list = recipients or settings.EMAIL_RECIPIENTS
    if not to_list:
        logger.warning("No email recipients configured.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    msg["To"] = ", ".join(to_list)
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email sent to {to_list}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False

async def send_email_signal(signal: dict) -> bool:
    sym = signal.get("symbol", "")
    sig = signal.get("signal", "")
    subject = f"PropAlgo Alert: {sym} {sig} Signal — {datetime.utcnow().strftime('%H:%M UTC')}"
    return await send_email(subject, _format_signal_email_html(signal))

async def test_email(
    smtp_host: str, smtp_port: int, username: str,
    password: str, from_email: str, to_email: str,
) -> dict:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "PropAlgo — Email Connection Test"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.attach(MIMEText("<p>✅ Email connection test successful.</p>", "html"))
    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=username,
            password=password,
            start_tls=True,
        )
        return {"success": True, "message": "Email sent successfully."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── SMS (Twilio) ─────────────────────────────────────────────────────

async def send_sms(body: str, recipients: Optional[List[str]] = None) -> bool:
    if not settings.SMS_ENABLED or not settings.TWILIO_ACCOUNT_SID:
        logger.debug("SMS disabled or not configured.")
        return False

    to_list = recipients or settings.SMS_RECIPIENTS
    if not to_list:
        logger.warning("No SMS recipients configured.")
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    success = True
    async with httpx.AsyncClient(timeout=15) as client:
        for number in to_list:
            try:
                resp = await client.post(
                    url,
                    data={"From": settings.TWILIO_FROM_NUMBER, "To": number, "Body": body},
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                )
                if resp.status_code not in (200, 201):
                    logger.error(f"SMS to {number} failed: {resp.text}")
                    success = False
                else:
                    logger.info(f"SMS sent to {number}")
            except Exception as e:
                logger.error(f"SMS send failed to {number}: {e}")
                success = False
    return success

async def send_sms_signal(signal: dict) -> bool:
    return await send_sms(_format_signal_sms(signal))

async def test_sms(account_sid: str, auth_token: str, from_number: str, to_number: str) -> dict:
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                data={"From": from_number, "To": to_number, "Body": "PropAlgo SMS test successful ✅"},
                auth=(account_sid, auth_token),
            )
            if resp.status_code in (200, 201):
                return {"success": True, "message": f"SMS sent to {to_number}."}
            return {"success": False, "message": resp.json().get("message", "Unknown error")}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── Broadcast All ────────────────────────────────────────────────────

async def broadcast_signal(signal: dict):
    """Send signal across all enabled channels."""
    conf = signal.get("confidence", 0)
    if conf < settings.MIN_CONFIDENCE_NOTIFY:
        logger.info(f"Signal confidence {conf:.2f} below threshold, skipping notification.")
        return

    tasks = []
    if settings.TELEGRAM_ENABLED:
        tasks.append(send_telegram_signal(signal))
    if settings.EMAIL_ENABLED:
        tasks.append(send_email_signal(signal))
    if settings.SMS_ENABLED:
        tasks.append(send_sms_signal(signal))

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Notification error: {r}")

async def broadcast_risk_alert(alert_type: str, message: str):
    """Send risk alert across all enabled channels."""
    tasks = []
    if settings.TELEGRAM_ENABLED:
        tasks.append(send_telegram_risk_alert(alert_type, message))
    if settings.EMAIL_ENABLED:
        tasks.append(send_email(
            f"⚠️ PropAlgo Risk Alert: {alert_type}",
            f"<html><body style='background:#0F1923;color:#E0E6ED;padding:24px;font-family:monospace;'>"
            f"<h2 style='color:#FF4757;'>⚠️ Risk Alert: {alert_type}</h2>"
            f"<p>{message}</p></body></html>",
        ))
    if settings.SMS_ENABLED:
        tasks.append(send_sms(f"PropAlgo RISK ALERT: {alert_type} — {message}"))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
