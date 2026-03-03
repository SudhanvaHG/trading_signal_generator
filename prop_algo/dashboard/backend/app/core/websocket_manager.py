"""
WebSocket Connection Manager
Broadcasts real-time signals and updates to all connected dashboard clients.
"""

from fastapi import WebSocket
from typing import Dict, List, Set
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        if not self.active_connections:
            return

        payload = json.dumps(message, default=str)
        disconnected = []

        for ws in self.active_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)

        # Clean up broken connections
        async with self._lock:
            for ws in disconnected:
                if ws in self.active_connections:
                    self.active_connections.remove(ws)

    async def send_signal(self, signal_data: dict):
        """Broadcast a new trading signal."""
        await self.broadcast({
            "type": "signal",
            "data": signal_data,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def send_scan_status(self, scan_num: int, status: str, summary: dict = None):
        """Broadcast scan status update."""
        await self.broadcast({
            "type": "scan_status",
            "scan_number": scan_num,
            "status": status,
            "summary": summary or {},
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def send_risk_alert(self, alert_type: str, message: str, data: dict = None):
        """Broadcast a risk management alert."""
        await self.broadcast({
            "type": "risk_alert",
            "alert_type": alert_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def send_backtest_progress(self, progress: int, message: str):
        """Broadcast backtest progress."""
        await self.broadcast({
            "type": "backtest_progress",
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        })

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Singleton instance
ws_manager = WebSocketManager()
