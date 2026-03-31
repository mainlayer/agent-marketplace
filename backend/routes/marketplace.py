"""
Marketplace discovery routes — browse and search agents.
"""

from fastapi import APIRouter, Query
from typing import Optional

from backend.models import (
    AgentListResponse,
    AgentResponse,
    CategorySummary,
    MarketplaceStatsResponse,
)
from backend.store import agent_store

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _matches(record: dict, query: Optional[str], category: Optional[str], tags: list[str]) -> bool:
    if category and record.get("category", "").lower() != category.lower():
        return False
    if tags:
        agent_tags = set(record.get("tags", []))
        if not set(t.lower() for t in tags).issubset(agent_tags):
            return False
    if query:
        q = query.lower()
        searchable = (
            record.get("name", "")
            + " "
            + record.get("description", "")
            + " "
            + " ".join(record.get("tags", []))
        ).lower()
        if q not in searchable:
            return False
    return True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/discover",
    response_model=AgentListResponse,
    summary="Browse and search agents",
)
async def discover_agents(
    query: Optional[str] = Query(None, description="Full-text search across name, description, tags"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: list[str] = Query(default=[], description="Filter by tags (all must match)"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("created_at", pattern="^(created_at|price_per_call|call_count)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AgentListResponse:
    """
    Discover agents with optional full-text search, category and tag
    filtering, price range filtering, and flexible sorting.
    """
    all_agents = list(agent_store.values())

    # Filter
    filtered = [r for r in all_agents if _matches(r, query, category, tags)]

    if min_price is not None:
        filtered = [r for r in filtered if r["price_per_call"] >= min_price]
    if max_price is not None:
        filtered = [r for r in filtered if r["price_per_call"] <= max_price]

    # Sort
    reverse = sort_order == "desc"
    if sort_by == "price_per_call":
        filtered.sort(key=lambda r: r.get("price_per_call", 0), reverse=reverse)
    elif sort_by == "call_count":
        filtered.sort(key=lambda r: r.get("call_count", 0), reverse=reverse)
    else:
        # created_at — sort as ISO string (consistent since we use datetime objects)
        filtered.sort(
            key=lambda r: r.get("created_at", ""),
            reverse=reverse,
        )

    total = len(filtered)
    page = filtered[offset : offset + limit]

    return AgentListResponse(
        agents=[AgentResponse(**r) for r in page],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/stats",
    response_model=MarketplaceStatsResponse,
    summary="Marketplace-level statistics",
)
async def marketplace_stats() -> MarketplaceStatsResponse:
    """Return aggregate statistics useful for dashboard widgets."""
    all_agents = list(agent_store.values())

    total_calls = sum(r.get("call_count", 0) for r in all_agents)

    category_counts: dict[str, int] = {}
    for r in all_agents:
        cat = r.get("category", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    categories = [
        CategorySummary(category=cat, count=count)
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])
    ]

    # Featured = top 3 by call count
    featured = sorted(all_agents, key=lambda r: r.get("call_count", 0), reverse=True)[:3]

    return MarketplaceStatsResponse(
        total_agents=len(all_agents),
        total_calls=total_calls,
        categories=categories,
        featured_agent_ids=[r["id"] for r in featured],
    )


@router.get(
    "/categories",
    response_model=list[str],
    summary="List available categories",
)
async def list_categories() -> list[str]:
    """Return a deduplicated list of all categories in the marketplace."""
    cats = sorted({r.get("category", "Other") for r in agent_store.values()})
    return cats
