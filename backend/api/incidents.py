import json
import uuid
import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.models import IncidentRecord
from backend.models.incident import Incident, IncidentCreate
from backend.models.response import AgentAssessmentResponse
from backend.models.feedback import ResolutionConfirm, ResolutionResponse
from backend.incident.parser import LogParser
from backend.agent.incident_agent import incident_agent
from backend.hindsight.memory_manager import memory_manager

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

@router.post("/parse-log")
def parse_raw_log_endpoint(payload: dict):
    raw_text = payload.get("raw_log", "")
    if not raw_text:
        raise HTTPException(status_code=400, detail="raw_log field is required")
    parsed_data = LogParser.parse_raw_log(raw_text)
    return parsed_data

@router.post("", response_model=Incident)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    inc_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    
    db_rec = IncidentRecord(
        incident_id=inc_id,
        timestamp=timestamp,
        service=payload.service,
        environment=payload.environment,
        severity=payload.severity,
        summary=payload.summary,
        symptoms_json=json.dumps(payload.symptoms),
        logs_json=json.dumps(payload.logs),
        metrics_json=json.dumps(payload.metrics),
        recent_changes_json=json.dumps(payload.recent_changes),
        status="investigating"
    )
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec.to_dict()

@router.get("", response_model=List[Incident])
def list_incidents(db: Session = Depends(get_db)):
    records = db.query(IncidentRecord).order_by(IncidentRecord.timestamp.desc()).all()
    return [r.to_dict() for r in records]

@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    rec = db.query(IncidentRecord).filter(IncidentRecord.incident_id == incident_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Incident not found")
    return rec.to_dict()

@router.post("/{incident_id}/analyze", response_model=AgentAssessmentResponse)
async def analyze_incident_endpoint(incident_id: str, db: Session = Depends(get_db)):
    rec = db.query(IncidentRecord).filter(IncidentRecord.incident_id == incident_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident = Incident(**rec.to_dict())
    assessment = await incident_agent.analyze_incident(incident)
    return assessment

@router.post("/{incident_id}/resolve", response_model=ResolutionResponse)
async def resolve_incident_endpoint(incident_id: str, payload: ResolutionConfirm, db: Session = Depends(get_db)):
    rec = db.query(IncidentRecord).filter(IncidentRecord.incident_id == incident_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = Incident(**rec.to_dict())
    
    # Retain experience in Hindsight Cloud
    retain_result = await memory_manager.retain_confirmed_resolution(incident, payload)
    retained_id = retain_result.get("id") or retain_result.get("memory_id")

    # Update SQLite record
    rec.status = "resolved"
    rec.root_cause = payload.confirmed_root_cause
    rec.actual_resolution = payload.actual_resolution
    rec.outcome = "resolved"
    rec.retained_memory_id = retained_id
    db.commit()

    return ResolutionResponse(
        incident_id=incident_id,
        status="resolved",
        retained_memory_id=retained_id,
        message="Incident resolved and confirmed experience persisted in database & retained into Hindsight Cloud."
    )

@router.delete("/reset")
async def reset_all_data(db: Session = Depends(get_db)):
    """
    Clears all incident records from SQLite database and resets the Hindsight Cloud memory bank.
    """
    # 1. Clear SQLite Database
    db.query(IncidentRecord).delete()
    db.commit()

    # 2. Clear Hindsight Cloud Memory Bank
    import os
    import httpx
    api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
    bank_id = os.getenv("HINDSIGHT_BANK_ID", "incident-response-bank").strip()
    api_url = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io").rstrip('/')
    
    hindsight_msg = "Mock Reset"
    if api_key and not api_key.startswith("your_"):
        url = f"{api_url}/v1/default/banks/{bank_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.delete(url, headers=headers)
                hindsight_msg = f"Bank reset status: {res.status_code}"
        except Exception as e:
            hindsight_msg = f"Bank reset error: {str(e)}"

    return {
        "status": "success",
        "message": f"SQLite database and Hindsight memory bank cleared. {hindsight_msg}"
    }