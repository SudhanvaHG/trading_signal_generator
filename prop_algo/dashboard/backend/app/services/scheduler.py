"""
Background Scheduler Service
Runs the live signal scan loop using APScheduler.
"""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..core.config import settings
from ..core.websocket_manager import ws_manager
from .trading_engine import trading_engine
from .notification_service import broadcast_signal, broadcast_risk_alert

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_scan_running = False


async def run_live_scan():
    """Single scan iteration — called by scheduler."""
    global _scan_running
    if _scan_running:
        logger.warning("Previous scan still running, skipping this tick.")
        return
    _scan_running = True

    try:
        logger.info(f"Starting scan #{trading_engine.scan_count + 1}...")
        await ws_manager.send_scan_status(
            trading_engine.scan_count + 1, "running"
        )

        result = await trading_engine.run_single_scan(
            period=settings.DATA_PERIOD_LIVE,
            interval=settings.DATA_INTERVAL,
        )

        # Broadcast summary to all WS clients
        await ws_manager.send_scan_status(
            trading_engine.scan_count,
            "complete",
            {
                "approved": result["approved_signals"],
                "raw_signals_count": result["raw_signals"],
                "approved_signals_count": result["approved_signals"],
                "rejected_signals_count": result["rejected_signals"],
                "data_status": result["data_status"],
                "scan_time": result["scan_time"],
            },
        )

        # Send new signals via WS + notifications
        new_signals = result.get("signals", [])
        for signal in new_signals:
            await ws_manager.send_signal(signal)
            if settings.NOTIFY_ON_SIGNAL:
                await broadcast_signal(signal)

        logger.info(
            f"Scan #{trading_engine.scan_count} complete — "
            f"{len(new_signals)} approved signals"
        )

    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        await ws_manager.send_scan_status(0, "error", {"error": str(e)})
    finally:
        _scan_running = False


def start_scheduler(interval_seconds: int = None):
    """Start the live scan scheduler."""
    secs = interval_seconds or settings.LIVE_SCAN_INTERVAL
    if not scheduler.running:
        scheduler.add_job(
            run_live_scan,
            trigger=IntervalTrigger(seconds=secs),
            id="live_scan",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()
        logger.info(f"Scheduler started — scanning every {secs}s")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


def update_scan_interval(seconds: int):
    """Reschedule the scan with a new interval."""
    scheduler.reschedule_job(
        "live_scan",
        trigger=IntervalTrigger(seconds=seconds),
    )
    logger.info(f"Scan interval updated to {seconds}s")


def get_scheduler_status() -> dict:
    job = scheduler.get_job("live_scan")
    return {
        "running": scheduler.running,
        "interval_seconds": settings.LIVE_SCAN_INTERVAL,
        "next_run": str(job.next_run_time) if job and job.next_run_time else None,
        "scan_count": trading_engine.scan_count,
        "last_scan": trading_engine.last_scan_time.isoformat() if trading_engine.last_scan_time else None,
    }
