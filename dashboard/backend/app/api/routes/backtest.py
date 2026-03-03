"""
Backtest API Routes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from ...services.trading_engine import trading_engine
from ...core.websocket_manager import ws_manager

router = APIRouter(prefix="/backtest", tags=["Backtest"])
logger = logging.getLogger(__name__)

# Store last backtest result in memory (also persisted to DB in production)
_last_backtest_result: Optional[dict] = None
_backtest_running: bool = False


class BacktestRequest(BaseModel):
    period: str = "1y"
    timeframe: str = "1d"
    initial_balance: float = 10000.0


@router.post("/run")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Start a backtest run in the background."""
    global _backtest_running

    if _backtest_running:
        raise HTTPException(status_code=409, detail="A backtest is already running.")

    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y"]
    valid_timeframes = ["1d", "4h", "1h"]

    if request.period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Choose from {valid_periods}")
    if request.timeframe not in valid_timeframes:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Choose from {valid_timeframes}")
    if not (1000 <= request.initial_balance <= 1_000_000):
        raise HTTPException(status_code=400, detail="Balance must be between $1,000 and $1,000,000")

    background_tasks.add_task(
        _run_backtest_task,
        request.period,
        request.timeframe,
        request.initial_balance,
    )

    return {"message": "Backtest started", "status": "running"}


async def _run_backtest_task(period: str, timeframe: str, initial_balance: float):
    global _backtest_running, _last_backtest_result
    _backtest_running = True

    try:
        await ws_manager.send_backtest_progress(5, "Initializing backtest engine...")

        async def progress_cb(pct: int, msg: str):
            await ws_manager.send_backtest_progress(pct, msg)

        await ws_manager.send_backtest_progress(15, "Fetching historical data...")

        result = await trading_engine.run_backtest(
            period=period,
            interval=timeframe,
            initial_balance=initial_balance,
            progress_callback=progress_cb,
        )

        _last_backtest_result = result
        await ws_manager.send_backtest_progress(100, "Backtest complete!")

        # Broadcast result summary
        await ws_manager.broadcast({
            "type": "backtest_complete",
            "data": {
                "total_return_pct": result["total_return_pct"],
                "win_rate_pct": result["win_rate_pct"],
                "total_trades": result["total_trades"],
                "max_drawdown_pct": result["max_drawdown_pct"],
                "challenge_passed": result["challenge_passed"],
            },
            "timestamp": datetime.utcnow().isoformat(),
        })

    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        await ws_manager.broadcast({
            "type": "backtest_error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        })
    finally:
        _backtest_running = False


@router.get("/status")
async def get_backtest_status():
    """Check if a backtest is running."""
    return {
        "running": _backtest_running,
        "has_result": _last_backtest_result is not None,
        "last_run": _last_backtest_result.get("run_at") if _last_backtest_result else None,
    }


@router.get("/result")
async def get_backtest_result():
    """Return the most recent backtest result."""
    if _last_backtest_result is None:
        raise HTTPException(status_code=404, detail="No backtest result available. Run a backtest first.")
    return _last_backtest_result


@router.get("/result/equity-curve")
async def get_equity_curve():
    """Return equity curve data for charting."""
    if not _last_backtest_result:
        raise HTTPException(status_code=404, detail="No backtest result available.")
    return {"equity_curve": _last_backtest_result.get("equity_curve", [])}


@router.get("/result/trade-log")
async def get_trade_log(
    limit: int = Query(100, ge=1, le=1000),
    result_filter: Optional[str] = Query(None, description="WIN or LOSS"),
):
    """Return the trade-by-trade log."""
    if not _last_backtest_result:
        raise HTTPException(status_code=404, detail="No backtest result available.")

    log = _last_backtest_result.get("trade_log", [])
    if result_filter:
        log = [t for t in log if t.get("result") == result_filter.upper()]

    return {"total": len(log), "trades": log[-limit:]}


@router.get("/result/breakdown")
async def get_strategy_breakdown():
    """Return per-strategy and per-asset breakdowns."""
    if not _last_backtest_result:
        raise HTTPException(status_code=404, detail="No backtest result available.")
    return {
        "strategy_breakdown": _last_backtest_result.get("strategy_breakdown", {}),
        "asset_breakdown": _last_backtest_result.get("asset_breakdown", {}),
    }
