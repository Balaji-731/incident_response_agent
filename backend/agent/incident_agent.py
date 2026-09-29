import os
import json
from groq import AsyncGroq
from dotenv import load_dotenv

from backend.models.incident import Incident
from backend.models.response import AgentAssessmentResponse, HistoricalEvidence, Hypothesis
from backend.incident.analyzer import IncidentAnalyzer
from backend.hindsight.recall import MemoryRecallClassifier
from backend.agent.prompts import INCIDENT_AGENT_SYSTEM_PROMPT, build_user_prompt

load_dotenv()

class IncidentAgent:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        # Clean prefix if user included "groq/"
        raw_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        self.model = raw_model.replace("groq/", "").strip()
        
        self.is_mock_llm = (
            not self.groq_api_key or 
            self.groq_api_key.startswith("your_") or 
            self.groq_api_key == "placeholder"
        )
        
        if not self.is_mock_llm:
            self.client = AsyncGroq(api_key=self.groq_api_key)

    async def analyze_incident(self, incident: Incident) -> AgentAssessmentResponse:
        # 1. Extract search query & current evidence
        query = IncidentAnalyzer.extract_search_query(incident)
        current_evidence = IncidentAnalyzer.extract_current_evidence(incident)

        # 2. Recall historical memory from Hindsight with precision domain & symptom matching
        historical_evidence = await MemoryRecallClassifier.get_historical_evidence(
            query, 
            service=incident.service, 
            symptoms=incident.symptoms
        )

        # 3. Handle LLM execution
        if self.is_mock_llm:
            return self._generate_fallback_assessment(incident, current_evidence, historical_evidence)

        user_prompt = build_user_prompt(
            incident.summary, 
            current_evidence, 
            historical_evidence.dict()
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INCIDENT_AGENT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw_json = json.loads(response.choices[0].message.content)
            
            # Enforce logical consistency between Hindsight status and LLM warnings
            raw_warnings = raw_json.get("warnings", [])
            final_warnings = []
            if historical_evidence.status == "none":
                no_mem_msg = "No relevant historical incident found; investigating from current evidence only."
                final_warnings.append(no_mem_msg)
            else:
                # Filter out contradictory "no memory found" warnings if historical evidence WAS found
                final_warnings = [
                    w for w in raw_warnings 
                    if "no relevant historical incident found" not in w.lower()
                ]
                # Inject warnings for past failed attempts if present
                for match in historical_evidence.matches:
                    if match.failed_attempts:
                        failed_msg = f"WARNING: Past experience indicates failed action: {', '.join(match.failed_attempts)}"
                        if failed_msg not in final_warnings:
                            final_warnings.append(failed_msg)

            return AgentAssessmentResponse(
                incident_id=incident.incident_id,
                severity=incident.severity,
                classification=raw_json.get("classification", f"{incident.service} / Infrastructure"),
                historical_evidence=historical_evidence,
                current_evidence=current_evidence,
                hypotheses=[Hypothesis(**h) for h in raw_json.get("hypotheses", [])],
                recommended_actions=raw_json.get("recommended_actions", []),
                relevant_runbooks=raw_json.get("relevant_runbooks", []),
                warnings=final_warnings
            )
        except Exception as err:
            print(f"[LLM Error] Fallback triggered: {err}")
            return self._generate_fallback_assessment(incident, current_evidence, historical_evidence)

    def _generate_fallback_assessment(
        self, 
        incident: Incident, 
        current_evidence: list, 
        historical_evidence: HistoricalEvidence
    ) -> AgentAssessmentResponse:
        """Deterministic rule-based assessment fallback for offline/testing mode."""
        warnings = []
        hypotheses = []
        recommended_actions = []

        if historical_evidence.status == "none" or not historical_evidence.matches:
            warnings.append("No relevant historical incident found; investigating from current evidence only.")
            hypotheses.append(Hypothesis(
                statement=f"Recent environment change or batch size increase may be contributing to {incident.summary}",
                evidence=current_evidence[:2],
                status="unconfirmed"
            ))
            recommended_actions = [
                "Inspect process memory and error stack trace",
                "Compare current parameters with previous working configuration",
                "Test reducing batch size or load in a safe environment",
                "Monitor error rate and resource usage after config adjustment"
            ]
        else:
            top_match = historical_evidence.matches[0]
            hypotheses.append(Hypothesis(
                statement=f"Incident matches historical memory [{top_match.memory_id}]. Root cause likely related to previous findings.",
                evidence=[f"Historical match ({top_match.score*100:.0f}% similarity): {top_match.content[:100]}..."],
                status="unconfirmed"
            ))
            
            # Check for failed attempts warning
            for match in historical_evidence.matches:
                if match.failed_attempts:
                    warnings.append(f"WARNING: Past experience indicates failed action: {', '.join(match.failed_attempts)}")

            recommended_actions = [
                "Verify if symptoms match historical resolution before attempting changes",
                "Execute confirmed resolution procedure from past incident",
                "Avoid actions identified as failed in historical memory"
            ]

        return AgentAssessmentResponse(
            incident_id=incident.incident_id,
            severity=incident.severity,
            classification=f"{incident.service} / Infrastructure",
            historical_evidence=historical_evidence,
            current_evidence=current_evidence,
            hypotheses=hypotheses,
            recommended_actions=recommended_actions,
            relevant_runbooks=[f"Runbook: Troubleshooting {incident.service}"],
            warnings=warnings
        )

incident_agent = IncidentAgent()