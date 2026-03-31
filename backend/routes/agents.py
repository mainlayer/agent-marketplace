"""Agent registration and retrieval routes.

Developers publish AI agents as Mainlayer resources. Each agent is stored
in the local in-memory registry (swap for a database in production) and
mirrored as a Mainlayer resource so per-call billing works out of the box.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from backend.mainlayer import get_client, MainlayerError
from backend.models import (
    AgentListResponse,
    AgentResponse,
    PublishAgentRequest,
)
from backend.store import agent_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["Agents"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_response(record: dict[str, Any]) -> AgentResponse:
    """Convert a store record dict to an AgentResponse model."""
    return AgentResponse(**record)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish a new AI agent",
)
async def publish_agent(body: PublishAgentRequest) -> AgentResponse:
    """Register an AI agent as a Mainlayer resource.

    The agent is stored in the marketplace registry and a corresponding
    Mainlayer resource is created so that per-call payments can be charged
    automatically.

    Args:
        body: Agent registration request with name, description, price, etc.

    Returns:
        The published agent with generated ID and resource_id

    Raises:
        HTTPException: If Mainlayer resource creation fails
    """
    client = get_client()

    try:
        resource = await client.create_resource(
            name=body.name,
            description=body.description,
            price_per_call=body.price_per_call,
            currency="usd",
            metadata={
                "category": body.category,
                "tags": body.tags,
            },
        )
        logger.info(f"Created Mainlayer resource for agent: {body.name}")
    except MainlayerError as exc:
        logger.error(f"Failed to create Mainlayer resource: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to register agent with payment service",
        )

    resource_id: str = resource.get("id", str(uuid.uuid4()))
    agent_id = str(uuid.uuid4())

    record: dict[str, Any] = {
        "id": agent_id,
        "name": body.name,
        "description": body.description,
        "category": body.category,
        "price_per_call": body.price_per_call,
        "currency": "usd",
        "capabilities": [c.model_dump() for c in body.capabilities],
        "tags": body.tags,
        "example_input": body.example_input,
        "example_output": body.example_output,
        "resource_id": resource_id,
        "publisher_id": resource.get("owner_id", "unknown"),
        "created_at": datetime.now(timezone.utc),
        "call_count": 0,
        "rating": None,
    }
    agent_store[agent_id] = record
    logger.info(f"Published agent {agent_id}: {body.name} at ${body.price_per_call}/call")
    return _to_response(record)


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List all published agents",
)
async def list_agents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AgentListResponse:
    """Return a paginated list of all agents in the marketplace."""
    all_agents = list(agent_store.values())
    total = len(all_agents)
    page = all_agents[offset : offset + limit]
    return AgentListResponse(
        agents=[_to_response(r) for r in page],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent details",
)
async def get_agent(agent_id: str) -> AgentResponse:
    """Retrieve full details for a specific agent by ID."""
    record = agent_store.get(agent_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )
    return _to_response(record)
