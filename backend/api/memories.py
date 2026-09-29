from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from backend.hindsight.client import hindsight_client

router = APIRouter(prefix="/api/memories", tags=["memories"])

@router.get("/search")
async def search_memories_endpoint(
    q: str = Query(..., description="Search query string"),
    top_k: int = Query(default=5, ge=1, le=20)
):
    """
    Search Vectorize Hindsight Cloud bank for past incident experiences, resolutions, and runbooks.
    """
    memories = await hindsight_client.recall(query=q, top_k=top_k)
    return {
        "query": q,
        "results_count": len(memories),
        "memories": memories
    }

@router.get("/status")
def get_hindsight_status():
    """
    Returns Hindsight Memory Bank connection configuration & status.
    """
    return {
        "bank_id": hindsight_client.bank_id,
        "api_url": hindsight_client.api_url,
        "is_mock": hindsight_client.is_mock,
        "connected": not hindsight_client.is_mock
    }