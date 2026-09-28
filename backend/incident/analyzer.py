from backend.models.incident import Incident

class IncidentAnalyzer:
    """Extracts features, error signatures, and constructs Hindsight recall queries."""
    
    @staticmethod
    def extract_search_query(incident: Incident) -> str:
        """
        Builds a high-precision query combining service, symptoms, and primary error log.
        """
        parts = [f"Service: {incident.service}"]
        if incident.symptoms:
            parts.append(f"Symptoms: {', '.join(incident.symptoms)}")
        if incident.summary:
            parts.append(f"Summary: {incident.summary}")
        if incident.logs:
            # First log entry often contains error trace
            parts.append(f"Error Log: {incident.logs[0]}")
            
        return " | ".join(parts)

    @staticmethod
    def extract_current_evidence(incident: Incident) -> list[str]:
        """Synthesizes structured current evidence from incident fields."""
        evidence = []
        if incident.summary:
            evidence.append(f"Summary: {incident.summary}")
        for symptom in incident.symptoms:
            evidence.append(f"Symptom: {symptom}")
        for log in incident.logs:
            evidence.append(f"Log: {log}")
        for change in incident.recent_changes:
            evidence.append(f"Recent Change: {change}")
        for k, v in incident.metrics.items():
            evidence.append(f"Metric - {k}: {v}")
        return evidence