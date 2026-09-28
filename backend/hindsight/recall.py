from typing import List, Dict, Any
from backend.hindsight.client import hindsight_client
from backend.models.response import HistoricalEvidence, MemoryMatch

class MemoryRecallClassifier:
    """Classifies recalled memories into Strong, Related, Weak, or None, and extracts failed approaches."""
    
    @staticmethod
    async def get_historical_evidence(query: str) -> HistoricalEvidence:
        raw_memories = await hindsight_client.recall(query, top_k=5)
        
        if not raw_memories:
            return HistoricalEvidence(status="none", matches=[])
        
        matches: List[MemoryMatch] = []
        highest_score = 0.0

        for mem in raw_memories:
            score = mem.get("score", 0.0)
            if score > highest_score:
                highest_score = score
                
            # Classify relevance
            if score >= 0.85:
                relevance = "strong"
            elif score >= 0.65:
                relevance = "related"
            elif score >= 0.40:
                relevance = "weak"
            else:
                continue  # Ignore very low relevance noise

            content = mem.get("content", "")
            
            # Extract failed attempts safely from metadata string or list
            metadata = mem.get("metadata") or {}
            failed_attempts_raw = metadata.get("failed_attempts")
            failed_attempts: List[str] = []

            if isinstance(failed_attempts_raw, str) and failed_attempts_raw.strip():
                failed_attempts = [item.strip() for item in failed_attempts_raw.split(",") if item.strip()]
            elif isinstance(failed_attempts_raw, list):
                failed_attempts = [str(item) for item in failed_attempts_raw]

            # Text fallback parsing if metadata was empty
            if not failed_attempts and "FAILED" in content:
                for line in content.split("."):
                    if "failed" in line.lower() or "attempted" in line.lower():
                        failed_attempts.append(line.strip())

            matches.append(MemoryMatch(
                memory_id=mem.get("memory_id"),
                content=content,
                score=score,
                relevance=relevance,
                failed_attempts=failed_attempts
            ))

        status = "found" if highest_score >= 0.85 else ("related_only" if highest_score >= 0.65 else "none")
        return HistoricalEvidence(status=status, matches=matches)