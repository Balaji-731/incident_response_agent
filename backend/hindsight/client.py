import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class HindsightClient:
    """
    Client for interacting with Vectorize Hindsight Memory API.
    Supports persistent organizational memory retain & recall with retry logic.
    """
    def __init__(self):
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
        self.api_url = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io").rstrip('/')
        self.bank_id = os.getenv("HINDSIGHT_BANK_ID", "incident-response-bank").strip()
        
        self.is_mock = (
            not self.api_key or 
            self.api_key.startswith("your_") or 
            self.api_key == "placeholder"
        )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def retain(self, memory_text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retain a confirmed incident experience in Hindsight Cloud.
        """
        if self.is_mock:
            print(f"[Hindsight Retain Mock] Retained: '{memory_text[:80]}...'")
            return {"status": "success", "mode": "mock", "retained_content": memory_text}

        sanitized_metadata = {
            k: (", ".join(v) if isinstance(v, list) else str(v))
            for k, v in (metadata or {}).items()
        }

        url = f"{self.api_url}/v1/default/banks/{self.bank_id}/memories"
        payload = {
            "items": [
                {
                    "content": memory_text,
                    "metadata": sanitized_metadata
                }
            ]
        }

        # Retry loop for network resiliency
        for attempt in range(1, 3):
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(url, json=payload, headers=self.headers)
                    response.raise_for_status()
                    data = response.json()
                    print(f"[Hindsight Retain Cloud] Retained memory successfully into bank '{self.bank_id}'")
                    return data
                except Exception as err:
                    print(f"[Hindsight Retain Error (Attempt {attempt})]: {err}")
                    if attempt < 2:
                        await asyncio.sleep(1.0)
                    else:
                        return {"status": "error", "message": str(err)}

    async def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Recall relevant past incidents from Hindsight Cloud with retry logic.
        """
        if self.is_mock:
            print(f"[Hindsight Recall Mock] Searching for: '{query}'")
            return self._get_mock_memories(query)

        url = f"{self.api_url}/v1/default/banks/{self.bank_id}/memories/recall"
        payload = {
            "query": query,
            "top_k": top_k
        }

        for attempt in range(1, 3):
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(url, json=payload, headers=self.headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    raw_results = data.get("results", [])
                    formatted_memories = []
                    for item in raw_results:
                        scores = item.get("scores", {})
                        final_score = scores.get("final") or scores.get("semantic", 0.0)
                        formatted_memories.append({
                            "memory_id": item.get("id"),
                            "content": item.get("text"),
                            "score": final_score,
                            "type": item.get("type"),
                            "entities": item.get("entities", []),
                            "metadata": item.get("metadata") or {}
                        })
                    return formatted_memories
                except Exception as err:
                    print(f"[Hindsight Recall Error (Attempt {attempt})]: {err}")
                    if attempt < 2:
                        await asyncio.sleep(1.0)
                    else:
                        return []

    def _get_mock_memories(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        if "auth" in query_lower or "redis" in query_lower or "500" in query_lower:
            return [{
                "memory_id": "MEM-3001",
                "content": "Incident INC-3001 (Auth Service 500): Auth tokens failing verification. Confirmed root cause: Redis connection pool exhausted. Resolution: Increased max connections.",
                "score": 0.94,
                "metadata": {"service": "auth-service"}
            }]
        elif "database" in query_lower or "cuda" in query_lower or "oom" in query_lower or "503" in query_lower:
            return [{
                "memory_id": "MEM-1080",
                "content": "Incident INC-1080 (Payment API 503): Database connection timeout. Attempted pod restart: FAILED. Confirmed root cause: Connection pool exhausted. Resolution: Increased pool size to 100.",
                "score": 0.89,
                "metadata": {"service": "payment-api"}
            }]
        return []

hindsight_client = HindsightClient()