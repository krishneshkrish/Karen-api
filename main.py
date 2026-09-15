import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.middleware.rate_limiter import limiter
from app.api.v1 import auth, chat, ml, history, report
from app.core.config import settings
from app.tasks.keep_alive import ping_self

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    keep_alive_task = asyncio.create_task(ping_self())
    yield
    # Shutdown
    keep_alive_task.cancel()
    logger.info("Karen API shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Karen — Emotional support and direction-giving API",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,   # Hide docs in production
    redoc_url=None,
)

# ── Rate limiter ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5180",            # SvelteKit dev
        "https://karen-app.vercel.app",     # Production frontend (update this)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,    prefix="/api/v1")
app.include_router(chat.router,    prefix="/api/v1")
app.include_router(ml.router,      prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(report.router,  prefix="/api/v1")


# ── Health check (used by keep-alive ping) ────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "Karen API is running"}
