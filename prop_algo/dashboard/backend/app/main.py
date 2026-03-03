"""
PropAlgo Trading Dashboard — FastAPI Application
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .core.config import settings
from .core.database import init_db
from .services.scheduler import start_scheduler, stop_scheduler
from .api.routes import signals, backtest, notifications, settings as settings_router, websocket, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting PropAlgo Dashboard...")
    await init_db()
    start_scheduler(settings.LIVE_SCAN_INTERVAL)
    logger.info(f"Live scan scheduler started (every {settings.LIVE_SCAN_INTERVAL}s)")
    yield
    # Shutdown
    stop_scheduler()
    logger.info("PropAlgo Dashboard shut down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Prop Firm Algorithmic Trading Dashboard — Real-time signals, backtest, risk management.",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── Middleware ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ─── Routes ───────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(signals.router, prefix="/api")
app.include_router(backtest.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(websocket.router)
