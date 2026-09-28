import asyncio
from backend.hindsight.client import hindsight_client

async def test_hindsight_flow():
    print("--- 1. Testing Hindsight Retain ---")
    memory_text = (
        "Incident INC-3001 (Auth Service 500): Auth tokens failing verification. "
        "Attempted cache clear: FAILED. "
        "Confirmed root cause: Redis connection pool exhausted. "
        "Resolution: Restarted Redis cluster nodes and increased max connections."
    )
    result = await hindsight_client.retain(memory_text, {"service": "auth-service"})
    print(f"Retain Result: {result}\n")

    print("--- 2. Testing Hindsight Recall (Known Incident) ---")
    memories = await hindsight_client.recall("Auth service 500 error token failure")
    print(f"Recalled {len(memories)} memories:")
    for mem in memories:
        print(f"  - [{mem.get('memory_id')}] Score: {mem.get('score')}")
        print(f"    Content: {mem.get('content')}\n")

    print("--- 3. Testing Hindsight Recall (Novel Incident) ---")
    novel_memories = await hindsight_client.recall("Kafka cluster consumer offset drift")
    print(f"Recalled for Novel Incident: {len(novel_memories)} memories (Expected: 0)")

if __name__ == "__main__":
    asyncio.run(test_hindsight_flow())