"""
WebSocket Route
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from ...core.websocket_manager import ws_manager

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send welcome message with current state
        from ...services.trading_engine import trading_engine
        from ...services.scheduler import get_scheduler_status
        import json

        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "PropAlgo WebSocket connected.",
            "scheduler": get_scheduler_status(),
            "signals_available": len(trading_engine.last_signals),
        }, default=str))

        # Keep alive — listen for client pings
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)
