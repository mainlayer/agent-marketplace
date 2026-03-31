"""
Mainlayer API client — payment infrastructure for AI agents.
Base URL: https://api.mainlayer.fr

Handles resource registration, payments, entitlements, and usage tracking.
"""

import logging
import os
import httpx
from typing import Any, Optional

logger = logging.getLogger(__name__)

MAINLAYER_BASE_URL = os.getenv("MAINLAYER_BASE_URL", "https://api.mainlayer.fr")
MAINLAYER_API_KEY = os.getenv("MAINLAYER_API_KEY", "")
REQUEST_TIMEOUT = 30.0


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
            raise MainlayerError("MAINLAYER_API_KEY environment variable not set")

    def _headers(self) -> dict[str, str]:
        """Build request headers with Bearer token authentication."""
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
        """Execute an HTTP request against the Mainlayer API.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            path: API endpoint path (e.g., '/v1/resources')
            json: Request body (optional)
            params: Query parameters (optional)

        Returns:
            Parsed JSON response

        Raises:
            MainlayerError: If the API returns an error status
        """
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
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
                logger.error(f"Mainlayer API error: {response.status_code} - {detail}")
                raise MainlayerError(
                    f"Mainlayer API error: {response.status_code}",
                    status_code=response.status_code,
                    detail=detail,
                )
            return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"Mainlayer API timeout: {e}")
            raise MainlayerError(
                f"Mainlayer API timeout after {REQUEST_TIMEOUT}s",
                status_code=504,
                detail=str(e),
            )

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
        """Register an AI agent as a Mainlayer resource.

        Args:
            name: Agent name
            description: Agent description
            price_per_call: Price in the specified currency
            currency: Currency code (default: USD)
            metadata: Optional metadata dict

        Returns:
            Resource record with 'id' and other fields
        """
        payload: dict[str, Any] = {
            "name": name,
            "description": description,
            "price": {"amount": price_per_call, "currency": currency},
        }
        if metadata:
            payload["metadata"] = metadata
        return await self._request("POST", "/v1/resources", json=payload)

    async def get_resource(self, resource_id: str) -> dict:
        """Retrieve a resource by ID."""
        return await self._request("GET", f"/v1/resources/{resource_id}")

    async def list_resources(self, limit: int = 50, offset: int = 0) -> dict:
        """List all resources with pagination."""
        return await self._request(
            "GET", "/v1/resources", params={"limit": limit, "offset": offset}
        )

    async def update_resource(
        self,
        resource_id: str,
        price_per_call: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Update resource pricing or metadata."""
        payload: dict[str, Any] = {}
        if price_per_call is not None:
            payload["price"] = {"amount": price_per_call, "currency": "usd"}
        if metadata:
            payload["metadata"] = metadata
        return await self._request("PUT", f"/v1/resources/{resource_id}", json=payload)

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
        """Charge a user's Mainlayer balance for running an agent.

        Args:
            resource_id: The resource being charged for
            payer_api_key: The payer's Mainlayer API key
            amount: Amount to charge
            currency: Currency (default: USD)
            metadata: Optional metadata (e.g., agent run ID)

        Returns:
            Payment record with status and payment ID
        """
        payload: dict[str, Any] = {
            "resource_id": resource_id,
            "payer_api_key": payer_api_key,
            "amount": {"value": amount, "currency": currency},
        }
        if metadata:
            payload["metadata"] = metadata
        return await self._request("POST", "/v1/payments", json=payload)

    async def get_payment(self, payment_id: str) -> dict:
        """Retrieve a payment by ID."""
        return await self._request("GET", f"/v1/payments/{payment_id}")

    # ------------------------------------------------------------------
    # Entitlements — verify the caller has paid / has access
    # ------------------------------------------------------------------

    async def check_entitlement(
        self, resource_id: str, payer_api_key: str
    ) -> dict:
        """Check whether a user is entitled to call a resource.

        Args:
            resource_id: The resource to check entitlement for
            payer_api_key: The payer's Mainlayer API key

        Returns:
            Dict with 'entitled' (bool) and 'calls_remaining' (int)
        """
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
        """Grant entitlement (free calls) or record payment entitlement.

        Args:
            resource_id: The resource to grant access to
            payer_api_key: The payer's Mainlayer API key
            calls_granted: Number of free calls to grant
            metadata: Optional metadata

        Returns:
            Entitlement record with calls_remaining
        """
        payload: dict[str, Any] = {
            "resource_id": resource_id,
            "payer_api_key": payer_api_key,
            "calls_granted": calls_granted,
        }
        if metadata:
            payload["metadata"] = metadata
        return await self._request("POST", "/v1/entitlements", json=payload)


# Module-level factory — creates and caches a Mainlayer client
_client: Optional[MainlayerClient] = None


def get_client() -> MainlayerClient:
    """Return a configured Mainlayer client (raises if API key missing).

    Uses module-level caching to avoid recreating the client on every request.
    """
    global _client
    if _client is None:
        _client = MainlayerClient()
    return _client
