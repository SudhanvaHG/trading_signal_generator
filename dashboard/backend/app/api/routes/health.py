"""
Health & System Info Routes
"""

from fastapi import APIRouter
from datetime import datetime
import sys, platform

from ...core.config import settings
from ...core.websocket_manager import ws_manager
from ...services.scheduler import get_scheduler_status
from ...services.trading_engine import trading_engine

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/system")
async def system_info():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "python": sys.version,
        "platform": platform.platform(),
        "ws_clients": ws_manager.connection_count,
        "scheduler": get_scheduler_status(),
        "last_scan": {
            "time": trading_engine.last_scan_time.isoformat() if trading_engine.last_scan_time else None,
            "signals": len(trading_engine.last_signals),
            "scan_count": trading_engine.scan_count,
        },
        "notifications": {
            "telegram": settings.TELEGRAM_ENABLED,
            "email": settings.EMAIL_ENABLED,
            "sms": settings.SMS_ENABLED,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
