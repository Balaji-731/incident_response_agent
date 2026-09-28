import asyncio
import json
from backend.models.incident import Incident
from backend.agent.incident_agent import incident_agent

async def main():
    # Load synthetic novel incident INC-2001
    with open("data/incidents/INC-2001_cuda_oom.json", "r") as f:
        data = json.load(f)
    
    incident = Incident(**data)
    print(f"--- Analyzing Incident {incident.incident_id} ({incident.service}) ---")
    
    assessment = await incident_agent.analyze_incident(incident)
    
    print(f"\n[Classification]: {assessment.classification}")
    print(f"[Historical Evidence Status]: {assessment.historical_evidence.status}")
    print(f"[Warnings]: {assessment.warnings}")
    print(f"[Hypotheses]:")
    for h in assessment.hypotheses:
        print(f"  - {h.statement} (Status: {h.status})")
    print(f"[Recommended Actions]:")
    for action in assessment.recommended_actions:
        print(f"  - {action}")

if __name__ == "__main__":
    asyncio.run(main())