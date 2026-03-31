from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class AgentRegistration(BaseModel):
    name: str
    description: str
    endpoint: str
    price_usdc: float = Field(gt=0, description="Price per call in USDC")
    fee_model: str = Field(default="pay_per_call")
    capabilities: List[str] = []
    category: str = "general"
    author: Optional[str] = None
    avatar_url: Optional[str] = None


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    endpoint: str
    price_usdc: float
    fee_model: str = "pay_per_call"
    capabilities: List[str] = []
    category: str = "general"
    author: Optional[str] = None
    avatar_url: Optional[str] = None
    mainlayer_resource_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    call_count: int = 0
    total_revenue_usdc: float = 0.0
    is_active: bool = True


class AgentCallRequest(BaseModel):
    input: str


class AgentCallResponse(BaseModel):
    agent_id: str
    result: str
    latency_ms: int
    cost_usdc: float


class AgentStats(BaseModel):
    agent_id: str
    name: str
    call_count: int
    total_revenue_usdc: float
    mainlayer_resource_id: Optional[str]
