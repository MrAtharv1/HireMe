"""
FastAPI application entrypoint.

Configures:
- CORS middleware
- Lifespan events (DB init / teardown, directory bootstrap)
- Global exception handlers
- Router mounting
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.database import close_db, init_db
import app.models.db_models  # noqa: F401 — registers ORM classes with Base.metadata
from app.services.scheduler import start_scheduler, stop_scheduler

# Import all routers
from app.routers import jobs, resume, applications, profiles, auth


# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)
logger = logging.getLogger(__name__)


# ── Logging Middleware ───────────────────────────────────────────────────
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with method, path, status code, duration, and
    client IP. Useful for debugging slow endpoints and tracing errors.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        query = f"?{request.url.query}" if request.url.query else ""

        # Log incoming request
        logger.info(
            "→  %s %s%s  (client=%s)",
            request.method,
            request.url.path,
            query,
            client_ip,
        )

        # Log request headers in DEBUG mode
        if settings.DEBUG:
            logger.debug(
                "   headers: content-type=%s  content-length=%s  user-agent=%s",
                request.headers.get("content-type", "-"),
                request.headers.get("content-length", "-"),
                request.headers.get("user-agent", "-"),
            )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "✗  %s %s  → UNHANDLED EXCEPTION after %.1fms: %s",
                request.method,
                request.url.path,
                duration_ms,
                exc,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        log_fn = logger.warning if response.status_code >= 400 else logger.info
        log_fn(
            "←  %s %s  → %d  (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response


# ── Lifespan ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("🚀  %s starting up (env=%s)", settings.APP_NAME, settings.APP_ENV)
    settings.ensure_dirs()
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()
    await close_db()
    logger.info("🛑  %s shut down.", settings.APP_NAME)


# ── App Factory ──────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "HireMe AI backend — AI-driven Fresher Job Discovery & ATS Resume Tailoring Platform."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Middleware (order matters: last added = first executed) ───────────────
# Logging runs first, then CORS.
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handlers ───────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 422 with a cleaner error payload."""
    errors = []
    for err in exc.errors():
        errors.append(
            {
                "field": " → ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": "Validation error", "errors": errors},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
        },
    )


# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1")
app.include_router(resume.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(profiles.router, prefix="/api/v1")

# ── Health Check ─────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "app": settings.APP_NAME, "env": settings.APP_ENV}