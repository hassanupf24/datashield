"""
DATASHIELD - Enterprise AI Data Governance Platform
Main FastAPI Application Entrypoint

Production-grade application with:
- Structured JSON logging with trace correlation
- Security middleware (CORS, rate limiting, trace IDs)
- RBAC-protected API routes
- Graceful startup/shutdown lifecycle
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import close_db, init_db
from app.logging_config import (
    generate_trace_id, get_logger, setup_logging,
    trace_id_var, user_id_var,
)

# Import all API routers
from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.assets import router as assets_router
from app.api.classification import router as classification_router
from app.api.risk import router as risk_router
from app.api.policies import router as policies_router
from app.api.audit import router as audit_router
from app.api.lineage import router as lineage_router
from app.api.dashboard import router as dashboard_router

settings = get_settings()

# Initialize structured logging
setup_logging(log_level=settings.LOG_LEVEL, log_format="json" if settings.is_production else "console")
logger = get_logger("datashield")

# Track uptime
_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    global _start_time
    _start_time = time.time()

    logger.info(
        "application_starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )

    # Initialize database
    await init_db()
    logger.info("database_ready")

    yield

    # Cleanup
    await close_db()
    logger.info("application_shutdown", uptime_seconds=round(time.time() - _start_time, 2))


# Create FastAPI application
app = FastAPI(
    title="DATASHIELD Governance API",
    description="Enterprise AI Data Governance Platform - Secure by Design",
    version=settings.APP_VERSION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-Id"],
)


# --- Request Tracing & Logging Middleware ---
@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    """
    Inject trace ID into every request for end-to-end correlation.
    Log request/response metrics for observability.
    """
    trace_id = request.headers.get("X-Trace-Id") or generate_trace_id()
    request.state.trace_id = trace_id
    trace_id_var.set(trace_id)

    # Extract user ID from JWT if present
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.security import decode_token
            payload = decode_token(auth_header[7:])
            user_id_var.set(payload.get("sub", "anonymous"))
        except Exception:
            user_id_var.set("anonymous")

    start_time = time.time()

    try:
        response: Response = await call_next(request)
    except Exception as exc:
        logger.error(
            "request_error",
            method=request.method,
            path=request.url.path,
            error=str(exc),
        )
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "trace_id": trace_id},
        )

    duration = round((time.time() - start_time) * 1000, 2)

    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Response-Time"] = f"{duration}ms"

    # Log request (skip health checks to reduce noise)
    if request.url.path not in ("/health", "/healthz"):
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration,
            client_ip=request.client.host if request.client else "unknown",
        )

    return response


# --- Rate Limiting Middleware (Simple in-memory) ---
_rate_limit_store: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple IP-based rate limiting."""
    if request.url.path in ("/health", "/healthz", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60  # 1 minute

    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []

    # Clean old entries
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if t > now - window
    ]

    if len(_rate_limit_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        logger.warning("rate_limit_exceeded", client_ip=client_ip)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."},
        )

    _rate_limit_store[client_ip].append(now)
    return await call_next(request)


# --- Health Check ---
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for load balancers and orchestrators."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME,
        "uptime_seconds": round(time.time() - _start_time, 2),
    }


# --- Register API Routers ---
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)
app.include_router(assets_router, prefix=API_PREFIX)
app.include_router(classification_router, prefix=API_PREFIX)
app.include_router(risk_router, prefix=API_PREFIX)
app.include_router(policies_router, prefix=API_PREFIX)
app.include_router(audit_router, prefix=API_PREFIX)
app.include_router(lineage_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)


# --- Root ---
@app.get("/", tags=["System"])
async def root():
    """API root endpoint."""
    return {
        "service": "DATASHIELD Governance API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
