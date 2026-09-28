import asyncio
from backend.hindsight.client import hindsight_client

async def main():
    print(f"=== Inspecting Hindsight Memory Bank: '{hindsight_client.bank_id}' ===\n")
    
    # We query Hindsight across broad topics to fetch stored memories
    search_queries = ["incident", "error", "service", "resolution", "failed"]
    seen_ids = set()
    total_found = 0

    for query in search_queries:
        memories = await hindsight_client.recall(query, top_k=10)
        for mem in memories:
            mem_id = mem.get("memory_id")
            if mem_id and mem_id not in seen_ids:
                seen_ids.add(mem_id)
                total_found += 1
                print(f"[{total_found}] Memory ID: {mem_id}")
                print(f"    Relevance Score: {mem.get('score')}")
                print(f"    Content: {mem.get('content')}")
                print(f"    Metadata: {mem.get('metadata')}")
                print("-" * 60)

    if total_found == 0:
        print("No memories currently stored in this bank.")
    else:
        print(f"\nTotal unique memories retrieved: {total_found}")

if __name__ == "__main__":
    asyncio.run(main())