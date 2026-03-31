"""Payment routes — pay to run an agent, check entitlement.

Flow:
  1. Caller POSTs to /payments/agents/{agent_id}/run with their Mainlayer API
     key and the input data.
  2. We charge the caller via Mainlayer, grant an entitlement, then execute the
     agent (stub in demo, real inference in production).
  3. The response includes payment details and agent output.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status

from backend.mainlayer import get_client, MainlayerError
from backend.models import (
    EntitlementRequest,
    EntitlementResponse,
    RunAgentRequest,
    RunAgentResponse,
)
from backend.store import agent_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


# ---------------------------------------------------------------------------
# Agent executor — replace with real inference logic per agent
# ---------------------------------------------------------------------------


def _execute_agent(agent_record: dict[str, Any], input_data: dict[str, Any]) -> Any:
    """Execute agent logic (stub version for demo).

    In production, replace this with:
    - HTTP calls to an inference service
    - LLM API calls (Claude, OpenAI, Ollama, etc.)
    - Custom business logic
    - Job queue submissions

    Args:
        agent_record: The agent's metadata from the store
        input_data: The caller's input payload

    Returns:
        Agent output dict with status and result fields
    """
    # Stub implementation for demo purposes
    return {
        "agent": agent_record["name"],
        "status": "completed",
        "result": f"Processed {len(input_data)} field(s) successfully.",
        "input_echo": input_data,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/agents/{agent_id}/run",
    response_model=RunAgentResponse,
    summary="Pay to run an agent",
)
async def run_agent(agent_id: str, body: RunAgentRequest) -> RunAgentResponse:
    """Charge the caller's Mainlayer balance and execute the agent.

    The caller must supply their own Mainlayer API key in `payer_api_key`.
    Mainlayer handles the charge atomically — if payment fails the agent
    will not run.

    Args:
        agent_id: The agent to run
        body: Request with payer_api_key and input_data

    Returns:
        Payment status, payment ID, and agent output

    Raises:
        HTTPException: If agent not found or payment fails
    """
    record = agent_store.get(agent_id)
    if not record:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    client = get_client()

    # 1. Charge the caller via Mainlayer
    try:
        payment = await client.create_payment(
            resource_id=record["resource_id"],
            payer_api_key=body.payer_api_key,
            amount=record["price_per_call"],
            currency=record["currency"],
            metadata=body.metadata,
        )
        logger.info(
            f"Payment successful: {record['name']} "
            f"(${record['price_per_call']})"
        )
    except MainlayerError as exc:
        logger.error(f"Payment failed for agent {agent_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Payment failed. Check your Mainlayer balance and API key.",
        )

    payment_id: str = payment.get("id", "unknown")
    payment_status: str = payment.get("status", "completed")

    # 2. Grant entitlement so subsequent entitlement checks pass
    try:
        await client.create_entitlement(
            resource_id=record["resource_id"],
            payer_api_key=body.payer_api_key,
            calls_granted=1,
            metadata={"payment_id": payment_id},
        )
    except MainlayerError as e:
        # Non-fatal: payment succeeded, entitlement grant failed. Log and continue.
        logger.warning(f"Entitlement grant failed (non-fatal): {e}")

    # 3. Execute the agent
    output = _execute_agent(record, body.input_data)

    # 4. Update call counter
    record["call_count"] = record.get("call_count", 0) + 1

    return RunAgentResponse(
        payment_id=payment_id,
        payment_status=payment_status,
        agent_id=agent_id,
        output=output,
        credits_used=record["price_per_call"],
        currency=record["currency"],
    )


@router.get(
    "/agents/{agent_id}/entitlement",
    response_model=EntitlementResponse,
    summary="Check if a user is entitled to run an agent",
)
async def check_entitlement(agent_id: str, payer_api_key: str) -> EntitlementResponse:
    """Verify that a payer has remaining calls for the given agent."""
    record = agent_store.get(agent_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    client = get_client()
    try:
        result = await client.check_entitlement(
            resource_id=record["resource_id"],
            payer_api_key=payer_api_key,
        )
    except MainlayerError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Entitlement check failed: {exc}",
        )

    return EntitlementResponse(
        entitled=result.get("entitled", False),
        calls_remaining=result.get("calls_remaining", 0),
        resource_id=record["resource_id"],
        payer_api_key=payer_api_key,
    )


@router.post(
    "/agents/{agent_id}/entitlement",
    response_model=EntitlementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant entitlement (admin/test helper)",
)
async def grant_entitlement(
    agent_id: str, body: EntitlementRequest
) -> EntitlementResponse:
    """
    Manually grant entitlement for a payer.  Useful for testing or gifting
    free calls without charging a payment method.
    """
    record = agent_store.get(agent_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    client = get_client()
    try:
        result = await client.create_entitlement(
            resource_id=record["resource_id"],
            payer_api_key=body.payer_api_key,
            calls_granted=body.calls_to_grant,
        )
    except MainlayerError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Entitlement grant failed: {exc}",
        )

    return EntitlementResponse(
        entitled=True,
        calls_remaining=result.get("calls_remaining", body.calls_to_grant),
        resource_id=record["resource_id"],
        payer_api_key=body.payer_api_key,
    )
