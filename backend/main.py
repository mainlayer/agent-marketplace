"""
Agent Marketplace — FastAPI application entry point.

Mainlayer powers all billing: every agent is a Mainlayer resource and
every call is a Mainlayer payment.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routes.agents import router as agents_router
from backend.routes.payments import router as payments_router
from backend.routes.marketplace import router as marketplace_router

app = FastAPI(
    title="Agent Marketplace",
    description=(
        "A marketplace of AI agents with inter-agent payments powered by Mainlayer. "
        "Developers publish agents as billable resources; users pay per-call to run them."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow the React dev server and any production frontend origin
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return JSONResponse({"service": "agent-marketplace", "status": "ok", "version": "1.0.0"})


@app.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}
