"""
Signals API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import Optional
import logging

from ...core.database import get_db, SignalRecord
from ...services.trading_engine import trading_engine
from ...services.scheduler import get_scheduler_status, update_scan_interval, run_live_scan

router = APIRouter(prefix="/signals", tags=["Signals"])
logger = logging.getLogger(__name__)


@router.get("/latest")
async def get_latest_signals(
    limit: int = Query(50, ge=1, le=500),
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    strategy: Optional[str] = None,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
):
    """Return the most recent approved signals from the last scan."""
    signals = trading_engine.last_signals or []

    if symbol:
        signals = [s for s in signals if s.get("symbol") == symbol.upper()]
    if signal_type:
        signals = [s for s in signals if s.get("signal") == signal_type.upper()]
    if strategy:
        signals = [s for s in signals if strategy.lower() in s.get("strategy", "").lower()]
    if min_confidence > 0:
        signals = [s for s in signals if s.get("confidence", 0) >= min_confidence]

    return {
        "total": len(signals),
        "signals": signals[-limit:],
        "scan_summary": trading_engine.last_scan_summary,
    }


@router.get("/scan-status")
async def get_scan_status():
    """Return current live scan status."""
    return get_scheduler_status()


@router.post("/scan-now")
async def trigger_manual_scan():
    """Trigger an immediate signal scan."""
    await run_live_scan()
    return {
        "message": "Scan triggered",
        "scan_number": trading_engine.scan_count,
        "signals_found": len(trading_engine.last_signals),
    }


@router.put("/scan-interval")
async def set_scan_interval(seconds: int = Query(..., ge=30, le=86400)):
    """Update the live scan refresh interval."""
    update_scan_interval(seconds)
    return {"message": f"Scan interval updated to {seconds}s"}


@router.get("/summary")
async def get_signal_summary():
    """Return breakdown by strategy and asset."""
    signals = trading_engine.last_signals or []

    by_strategy: dict = {}
    by_asset: dict = {}
    by_type = {"BUY": 0, "SELL": 0}

    for s in signals:
        strat = s.get("strategy", "Unknown")
        sym = s.get("symbol", "Unknown")
        sig = s.get("signal", "")

        by_strategy[strat] = by_strategy.get(strat, 0) + 1
        by_asset[sym] = by_asset.get(sym, 0) + 1
        if sig in by_type:
            by_type[sig] += 1

    return {
        "total_signals": len(signals),
        "by_strategy": by_strategy,
        "by_asset": by_asset,
        "by_type": by_type,
        "last_scan": trading_engine.last_scan_time.isoformat() if trading_engine.last_scan_time else None,
    }
