from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class MemoryMatch(BaseModel):
    memory_id: Optional[str] = None
    content: str
    score: float
    relevance: str = Field(..., example="strong")
    failed_attempts: List[str] = Field(default_factory=list)
    service: Optional[str] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None

class HistoricalEvidence(BaseModel):
    status: str = Field(..., example="found")
    matches: List[MemoryMatch] = Field(default_factory=list)

class Hypothesis(BaseModel):
    statement: str
    evidence: List[str]
    status: str = Field(default="unconfirmed", example="unconfirmed")

class AgentAssessmentResponse(BaseModel):
    incident_id: str
    severity: str
    classification: str
    historical_evidence: HistoricalEvidence
    current_evidence: List[str]
    hypotheses: List[Hypothesis]
    recommended_actions: List[str]
    relevant_runbooks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)