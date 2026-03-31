"""
Payment routes — pay to run an agent, check entitlement.

Flow:
  1. Caller POSTs to /payments/agents/{agent_id}/run with their Mainlayer API
     key and the input data.
  2. We charge the caller via Mainlayer, grant an entitlement, then execute a
     stub agent (swap out the stub for a real inference call in production).
  3. The response includes payment details and agent output.
"""

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

router = APIRouter(prefix="/payments", tags=["Payments"])


# ---------------------------------------------------------------------------
# Stub agent executor — replace with real inference logic per agent
# ---------------------------------------------------------------------------


def _execute_agent(agent_record: dict[str, Any], input_data: dict[str, Any]) -> Any:
    """
    Stub: in production, dispatch to the agent's actual inference endpoint
    or run the agent logic here.  Returns a deterministic mock output so the
    marketplace demo is fully functional without external AI backends.
    """
    return {
        "agent": agent_record["name"],
        "status": "completed",
        "result": f"Processed input with {len(input_data)} field(s) successfully.",
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
    """
    Charge the caller's Mainlayer balance and execute the agent.

    The caller must supply their own Mainlayer API key in `payer_api_key`.
    Mainlayer handles the charge atomically — if payment fails the agent
    will not run.
    """
    record = agent_store.get(agent_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    client = get_client()

    # 1. Charge the caller
    try:
        payment = await client.create_payment(
            resource_id=record["resource_id"],
            payer_api_key=body.payer_api_key,
            amount=record["price_per_call"],
            currency=record["currency"],
            metadata=body.metadata,
        )
    except MainlayerError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Payment failed: {exc}",
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
    except MainlayerError:
        # Non-fatal: payment succeeded, log and continue
        pass

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
