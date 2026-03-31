"""Agent Marketplace — FastAPI application entry point.

Mainlayer powers all billing: every agent is a Mainlayer resource and
every call is a Mainlayer payment.
"""

import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.routes.agents import router as agents_router
from backend.routes.payments import router as payments_router
from backend.routes.marketplace import router as marketplace_router

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Marketplace",
    description=(
        "A marketplace of AI agents with per-call billing powered by Mainlayer. "
        "Developers publish agents as billable resources; users pay per-call to run them."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow frontend origins
# ---------------------------------------------------------------------------
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
logger.info(f"CORS origins: {CORS_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with clear messaging."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": exc.errors(),
            "message": "Invalid request parameters"
        },
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(agents_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(marketplace_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    """Root endpoint — returns service info."""
    return JSONResponse({
        "service": "agent-marketplace",
        "status": "ok",
        "version": "1.0.0",
        "docs": "/docs",
    })


@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Liveness probe — returns 200 if healthy."""
    return {"status": "ok", "service": "agent-marketplace"}


@app.on_event("startup")
def startup_event():
    """Log startup information."""
    logger.info("Agent Marketplace starting up")
    logger.info(f"API endpoint: /api/v1")
    logger.info(f"Documentation: /docs, /redoc")


@app.on_event("shutdown")
def shutdown_event():
    """Log shutdown."""
    logger.info("Agent Marketplace shutting down")
