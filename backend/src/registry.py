import json
import os
from typing import Dict, List, Optional
from .models import Agent


REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "agents.json")


class AgentRegistry:
    """In-memory agent registry with file persistence."""

    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._load()

    def _load(self):
        """Load agents from file if it exists."""
        os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
        if os.path.exists(REGISTRY_FILE):
            try:
                with open(REGISTRY_FILE, "r") as f:
                    data = json.load(f)
                    for item in data:
                        agent = Agent(**item)
                        self._agents[agent.id] = agent
            except (json.JSONDecodeError, Exception):
                pass

    def _save(self):
        """Persist registry to file."""
        os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
        with open(REGISTRY_FILE, "w") as f:
            json.dump([a.model_dump() for a in self._agents.values()], f, indent=2)

    def add(self, agent: Agent) -> Agent:
        self._agents[agent.id] = agent
        self._save()
        return agent

    def get(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def list_all(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Agent]:
        agents = [a for a in self._agents.values() if a.is_active]
        if category:
            agents = [a for a in agents if a.category == category]
        if search:
            q = search.lower()
            agents = [
                a for a in agents
                if q in a.name.lower()
                or q in a.description.lower()
                or any(q in cap.lower() for cap in a.capabilities)
            ]
        return agents

    def increment_call(self, agent_id: str, revenue: float):
        if agent_id in self._agents:
            self._agents[agent_id].call_count += 1
            self._agents[agent_id].total_revenue_usdc += revenue
            self._save()

    def update_resource_id(self, agent_id: str, resource_id: str):
        if agent_id in self._agents:
            self._agents[agent_id].mainlayer_resource_id = resource_id
            self._save()

    def seed_demo_agents(self):
        """Seed the registry with demo agents if empty."""
        if self._agents:
            return

        demos = [
            Agent(
                id="demo-weather-001",
                name="Weather Agent",
                description="Get real-time weather conditions and 7-day forecasts for any city worldwide. Powered by meteorological data.",
                endpoint="http://weather-agent:3001/run",
                price_usdc=0.005,
                fee_model="pay_per_call",
                capabilities=["weather", "forecasting", "climate"],
                category="data",
                author="Mainlayer Labs",
                avatar_url="https://api.dicebear.com/7.x/icons/svg?seed=weather&backgroundColor=dbeafe",
                mainlayer_resource_id="res_weather_demo",
                call_count=1247,
                total_revenue_usdc=6.235,
            ),
            Agent(
                id="demo-summarizer-001",
                name="Summarizer Agent",
                description="Condense long documents, articles, or text into clear, concise summaries. Supports multiple output lengths.",
                endpoint="http://summarizer-agent:3002/run",
                price_usdc=0.008,
                fee_model="pay_per_call",
                capabilities=["summarization", "nlp", "text-processing"],
                category="nlp",
                author="Mainlayer Labs",
                avatar_url="https://api.dicebear.com/7.x/icons/svg?seed=summarizer&backgroundColor=dcfce7",
                mainlayer_resource_id="res_summarizer_demo",
                call_count=892,
                total_revenue_usdc=7.136,
            ),
            Agent(
                id="demo-translator-001",
                name="Translator Agent",
                description="Translate text between 50+ languages with high accuracy. Supports formal and informal register detection.",
                endpoint="http://translator-agent:3003/run",
                price_usdc=0.006,
                fee_model="pay_per_call",
                capabilities=["translation", "nlp", "multilingual"],
                category="nlp",
                author="Mainlayer Labs",
                avatar_url="https://api.dicebear.com/7.x/icons/svg?seed=translator&backgroundColor=fef9c3",
                mainlayer_resource_id="res_translator_demo",
                call_count=2341,
                total_revenue_usdc=14.046,
            ),
        ]
        for agent in demos:
            self._agents[agent.id] = agent
        self._save()


registry = AgentRegistry()
