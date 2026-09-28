from fastapi import APIRouter, HTTPException
from typing import List, Dict
import datetime
import uuid

from backend.models.incident import Incident, IncidentCreate
from backend.models.response import AgentAssessmentResponse
from backend.agent.incident_agent import incident_agent
from backend.models.feedback import ResolutionConfirm, ResolutionResponse
from backend.hindsight.memory_manager import memory_manager

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

# In-memory store for MVP lifecycle records
incidents_db: Dict[str, Incident] = {}

@router.post("", response_model=Incident)
def create_incident(payload: IncidentCreate):
    inc_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    incident = Incident(
        incident_id=inc_id,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        **payload.dict()
    )
    incidents_db[inc_id] = incident
    return incident

@router.get("", response_model=List[Incident])
def list_incidents():
    return list(incidents_db.values())

@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: str):
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incidents_db[incident_id]

@router.post("/{incident_id}/analyze", response_model=AgentAssessmentResponse)
async def analyze_incident_endpoint(incident_id: str):
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = incidents_db[incident_id]
    assessment = await incident_agent.analyze_incident(incident)
    
    # Store recommended actions back on the incident lifecycle model
    incident.recommended_actions = assessment.recommended_actions
    return assessment

@router.post("/{incident_id}/resolve", response_model=ResolutionResponse)
async def resolve_incident_endpoint(incident_id: str, payload: ResolutionConfirm):
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident = incidents_db[incident_id]
    
    # 1. Update incident state
    incident.status = "resolved"
    incident.root_cause = payload.confirmed_root_cause
    incident.actual_resolution = payload.actual_resolution
    incident.outcome = "resolved"
    # 2. Retain experience in Hindsight Cloud
    retain_result = await memory_manager.retain_confirmed_resolution(incident, payload)
    return ResolutionResponse(
        incident_id=incident_id,
        status="resolved",
        retained_memory_id=retain_result.get("id") or retain_result.get("memory_id"),
        message="Incident resolved and confirmed experience retained into Hindsight memory bank."
    )
