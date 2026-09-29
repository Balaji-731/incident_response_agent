import json
from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from backend.database.db import Base

class IncidentRecord(Base):
    __tablename__ = "incidents"

    incident_id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")
    service = Column(String, index=True)
    environment = Column(String, default="production")
    severity = Column(String, default="high")
    summary = Column(Text)
    
    # Stored as JSON strings in SQLite
    symptoms_json = Column(Text, default="[]")
    logs_json = Column(Text, default="[]")
    metrics_json = Column(Text, default="{}")
    recent_changes_json = Column(Text, default="[]")
    
    status = Column(String, default="investigating")  # investigating, resolved, escalated
    root_cause = Column(Text, nullable=True)
    actual_resolution = Column(Text, nullable=True)
    outcome = Column(String, nullable=True)
    retained_memory_id = Column(String, nullable=True)

    def to_dict(self):
        return {
            "incident_id": self.incident_id,
            "timestamp": self.timestamp,
            "service": self.service,
            "environment": self.environment,
            "severity": self.severity,
            "summary": self.summary,
            "symptoms": json.loads(self.symptoms_json or "[]"),
            "logs": json.loads(self.logs_json or "[]"),
            "metrics": json.loads(self.metrics_json or "{}"),
            "recent_changes": json.loads(self.recent_changes_json or "[]"),
            "status": self.status,
            "root_cause": self.root_cause,
            "actual_resolution": self.actual_resolution,
            "outcome": self.outcome,
            "retained_memory_id": self.retained_memory_id
        }