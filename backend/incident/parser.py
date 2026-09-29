import re
from typing import Dict, Any, List

class LogParser:
    """Parses raw server logs and stack traces into structured incident fields."""
    
    @staticmethod
    def parse_raw_log(raw_text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
        
        extracted_logs: List[str] = []
        extracted_symptoms: List[str] = []
        detected_service = "unknown-service"
        detected_severity = "high"
        
        # 1. Identify primary exception / error line
        for line in lines:
            if any(k in line for k in ["Error", "Exception", "CRITICAL", "FATAL", "Timeout", "OOM", "500", "503"]):
                extracted_logs.append(line[:300]) # Cap long lines
                
                # Extract symptom keywords
                if "CUDA out of memory" in line or "OOM" in line:
                    extracted_symptoms.append("CUDA / VRAM Out of Memory")
                elif "Timeout" in line or "503" in line:
                    extracted_symptoms.append("Service Timeout / HTTP 503")
                elif "Connection pool" in line or "Redis" in line or "Hikari" in line:
                    extracted_symptoms.append("Connection Pool Exhaustion")
                elif "500" in line or "Internal Error" in line:
                    extracted_symptoms.append("Internal Server Error")
        
        # Fallback if no error keyword matched
        if not extracted_logs and lines:
            extracted_logs.append(lines[0][:300])
        if not extracted_symptoms:
            extracted_symptoms.append("Unclassified Operational Anomaly")

        # 2. Service detection heuristically from log text
        lower_text = raw_text.lower()
        if "recommendation" in lower_text or "inference" in lower_text or "cuda" in lower_text:
            detected_service = "recommendation-engine"
        elif "payment" in lower_text or "checkout" in lower_text or "stripe" in lower_text:
            detected_service = "payment-api"
        elif "auth" in lower_text or "token" in lower_text or "jwt" in lower_text or "redis" in lower_text:
            detected_service = "auth-service"
        elif "cart" in lower_text or "order" in lower_text:
            detected_service = "order-service"

        summary = extracted_symptoms[0] if extracted_symptoms else "Raw Log Intake Incident"
        if lines:
            summary = f"{summary}: {lines[0][:80]}"

        return {
            "service": detected_service,
            "severity": detected_severity,
            "summary": summary,
            "symptoms": list(set(extracted_symptoms)),
            "logs": extracted_logs[:5],  # Keep top 5 log traces
            "metrics": {"parsed_lines_count": len(lines)},
            "recent_changes": ["Pasted raw log trace"]
        }