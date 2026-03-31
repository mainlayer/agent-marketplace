"""Pydantic models for the agent marketplace.

Includes request/response models for agents, payments, entitlements, and search.
All models validate input and provide clear error messages.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Agent / Resource models
# ---------------------------------------------------------------------------


class AgentCapability(BaseModel):
    name: str
    description: str


class PublishAgentRequest(BaseModel):
    """Request to publish a new agent to the marketplace.

    Agents are registered as Mainlayer resources with per-call billing.
    """

    name: str = Field(..., min_length=3, max_length=80, description="Agent display name")
    description: str = Field(..., min_length=10, max_length=1000, description="What the agent does")
    category: str = Field(..., min_length=2, max_length=50, description="Category (e.g., NLP, Scheduling)")
    price_per_call: float = Field(..., gt=0, description="Price in USD per API call")
    capabilities: list[AgentCapability] = Field(default_factory=list, description="Agent capabilities")
    tags: list[str] = Field(default_factory=list, description="Search tags")
    example_input: Optional[str] = Field(None, description="Example JSON input for testing")
    example_output: Optional[str] = Field(None, description="Example JSON output")

    @field_validator("tags", mode="before")
    @classmethod
    def tags_limit(cls, v: list[str]) -> list[str]:
        """Validate tag count and normalize."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return [t.strip().lower() for t in v if t.strip()]


class AgentResponse(BaseModel):
    """Full details of a published agent in the marketplace."""

    id: str = Field(description="Unique agent ID")
    name: str
    description: str
    category: str
    price_per_call: float = Field(description="Price in USD")
    currency: str = "usd"
    capabilities: list[AgentCapability]
    tags: list[str]
    example_input: Optional[str]
    example_output: Optional[str]
    resource_id: str = Field(description="Mainlayer resource ID for billing")
    publisher_id: str = Field(description="Owner's Mainlayer account ID")
    created_at: datetime
    call_count: int = Field(0, ge=0, description="Number of times called")
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Average user rating")


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Payment models
# ---------------------------------------------------------------------------


class RunAgentRequest(BaseModel):
    """Request body to pay for and run an agent."""

    payer_api_key: str = Field(..., min_length=10, description="Caller's Mainlayer API key")
    input_data: dict[str, Any] = Field(
        ..., description="Input payload forwarded to the agent"
    )
    metadata: Optional[dict[str, Any]] = None


class PaymentStatus(BaseModel):
    payment_id: str
    status: str  # pending | completed | failed
    amount: float
    currency: str
    resource_id: str
    created_at: datetime


class RunAgentResponse(BaseModel):
    payment_id: str
    payment_status: str
    agent_id: str
    output: Any
    credits_used: float
    currency: str


# ---------------------------------------------------------------------------
# Entitlement models
# ---------------------------------------------------------------------------


class EntitlementRequest(BaseModel):
    payer_api_key: str = Field(..., min_length=10)
    calls_to_grant: int = Field(default=1, ge=1, le=1000)


class EntitlementResponse(BaseModel):
    entitled: bool
    calls_remaining: int
    resource_id: str
    payer_api_key: str


# ---------------------------------------------------------------------------
# Marketplace / Discovery models
# ---------------------------------------------------------------------------


class SearchAgentsRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    sort_by: str = Field(default="created_at", pattern="^(created_at|price|rating|call_count)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CategorySummary(BaseModel):
    category: str
    count: int


class MarketplaceStatsResponse(BaseModel):
    total_agents: int
    total_calls: int
    categories: list[CategorySummary]
    featured_agent_ids: list[str]


# ---------------------------------------------------------------------------
# Error model
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[Any] = None
    code: Optional[str] = None
