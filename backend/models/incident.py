from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class IncidentCreate(BaseModel):
    service: str = Field(..., example="recommendation-engine")
    environment: str = Field(default="production", example="production")
    severity: str = Field(default="high", example="high")
    summary: str = Field(..., example="Inference requests timing out with OOM")
    symptoms: List[str] = Field(default_factory=list, example=["CUDA out of memory", "latency increased"])
    logs: List[str] = Field(default_factory=list, example=["RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB"])
    metrics: Dict[str, Any] = Field(default_factory=dict, example={"gpu_memory": "100%", "batch_size": 64})
    recent_changes: List[str] = Field(default_factory=list, example=["Batch size increased from 16 to 64 two hours ago"])

class Incident(IncidentCreate):
    incident_id: str
    timestamp: str
    status: str = Field(default="investigating", example="investigating")  # investigating, resolved, escalated
    root_cause: Optional[str] = None
    recommended_actions: List[str] = Field(default_factory=list)
    actual_resolution: Optional[str] = None
    outcome: Optional[str] = None  # resolved, unresolved