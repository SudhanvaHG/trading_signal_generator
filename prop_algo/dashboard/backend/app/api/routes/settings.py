"""
Settings API Routes — Risk config, strategy config, assets.
"""

from fastapi import APIRouter
from ...services.trading_engine import trading_engine

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/risk")
async def get_risk_config():
    return trading_engine.get_risk_config()


@router.get("/strategy")
async def get_strategy_config():
    return trading_engine.get_strategy_config()


@router.get("/assets")
async def get_assets():
    return trading_engine.get_assets_config()


@router.get("/all")
async def get_all_settings():
    return {
        "risk": trading_engine.get_risk_config(),
        "strategy": trading_engine.get_strategy_config(),
        "assets": trading_engine.get_assets_config(),
    }
