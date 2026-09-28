from pydantic import BaseModel, Field
from typing import List, Optional

class ResolutionConfirm(BaseModel):
    confirmed_root_cause: str = Field(..., example="Excessive GPU batch size (64) exceeding VRAM limit")
    actual_resolution: str = Field(..., example="Reduced batch size from 64 to 16 in config")
    failed_attempts: List[str] = Field(default_factory=list, example=["Restarted inference pods"])
    engineer_notes: Optional[str] = Field(default=None, example="Rollback to batch size 16 restored P99 latency to 120ms")
    was_agent_helpful: bool = Field(default=True)

class ResolutionResponse(BaseModel):
    incident_id: str
    status: str = Field(default="resolved")
    retained_memory_id: Optional[str] = None
    message: str