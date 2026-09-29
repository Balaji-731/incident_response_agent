from typing import List, Dict, Any, Optional
from backend.hindsight.client import hindsight_client
from backend.models.response import HistoricalEvidence, MemoryMatch

class MemoryRecallClassifier:
    """Precision Memory Classifier using Service Correlation, Symptom Overlap, and Score Normalization."""
    
    @staticmethod
    async def get_historical_evidence(query: str, service: str = "", symptoms: Optional[List[str]] = None) -> HistoricalEvidence:
        raw_memories = await hindsight_client.recall(query, top_k=5)
        
        if not raw_memories:
            return HistoricalEvidence(status="none", matches=[])
        
        matches: List[MemoryMatch] = []
        highest_relevance_score = 0.0

        target_service = (service or "").lower().strip()
        target_symptoms = [s.lower().strip() for s in (symptoms or []) if s]

        for mem in raw_memories:
            raw_score = mem.get("score", 0.0)
            
            # Normalize vector score (cap max at 1.0 / 100%)
            norm_score = min(round(raw_score if raw_score <= 1.0 else (raw_score / 1.15), 2), 1.0)
            
            metadata = mem.get("metadata") or {}
            mem_service = str(metadata.get("service") or "").lower().strip()
            content = mem.get("content", "").lower()

            # Check service correlation and symptom overlap
            is_same_service = bool(target_service and mem_service and target_service == mem_service)
            
            has_symptom_overlap = False
            for s in target_symptoms:
                if s in content or (isinstance(metadata.get("symptoms"), list) and any(s in str(x).lower() for x in metadata.get("symptoms"))):
                    has_symptom_overlap = True
                    break

            # Precision Relevance Rules
            if is_same_service and norm_score >= 0.70:
                relevance = "strong"
                calc_score = norm_score
            elif (is_same_service or has_symptom_overlap) and norm_score >= 0.55:
                relevance = "related"
                calc_score = norm_score * 0.85  # Slight discount for cross-service or partial match
            elif norm_score >= 0.75 and has_symptom_overlap:
                relevance = "related"
                calc_score = norm_score * 0.75
            else:
                relevance = "weak"
                calc_score = norm_score * 0.35  # Discount non-matching domain/symptom noise

            if calc_score > highest_relevance_score and relevance in ["strong", "related"]:
                highest_relevance_score = calc_score

            # Parse failed attempts
            failed_attempts_raw = metadata.get("failed_attempts")
            failed_attempts: List[str] = []
            if isinstance(failed_attempts_raw, str) and failed_attempts_raw.strip():
                failed_attempts = [item.strip() for item in failed_attempts_raw.split(",") if item.strip()]
            elif isinstance(failed_attempts_raw, list):
                failed_attempts = [str(item) for item in failed_attempts_raw]

            matches.append(MemoryMatch(
                memory_id=mem.get("memory_id"),
                content=mem.get("content", ""),
                score=round(calc_score, 2),
                relevance=relevance,
                failed_attempts=failed_attempts,
                service=metadata.get("service"),
                root_cause=metadata.get("root_cause"),
                resolution=metadata.get("resolution")
            ))

        # Sort matches by calculated relevance score descending
        matches.sort(key=lambda m: m.score, reverse=True)

        status = "found" if highest_relevance_score >= 0.75 else ("related_only" if highest_relevance_score >= 0.50 else "none")
        return HistoricalEvidence(status=status, matches=matches)