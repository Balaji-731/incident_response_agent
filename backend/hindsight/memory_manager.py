from typing import Dict, Any
from backend.models.incident import Incident
from backend.models.feedback import ResolutionConfirm
from backend.hindsight.client import hindsight_client

class HindsightMemoryManager:
    """Formats and retains confirmed organizational experience into Hindsight memory."""
    
    @staticmethod
    async def retain_confirmed_resolution(incident: Incident, resolution: ResolutionConfirm) -> Dict[str, Any]:
        failed_str = f" Attempted fixes that FAILED: {', '.join(resolution.failed_attempts)}." if resolution.failed_attempts else ""
        
        # Formulate structured memory string
        memory_text = (
            f"Incident {incident.incident_id} ({incident.service}): {incident.summary}. "
            f"Symptoms: {', '.join(incident.symptoms)}.{failed_str} "
            f"Confirmed Root Cause: {resolution.confirmed_root_cause}. "
            f"Successful Resolution: {resolution.actual_resolution}."
        )

        # Hindsight Cloud metadata values MUST be strings
        metadata = {
            "incident_id": str(incident.incident_id),
            "service": str(incident.service),
            "environment": str(incident.environment),
            "severity": str(incident.severity),
            "root_cause": str(resolution.confirmed_root_cause),
            "resolution": str(resolution.actual_resolution),
            "failed_attempts": ", ".join(resolution.failed_attempts) if resolution.failed_attempts else ""
        }

        # Retain into Hindsight Cloud
        return await hindsight_client.retain(memory_text, metadata)

memory_manager = HindsightMemoryManager()