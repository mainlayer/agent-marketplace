"""
Mainlayer API client — Stripe for AI agents.
Base URL: https://api.mainlayer.xyz
"""

import os
import httpx
from typing import Any, Optional


MAINLAYER_BASE_URL = os.getenv("MAINLAYER_BASE_URL", "https://api.mainlayer.xyz")
MAINLAYER_API_KEY = os.getenv("MAINLAYER_API_KEY", "")


class MainlayerError(Exception):
    """Raised when the Mainlayer API returns an error."""

    def __init__(self, message: str, status_code: int = 0, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class MainlayerClient:
    """Async HTTP client for the Mainlayer payment infrastructure API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or MAINLAYER_API_KEY
        self.base_url = (base_url or MAINLAYER_BASE_URL).rstrip("/")
        if not self.api_key:
            raise MainlayerError("MAINLAYER_API_KEY is not set")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[dict] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                params=params,
            )
        if not response.is_success:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise MainlayerError(
                f"Mainlayer API error: {response.status_code}",
                status_code=response.status_code,
                detail=detail,
            )
        return response.json()

    # ------------------------------------------------------------------
    # Resources — agents published as billable resources
    # ------------------------------------------------------------------

    async def create_resource(
        self,
        name: str,
        description: str,
        price_per_call: float,
        currency: str = "usd",
        metadata: Optional[dict] = None,
    ) -> dict:
        """Register an AI agent as a Mainlayer resource."""
        payload: dict[str, Any] = {
            "name": name,
            "description": description,
            "price": {"amount": price_per_call, "currency": currency},
        }
        if metadata:
            payload["metadata"] = metadata
        return await self._request("POST", "/v1/resources", json=payload)

    async def get_resource(self, resource_id: str) -> dict:
        return await self._request("GET", f"/v1/resources/{resource_id}")

    async def list_resources(self, limit: int = 50, offset: int = 0) -> dict:
        return await self._request(
            "GET", "/v1/resources", params={"limit": limit, "offset": offset}
        )

    # ------------------------------------------------------------------
    # Payments — charge a user to run an agent
    # ------------------------------------------------------------------

    async def create_payment(
        self,
        resource_id: str,
        payer_api_key: str,
        amount: float,
        currency: str = "usd",
        metadata: Optional[dict] = None,
    ) -> dict:
        """Charge a user's Mainlayer balance for running an agent."""
        payload: dict[str, Any] = {
            "resource_id": resource_id,
            "payer_api_key": payer_api_key,
            "amount": {"value": amount, "currency": currency},
        }
        if metadata:
            payload["metadata"] = metadata
        return await self._request("POST", "/v1/payments", json=payload)

    async def get_payment(self, payment_id: str) -> dict:
        return await self._request("GET", f"/v1/payments/{payment_id}")

    # ------------------------------------------------------------------
    # Entitlements — verify the caller has paid / has access
    # ------------------------------------------------------------------

    async def check_entitlement(
        self, resource_id: str, payer_api_key: str
    ) -> dict:
        """Check whether a user is entitled to call a resource."""
        return await self._request(
            "GET",
            f"/v1/entitlements/{resource_id}",
            params={"payer_api_key": payer_api_key},
        )

    async def create_entitlement(
        self,
        resource_id: str,
        payer_api_key: str,
        calls_granted: int = 1,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Grant entitlement after successful payment."""
        payload: dict[str, Any] = {
            "resource_id": resource_id,
            "payer_api_key": payer_api_key,
            "calls_granted": calls_granted,
        }
        if metadata:
            payload["metadata"] = metadata
        return await self._request("POST", "/v1/entitlements", json=payload)


# Module-level singleton — callers import and use this directly
def get_client() -> MainlayerClient:
    """Return a configured Mainlayer client (raises if API key missing)."""
    return MainlayerClient()
