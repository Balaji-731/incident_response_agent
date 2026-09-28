import asyncio
import json
from backend.models.incident import Incident
from backend.models.feedback import ResolutionConfirm
from backend.agent.incident_agent import incident_agent
from backend.hindsight.memory_manager import memory_manager
from backend.api.incidents import incidents_db

async def run_learning_loop():
    print("==================================================")
    print("STEP 1: Ingesting & Analyzing Novel Incident INC-2001")
    print("==================================================")
    with open("data/incidents/INC-2001_cuda_oom.json", "r") as f:
        inc1_data = json.load(f)
    
    inc1 = Incident(**inc1_data)
    incidents_db[inc1.incident_id] = inc1
    
    assessment1 = await incident_agent.analyze_incident(inc1)
    print(f"INC-2001 Analysis -> Classification: {assessment1.classification}")
    print(f"Historical Evidence Status: {assessment1.historical_evidence.status}")
    print(f"Hypothesis: {assessment1.hypotheses[0].statement}\n")

    print("==================================================")
    print("STEP 2: Engineer Confirms Resolution & Retains in Hindsight")
    print("==================================================")
    resolution = ResolutionConfirm(
        confirmed_root_cause="Batch size increased to 64 exceeded GPU VRAM during concurrent inference",
        actual_resolution="Reduced batch size to 16 in recommendation-engine config",
        failed_attempts=["Restarted GPU inference pods"],
        was_agent_helpful=True
    )
    retain_res = await memory_manager.retain_confirmed_resolution(inc1, resolution)
    print(f"Experience Retained into Hindsight: {retain_res}\n")

    print("==================================================")
    print("STEP 3: Analyzing a NEW Similar Incident (INC-2002)")
    print("==================================================")
    inc2 = Incident(
        incident_id="INC-2002",
        timestamp="2026-09-29T01:00:00Z",
        service="recommendation-engine",
        summary="Recommendation engine timing out with high GPU allocation",
        symptoms=["CUDA memory allocation failure", "latency spike"],
        logs=["RuntimeError: CUDA out of memory on GPU 0"],
        metrics={"gpu_memory": "99%"},
        recent_changes=["Increased batch size"]
    )
    incidents_db[inc2.incident_id] = inc2

    assessment2 = await incident_agent.analyze_incident(inc2)
    print(f"INC-2002 Historical Evidence Status: {assessment2.historical_evidence.status}")
    print(f"Recalled Memory Matches: {len(assessment2.historical_evidence.matches)}")
    for match in assessment2.historical_evidence.matches:
        print(f"  - Score: {match.score*100:.1f}% | Content: {match.content}")
        
    print("\n[Warnings Detected]:", assessment2.warnings)
    print("[Agent Hypotheses]:")
    for h in assessment2.hypotheses:
        print(f"  - {h.statement}")

if __name__ == "__main__":
    asyncio.run(run_learning_loop())