import httpx
import os
from typing import Optional


MAINLAYER_BASE_URL = "https://api.mainlayer.xyz"


class MainlayerClient:
    def __init__(self):
        self.api_key = os.getenv("MAINLAYER_API_KEY", "")
        self.base_url = MAINLAYER_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def register_resource(
        self,
        name: str,
        description: str,
        price_usdc: float,
        fee_model: str = "pay_per_call",
    ) -> dict:
        """Register an agent as a Mainlayer resource."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/resources",
                    headers=self.headers,
                    json={
                        "name": name,
                        "description": description,
                        "price_usdc": price_usdc,
                        "fee_model": fee_model,
                    },
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # If API key is not set or invalid, return a mock resource ID for demo
                if not self.api_key or self.api_key == "ml_...":
                    import uuid
                    return {"resource_id": f"res_{uuid.uuid4().hex[:12]}", "mock": True}
                raise ValueError(f"Mainlayer API error: {e.response.text}") from e
            except httpx.RequestError:
                # Network error — return mock for demo purposes
                import uuid
                return {"resource_id": f"res_{uuid.uuid4().hex[:12]}", "mock": True}

    async def check_entitlement(
        self, resource_id: str, payer_wallet: str
    ) -> bool:
        """Check if a payer has an active entitlement for a resource."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/entitlements/check",
                    headers=self.headers,
                    params={"resource_id": resource_id, "payer_wallet": payer_wallet},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("entitled", False)
                return False
            except (httpx.HTTPStatusError, httpx.RequestError):
                # In demo mode without a real API key, allow calls
                return not self.api_key or self.api_key in ("ml_...", "")

    async def pay(self, resource_id: str, payer_wallet: str) -> dict:
        """Process a payment for a resource."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pay",
                    headers=self.headers,
                    json={"resource_id": resource_id, "payer_wallet": payer_wallet},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise ValueError(f"Payment failed: {e.response.text}") from e

    async def get_analytics(self) -> dict:
        """Get revenue analytics."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/analytics",
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError):
                return {"total_revenue_usdc": 0, "total_calls": 0, "mock": True}

    async def discover(self, query: str) -> list:
        """Search agents via Mainlayer discovery."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/discover",
                    headers=self.headers,
                    params={"q": query},
                )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError):
                return []


mainlayer = MainlayerClient()
